from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from compiler.build_requirements_model import (
    build_requirements_model,
    default_requirements_schema_path,
    validate_requirements_model,
)
from intake.workspace_manifest import refresh_workspace_manifest
from compiler.compile_graphs import compile_all_graphs, summarize_graph_bundle
from model_utils import load_yaml, write_yaml
from reports.generate_handoff_matrix import generate_handoff_matrix
from reports.generate_network_volume_summary import generate_network_volume_summary
from validators.validate_annex_activation import validate_annex_activation
from validators.validate_connectivity import validate_connectivity
from validators.validate_cross_graph import validate_cross_graph
from validators.validate_power_ports import validate_power_ports
from validators.validate_resilience import validate_resilience
from validators.validate_role_assignments import validate_role_assignments
from validators.validate_segmentation import validate_segmentation
from validators.validate_semantic_consistency import validate_semantic_consistency
from validators.validate_stage_confidence import (
    count_tbd_fields,
    derive_confidence_level,
    summarize_assumptions,
    validate_stage_confidence,
)
from validators.validate_time import validate_time


def run_validators(
    requirements: dict[str, Any],
    graph_summary: dict[str, Any],
    bundle: Any,
    assumptions: list[dict[str, str | Any]],
    role_assignments: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    issues.extend(validate_stage_confidence(requirements, assumptions))
    issues.extend(validate_semantic_consistency(requirements, assumptions))
    issues.extend(validate_connectivity(bundle.physical, requirements))
    issues.extend(validate_segmentation(bundle.logical, requirements))
    issues.extend(validate_resilience(bundle.physical, bundle.failure_domain, requirements))
    issues.extend(validate_power_ports(requirements, bundle.physical))
    issues.extend(validate_time(requirements, bundle.physical))
    issues.extend(validate_annex_activation(requirements))
    issues.extend(validate_cross_graph(bundle.logical, bundle.service, bundle.interface, requirements))
    issues.extend(validate_role_assignments(role_assignments))

    if graph_summary["service"]["nodes"] == 0:
        issues.append(
            {
                "validator": "service_graph",
                "severity": "warning",
                "message": "No required services were compiled into the service graph.",
            }
        )
    return issues


def summarize_validation(issues: list[dict[str, Any]]) -> dict[str, Any]:
    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    return {
        "status": "failed" if error_count else "ok",
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }


def default_output_dir(questionnaire_path: Path) -> Path:
    return questionnaire_path.parent / "reports"


def _manifest_path(path: Path, base_dir: Path | None = None) -> str:
    """Prefer a stable relative path for manifest artifacts when possible."""
    resolved_path = path.resolve()
    resolved_base = (base_dir or Path.cwd()).resolve()
    try:
        return str(resolved_path.relative_to(resolved_base))
    except ValueError:
        return str(resolved_path)


def resolve_role_assignments(
    questionnaire_path: Path,
    role_assignments_path: Path | None = None,
) -> dict[str, Any] | None:
    if role_assignments_path:
        return load_yaml(role_assignments_path)

    auto_path = questionnaire_path.parent / "role_assignments.yaml"
    if auto_path.exists():
        return load_yaml(auto_path)
    return None


def _resolve_manifest_date_used(
    questionnaire_path: Path,
    questionnaire: dict[str, Any],
) -> str:
    intake_status_path = questionnaire_path.parent / "reports" / "intake_status.yaml"
    candidate_values: list[Any] = []
    if intake_status_path.exists():
        intake_status = load_yaml(intake_status_path) or {}
        candidate_values.append(intake_status.get("compiled_at"))

    metadata = questionnaire.get("metadata", {}) if isinstance(questionnaire, dict) else {}
    candidate_values.extend(
        [
            metadata.get("compiled_at"),
            metadata.get("compiled_on"),
        ]
    )

    for candidate in candidate_values:
        if candidate in {None, ""}:
            continue
        date_used = str(candidate)
        try:
            date.fromisoformat(date_used)
        except ValueError as exc:
            raise ValueError(
                f"Pipeline manifest date_used must be an ISO date, got {date_used!r}."
            ) from exc
        return date_used

    raise ValueError(
        "Pipeline manifest date_used requires reports/intake_status.yaml compiled_at "
        "or questionnaire metadata compiled_at/compiled_on."
    )


def execute_pipeline(
    questionnaire_path: Path,
    schema: Path | None = None,
    output_dir: Path | None = None,
    role_assignments_path: Path | None = None,
    *,
    write_outputs: bool = True,
) -> dict[str, Any]:
    schema_path = schema or default_requirements_schema_path()

    questionnaire = load_yaml(questionnaire_path)
    requirements, assumptions = build_requirements_model(questionnaire)
    validate_requirements_model(requirements, schema=load_yaml(schema_path))

    role_assignments = resolve_role_assignments(
        questionnaire_path,
        role_assignments_path=role_assignments_path,
    )

    bundle = compile_all_graphs(requirements)
    graph_summary = summarize_graph_bundle(bundle)
    issues = run_validators(
        requirements,
        graph_summary,
        bundle,
        assumptions,
        role_assignments=role_assignments,
    )
    validation_summary = summarize_validation(issues)
    tbd_fields = count_tbd_fields(requirements)
    assumption_summary = summarize_assumptions(assumptions)
    validation_summary["confidence_level"] = derive_confidence_level(requirements)
    validation_summary["tbd_count"] = len(tbd_fields)
    validation_summary["assumed_count"] = assumption_summary["total"]
    validation_summary["archetype_default_count"] = assumption_summary["archetype_default_count"]
    validation_summary["inference_count"] = assumption_summary["inference_count"]
    if tbd_fields:
        validation_summary["tbd_fields"] = tbd_fields
    if assumptions:
        validation_summary["assumed_fields"] = [
            {k: v for k, v in a.items() if k != "section"} for a in assumptions
        ]

    resolved_output_dir = output_dir or default_output_dir(questionnaire_path)
    if write_outputs:
        manifest_date_used = _resolve_manifest_date_used(questionnaire_path, questionnaire)
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

        compiled_output = dict(requirements)
        if assumptions:
            compiled_output["_assumptions"] = assumptions
        write_yaml(resolved_output_dir / "requirements.compiled.yaml", compiled_output)
        write_yaml(resolved_output_dir / "graphs.summary.yaml", graph_summary)
        write_yaml(resolved_output_dir / "validation.summary.yaml", validation_summary)
        write_yaml(
            resolved_output_dir / "pipeline.manifest.yaml",
            {
                "questionnaire": _manifest_path(questionnaire_path),
                "schema": _manifest_path(schema_path),
                "questionnaire_version": requirements.get("metadata", {}).get("questionnaire_version"),
                "resolved_archetype": requirements.get("metadata", {}).get("resolved_archetype"),
                "outputs": {
                    "requirements": "requirements.compiled.yaml",
                    "graph_summary": "graphs.summary.yaml",
                    "validation_summary": "validation.summary.yaml",
                    "network_volume_summary": "network_volume_summary.md",
                    "handoff_matrix": "handoff_matrix.md",
                },
                "status": validation_summary["status"],
            },
        )
        (resolved_output_dir / "network_volume_summary.md").write_text(
            generate_network_volume_summary(requirements), encoding="utf-8"
        )
        (resolved_output_dir / "handoff_matrix.md").write_text(
            generate_handoff_matrix(requirements), encoding="utf-8"
        )

        refresh_workspace_manifest(
            questionnaire_path.parent,
            object_id=requirements.get("metadata", {}).get("object_id") or questionnaire_path.parent.name,
            date_used=manifest_date_used,
            artifacts=[
                {
                    "producer": "pipeline",
                    "artifact_type": "requirements_compiled",
                    "format": "yaml",
                    "path": resolved_output_dir / "requirements.compiled.yaml",
                },
                {
                    "producer": "pipeline",
                    "artifact_type": "graphs_summary",
                    "format": "yaml",
                    "path": resolved_output_dir / "graphs.summary.yaml",
                },
                {
                    "producer": "pipeline",
                    "artifact_type": "validation_summary",
                    "format": "yaml",
                    "path": resolved_output_dir / "validation.summary.yaml",
                },
                {
                    "producer": "pipeline",
                    "artifact_type": "pipeline_manifest",
                    "format": "yaml",
                    "path": resolved_output_dir / "pipeline.manifest.yaml",
                },
                {
                    "producer": "pipeline",
                    "artifact_type": "network_volume_summary",
                    "format": "markdown",
                    "path": resolved_output_dir / "network_volume_summary.md",
                },
                {
                    "producer": "pipeline",
                    "artifact_type": "handoff_matrix",
                    "format": "markdown",
                    "path": resolved_output_dir / "handoff_matrix.md",
                },
            ],
        )

    return {
        "questionnaire_path": questionnaire_path,
        "schema_path": schema_path,
        "output_dir": resolved_output_dir,
        "requirements": requirements,
        "assumptions": assumptions,
        "graph_summary": graph_summary,
        "issues": issues,
        "validation": validation_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run questionnaire -> requirements -> graphs -> validators -> reports"
    )
    parser.add_argument("questionnaire", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=default_requirements_schema_path(),
        help="Path to requirements schema used for validation.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Directory for generated pipeline outputs. Defaults to questionnaire's reports directory.",
    )
    parser.add_argument(
        "--role-assignments",
        type=Path,
        help="Path to role_assignments.yaml for role conflict validation.",
    )
    args = parser.parse_args()

    result = execute_pipeline(
        args.questionnaire,
        schema=args.schema,
        output_dir=args.output_dir,
        role_assignments_path=args.role_assignments,
    )
    validation_summary = result["validation"]
    output_dir = result["output_dir"]
    requirements = result["requirements"]
    assumptions = result["assumptions"]

    print(
        yaml.safe_dump(
            {
                "status": validation_summary["status"],
                "output_dir": str(output_dir),
                "resolved_archetype": requirements.get("metadata", {}).get("resolved_archetype"),
                "error_count": validation_summary["error_count"],
                "warning_count": validation_summary["warning_count"],
                "assumed_count": len(assumptions),
                "archetype_default_count": validation_summary.get("archetype_default_count", 0),
                "inference_count": validation_summary.get("inference_count", 0),
            },
            sort_keys=False,
            allow_unicode=True,
        )
    )

    if validation_summary["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
