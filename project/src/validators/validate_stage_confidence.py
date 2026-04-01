from __future__ import annotations

from typing import Any

from model_utils import is_tbd


CONFIDENCE_MAP: dict[str, dict[str, str]] = {
    "concept": {
        "assumption_heavy": "indicative",
        "mixed": "indicative",
        "mostly_confirmed": "provisional",
        "field_verified": "provisional",
    },
    "basic_design": {
        "assumption_heavy": "indicative",
        "mixed": "provisional",
        "mostly_confirmed": "provisional",
        "field_verified": "binding",
    },
    "detailed_design": {
        "assumption_heavy": "indicative",
        "mixed": "provisional",
        "mostly_confirmed": "binding",
        "field_verified": "binding",
    },
    "build_commission": {
        "assumption_heavy": "indicative",
        "mixed": "provisional",
        "mostly_confirmed": "binding",
        "field_verified": "binding",
    },
}

HIGH_ASSUMPTION_THRESHOLD = 5
HIGH_TBD_THRESHOLD = 3


def derive_confidence_level(requirements: dict[str, Any]) -> str:
    stage = requirements.get("metadata", {}).get("project_stage", "concept")
    maturity = requirements.get("governance", {}).get("evidence_maturity_class", "assumption_heavy")
    return CONFIDENCE_MAP.get(stage, {}).get(maturity, "indicative")


def count_tbd_fields(requirements: dict[str, Any]) -> list[str]:
    tbd_fields: list[str] = []
    for section_name, section in requirements.items():
        if section_name.startswith("_") or not isinstance(section, dict):
            continue
        for field_id, value in section.items():
            if is_tbd(value):
                tbd_fields.append(field_id)
    return tbd_fields


def validate_stage_confidence(
    requirements: dict[str, Any],
    assumptions: list[dict[str, str | Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    stage = requirements.get("metadata", {}).get("project_stage", "concept")
    maturity = requirements.get("governance", {}).get("evidence_maturity_class", "assumption_heavy")
    assumed_count = len(assumptions)
    confidence = derive_confidence_level(requirements)
    tbd_fields = count_tbd_fields(requirements)
    tbd_count = len(tbd_fields)

    if stage in {"detailed_design", "build_commission"} and maturity == "assumption_heavy":
        issues.append({
            "validator": "stage_confidence",
            "severity": "error",
            "message": (
                f"Stage '{stage}' with evidence_maturity_class='assumption_heavy' "
                f"is not acceptable — design decisions cannot rely on unverified assumptions."
            ),
        })

    if stage == "concept" and maturity in {"assumption_heavy", "mixed"}:
        issues.append({
            "validator": "stage_confidence",
            "severity": "warning",
            "message": (
                f"Concept stage with evidence_maturity_class='{maturity}' — "
                f"validation results are indicative, not binding (confidence_level={confidence})."
            ),
        })

    if tbd_count > 0 and stage in {"detailed_design", "build_commission"}:
        issues.append({
            "validator": "stage_confidence",
            "severity": "error",
            "message": (
                f"{tbd_count} fields are still 'tbd' at stage '{stage}': "
                f"{', '.join(tbd_fields)}. All fields must be resolved before this stage."
            ),
        })

    if tbd_count > HIGH_TBD_THRESHOLD:
        issues.append({
            "validator": "stage_confidence",
            "severity": "warning",
            "message": (
                f"{tbd_count} fields remain 'tbd': {', '.join(tbd_fields)}. "
                f"Validators cannot fully evaluate design with unresolved inputs."
            ),
        })

    if assumed_count > HIGH_ASSUMPTION_THRESHOLD:
        issues.append({
            "validator": "stage_confidence",
            "severity": "warning",
            "message": (
                f"{assumed_count} fields were filled from archetype defaults, not from questionnaire answers. "
                f"Validation is operating on assumptions, not on confirmed data."
            ),
        })

    if assumed_count > 0 and stage in {"detailed_design", "build_commission"}:
        issues.append({
            "validator": "stage_confidence",
            "severity": "error",
            "message": (
                f"{assumed_count} assumed fields remain at stage '{stage}'. "
                f"All fields must be explicitly answered before this stage."
            ),
        })

    return issues
