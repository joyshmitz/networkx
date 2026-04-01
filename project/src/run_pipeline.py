from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from compiler.build_requirements_model import (
    build_requirements_model,
    default_requirements_schema_path,
    validate_requirements_model,
)
from compiler.compile_graphs import compile_all_graphs, summarize_graph_bundle
from model_utils import load_yaml, write_yaml
from reports.generate_handoff_matrix import generate_handoff_matrix
from reports.generate_network_volume_summary import generate_network_volume_summary
from validators.validate_connectivity import validate_connectivity
from validators.validate_power_ports import validate_power_ports
from validators.validate_resilience import validate_resilience
from validators.validate_segmentation import validate_segmentation
from validators.validate_stage_confidence import count_tbd_fields, derive_confidence_level, validate_stage_confidence
from validators.validate_time import validate_time


def run_validators(
    requirements: dict[str, Any],
    graph_summary: dict[str, Any],
    bundle: Any,
    assumptions: list[dict[str, str | Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    issues.extend(validate_stage_confidence(requirements, assumptions))
    issues.extend(validate_connectivity(bundle.physical, requirements))
    issues.extend(validate_segmentation(bundle.logical, requirements))
    issues.extend(validate_resilience(bundle.physical, bundle.failure_domain, requirements))
    issues.extend(validate_power_ports(requirements, bundle.physical))
    issues.extend(validate_time(requirements, bundle.physical))

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
    args = parser.parse_args()

    questionnaire = load_yaml(args.questionnaire)
    requirements, assumptions = build_requirements_model(questionnaire)
    validate_requirements_model(requirements, schema=load_yaml(args.schema))

    bundle = compile_all_graphs(requirements)
    graph_summary = summarize_graph_bundle(bundle)
    issues = run_validators(requirements, graph_summary, bundle, assumptions)
    validation_summary = summarize_validation(issues)
    tbd_fields = count_tbd_fields(requirements)
    validation_summary["confidence_level"] = derive_confidence_level(requirements)
    validation_summary["tbd_count"] = len(tbd_fields)
    validation_summary["assumed_count"] = len(assumptions)
    if tbd_fields:
        validation_summary["tbd_fields"] = tbd_fields
    if assumptions:
        validation_summary["assumed_fields"] = [
            {k: v for k, v in a.items() if k != "section"} for a in assumptions
        ]

    output_dir = args.output_dir or default_output_dir(args.questionnaire)
    output_dir.mkdir(parents=True, exist_ok=True)

    compiled_output = dict(requirements)
    if assumptions:
        compiled_output["_assumptions"] = assumptions
    write_yaml(output_dir / "requirements.compiled.yaml", compiled_output)
    write_yaml(output_dir / "graphs.summary.yaml", graph_summary)
    write_yaml(output_dir / "validation.summary.yaml", validation_summary)
    write_yaml(
        output_dir / "pipeline.manifest.yaml",
        {
            "questionnaire": str(args.questionnaire),
            "schema": str(args.schema),
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
    (output_dir / "network_volume_summary.md").write_text(
        generate_network_volume_summary(requirements), encoding="utf-8"
    )
    (output_dir / "handoff_matrix.md").write_text(
        generate_handoff_matrix(requirements), encoding="utf-8"
    )

    print(
        yaml.safe_dump(
            {
                "status": validation_summary["status"],
                "output_dir": str(output_dir),
                "resolved_archetype": requirements.get("metadata", {}).get("resolved_archetype"),
                "error_count": validation_summary["error_count"],
                "warning_count": validation_summary["warning_count"],
                "assumed_count": len(assumptions),
            },
            sort_keys=False,
            allow_unicode=True,
        )
    )

    if validation_summary["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
