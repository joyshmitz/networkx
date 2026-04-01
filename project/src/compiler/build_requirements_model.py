from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from model_utils import load_yaml, merge_missing_values_tracked, resolve_project_root


class SchemaValidationError(ValueError):
    """Raised when the compiled requirements model does not satisfy the schema."""


def default_requirements_schema_path() -> Path:
    return resolve_project_root() / "specs" / "requirements" / "object_requirements_v2.schema.yaml"


def default_archetypes_path() -> Path:
    return resolve_project_root() / "specs" / "archetypes" / "station_archetypes.yaml"


EXPECTED_V2_SECTIONS = (
    "metadata",
    "object_profile",
    "critical_services",
    "external_transport",
    "security_access",
    "time_sync",
    "power_environment",
    "resilience",
    "operations",
    "acceptance_criteria",
    "governance",
    "known_unknowns",
)


def detect_questionnaire_version(questionnaire: dict[str, Any]) -> str:
    if "functional_scope" in questionnaire:
        return "v1"
    if "object_profile" in questionnaire and "governance" in questionnaire:
        return "v2"
    raise ValueError("Unknown questionnaire structure. Cannot determine questionnaire version.")


def load_archetypes(path: Path | None = None) -> dict[str, dict[str, Any]]:
    payload = load_yaml(path or default_archetypes_path())
    return {item["archetype_id"]: item for item in payload.get("archetypes", [])}


def _section(questionnaire: dict[str, Any], name: str) -> dict[str, Any]:
    val = questionnaire.get(name)
    return val if isinstance(val, dict) else {}


def resolve_archetype_id(questionnaire: dict[str, Any]) -> str:
    services = _section(questionnaire, "critical_services")
    power_environment = _section(questionnaire, "power_environment")
    metadata = _section(questionnaire, "metadata")
    resilience = _section(questionnaire, "resilience")

    if services.get("iiot_required") == "yes":
        return "mixed_iiot_site"
    if services.get("video_required") == "yes" or power_environment.get("poe_budget_class") in {
        "medium",
        "heavy",
    }:
        return "video_heavy_site"
    if metadata.get("criticality_class") in {"high", "mission_critical"} or resilience.get(
        "redundancy_target"
    ) in {"n_plus_1", "no_spof"}:
        return "resilient_telemetry_site"
    return "small_remote_site"


def apply_archetype_defaults(
    questionnaire: dict[str, Any], archetype: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, str | Any]]]:
    defaults = archetype.get("defaults", {})
    archetype_id = archetype.get("archetype_id", "unknown")
    normalized: dict[str, dict[str, Any]] = {}
    all_assumptions: list[dict[str, str | Any]] = []

    for section_name in EXPECTED_V2_SECTIONS:
        section = questionnaire.get(section_name)
        if section is None:
            section = {}
        if not isinstance(section, dict):
            raise ValueError(
                f"Questionnaire section '{section_name}' must be a mapping, "
                f"got {type(section).__name__}: {section!r}"
            )
        normalized[section_name] = dict(section)

    section_to_fields = {
        "object_profile": ["staffing_model", "growth_horizon_months"],
        "critical_services": [
            "telemetry_required",
            "control_required",
            "video_required",
            "iiot_required",
            "local_archiving_required",
        ],
        "external_transport": [
            "wan_required",
            "carrier_diversity_target",
            "transport_separation_policy",
        ],
        "security_access": [
            "security_zone_model",
            "remote_access_profile",
            "contractor_access_policy",
            "audit_logging_required",
            "oob_required",
        ],
        "time_sync": ["timing_required", "sync_protocol", "timing_accuracy_class"],
        "power_environment": [
            "power_source_model",
            "cabinet_constraint_class",
            "environmental_constraint_class",
            "poe_required",
            "poe_budget_class",
        ],
        "resilience": [
            "redundancy_target",
            "degraded_mode_profile",
            "mttr_target_class",
            "common_cause_separation_required",
        ],
        "operations": [
            "support_model",
            "maintenance_window_model",
            "operations_handoff_required",
            "asbuilt_package_required",
        ],
        "acceptance_criteria": [
            "fat_required",
            "sat_required",
            "acceptance_evidence_class",
        ],
        "governance": ["evidence_maturity_class", "waiver_policy_class"],
    }

    for section_name, fields in section_to_fields.items():
        defaults_for_section = {field_id: defaults[field_id] for field_id in fields if field_id in defaults}
        normalized[section_name], assumed = merge_missing_values_tracked(
            normalized[section_name], defaults_for_section, section_name, archetype_id,
        )
        all_assumptions.extend(assumed)

    return normalized, all_assumptions


def normalize_boolish_enums(requirements: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    boolish_fields = {
        "telemetry_required",
        "control_required",
        "video_required",
        "iiot_required",
        "local_archiving_required",
        "wan_required",
        "audit_logging_required",
        "oob_required",
        "timing_required",
        "poe_required",
        "common_cause_separation_required",
        "operations_handoff_required",
        "asbuilt_package_required",
        "fat_required",
        "sat_required",
    }

    normalized: dict[str, dict[str, Any]] = {}
    for section_name, section in requirements.items():
        normalized_section = dict(section)
        for field_id, value in normalized_section.items():
            if field_id in boolish_fields and isinstance(value, bool):
                normalized_section[field_id] = "yes" if value else "no"
        normalized[section_name] = normalized_section
    return normalized


def build_requirements_model(
    questionnaire: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, str | Any]]]:
    """Compile questionnaire v2 into a normalized requirements model.

    Returns (requirements, assumptions) where assumptions is a list of fields
    that were filled from archetype defaults instead of questionnaire answers.
    """
    version = detect_questionnaire_version(questionnaire)
    if version == "v1":
        raise ValueError(
            "Questionnaire v1 is deprecated. Migrate to core_questionnaire_v2.yaml before running the pipeline."
        )

    archetypes = load_archetypes()
    resolved_archetype = resolve_archetype_id(questionnaire)
    archetype = archetypes[resolved_archetype]
    normalized, assumptions = apply_archetype_defaults(questionnaire, archetype)
    normalized = normalize_boolish_enums(normalized)

    metadata = dict(normalized["metadata"])
    metadata["questionnaire_version"] = str(questionnaire.get("version", "0.2.0"))
    metadata["resolved_archetype"] = resolved_archetype
    normalized["metadata"] = metadata

    requirements = {section_name: normalized.get(section_name, {}) for section_name in EXPECTED_V2_SECTIONS}
    return requirements, assumptions


def validate_requirements_model(
    requirements: dict[str, Any], schema: dict[str, Any] | None = None
) -> None:
    if schema is None:
        schema = load_yaml(default_requirements_schema_path())

    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(requirements), key=lambda err: list(err.absolute_path))
    if not errors:
        return

    lines = ["Requirements model failed schema validation:"]
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        lines.append(f"- {location}: {error.message}")
    raise SchemaValidationError("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build normalized requirements model")
    parser.add_argument("questionnaire", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=default_requirements_schema_path(),
        help="Path to requirements schema used for validating compiled output.",
    )
    args = parser.parse_args()

    questionnaire = load_yaml(args.questionnaire)
    requirements, assumptions = build_requirements_model(questionnaire)
    validate_requirements_model(requirements, schema=load_yaml(args.schema))
    from yaml import safe_dump

    output = dict(requirements)
    if assumptions:
        output["_assumptions"] = assumptions
    rendered = safe_dump(output, sort_keys=False, allow_unicode=True)

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
