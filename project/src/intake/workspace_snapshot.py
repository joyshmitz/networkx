from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from intake.compile_intake import _count_statuses, compile_intake
from model_utils import load_yaml, resolve_project_root
from run_pipeline import execute_pipeline
from validators.validate_role_assignments import build_person_to_roles, build_role_to_persons

SNAPSHOT_SCHEMA_VERSION = "0.1.0"
UNRESOLVED_STATUSES = {"tbd", "unanswered", "not_applicable"}


def load_field_metadata(
    project_root: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    fields_data = load_yaml(
        project_root / "specs" / "dictionary" / "questionnaire_v2_fields.yaml"
    )
    core_data = load_yaml(
        project_root / "specs" / "questionnaire" / "core_questionnaire_v2.yaml"
    )

    field_index = {field["field_id"]: field for field in fields_data["fields"]}
    field_to_section: dict[str, str] = {}
    for section in core_data["sections"]:
        for field_id in section.get("fields", []):
            field_to_section[field_id] = section["id"]

    return field_index, field_to_section


def load_role_resolution(workspace_path: Path) -> dict[str, Any]:
    role_assignments = load_yaml(workspace_path / "role_assignments.yaml")
    assignments = role_assignments.get("assignments", [])
    person_to_roles = build_person_to_roles(assignments)
    role_to_persons = build_role_to_persons(person_to_roles)

    return {
        "assignments": assignments,
        "person_to_roles": {
            person_id: sorted(roles)
            for person_id, roles in sorted(person_to_roles.items())
        },
        "role_to_persons": {
            role: sorted(persons)
            for role, persons in sorted(role_to_persons.items())
        },
    }


def collect_unresolved_fields(
    all_fields: dict[str, dict[str, Any]],
    field_index: dict[str, dict[str, Any]],
    field_to_section: dict[str, str],
    role_to_persons: dict[str, list[str]],
) -> list[dict[str, Any]]:
    unresolved: list[dict[str, Any]] = []
    for field_id, entry in all_fields.items():
        status = entry["status"]
        if status not in UNRESOLVED_STATUSES:
            continue

        field_def = field_index.get(field_id, {})
        owner_role = field_def.get("owner_role")
        reviewer_roles = list(field_def.get("reviewer_roles", []))
        reviewer_persons: set[str] = set()
        for reviewer_role in reviewer_roles:
            reviewer_persons.update(role_to_persons.get(reviewer_role, []))

        unresolved.append(
            {
                "field_id": field_id,
                "section": field_to_section.get(field_id, ""),
                "strictness": field_def.get("strictness"),
                "status": status,
                "owner_role": owner_role,
                "reviewer_roles": reviewer_roles,
                "owner_persons": list(role_to_persons.get(owner_role, [])) if owner_role else [],
                "reviewer_persons": sorted(reviewer_persons),
                "person_id": entry.get("person_id"),
            }
        )

    return sorted(unresolved, key=lambda item: (item["section"], item["field_id"]))


def pipeline_error_records(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "validator": issue["validator"],
            "severity": issue["severity"],
            "message": issue["message"],
        }
        for issue in issues
        if issue["severity"] == "error"
    ]


def build_blockers(
    pipeline_errors: list[dict[str, Any]],
    unresolved_s4_fields: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for issue in pipeline_errors:
        blockers.append(
            {
                "kind": "pipeline_error",
                "validator": issue["validator"],
                "message": issue["message"],
            }
        )
    for field in unresolved_s4_fields:
        blockers.append(
            {
                "kind": "unresolved_s4",
                "field_id": field["field_id"],
                "section": field["section"],
                "status": field["status"],
            }
        )
    return blockers


def build_workspace_snapshot(
    workspace_path: Path,
    *,
    project_root: Path | None = None,
    snapshot_on: date | None = None,
) -> dict[str, Any]:
    resolved_workspace = workspace_path.resolve()
    if not resolved_workspace.exists():
        raise FileNotFoundError(f"Workspace not found: {resolved_workspace}")
    if not resolved_workspace.is_dir():
        raise NotADirectoryError(
            f"Snapshot expects a workspace directory, got: {resolved_workspace}"
        )

    project_root = project_root or resolve_project_root()
    snapshot_on = snapshot_on or date.today()

    compile_result = compile_intake(
        resolved_workspace,
        project_root=project_root,
        compiled_on=snapshot_on,
    )
    pipeline_result = execute_pipeline(
        resolved_workspace / "questionnaire.yaml",
        output_dir=resolved_workspace / "reports",
    )

    field_index, field_to_section = load_field_metadata(project_root)
    role_resolution = load_role_resolution(resolved_workspace)
    compile_totals = _count_statuses(compile_result["all_fields"])
    compile_totals["total"] = len(compile_result["all_fields"])

    unresolved_fields = collect_unresolved_fields(
        compile_result["all_fields"],
        field_index,
        field_to_section,
        role_resolution["role_to_persons"],
    )
    unresolved_by_strictness: dict[str, list[dict[str, Any]]] = {}
    for field in unresolved_fields:
        strictness = field["strictness"] or "unknown"
        unresolved_by_strictness.setdefault(strictness, []).append(field)

    pipeline_errors = pipeline_error_records(pipeline_result["issues"])
    unresolved_s4_fields = unresolved_by_strictness.get("S4", [])
    baseline_ready = not pipeline_errors and not unresolved_s4_fields

    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_at": snapshot_on.isoformat(),
        "date_used": snapshot_on.isoformat(),
        "object_id": compile_result["object_id"],
        "workspace": str(resolved_workspace),
        "questionnaire_path": str(resolved_workspace / "questionnaire.yaml"),
        "compile": {
            "totals": compile_totals,
            "warnings": list(compile_result["warnings"]),
        },
        "fields": {
            "unresolved": unresolved_fields,
            "unresolved_by_strictness": unresolved_by_strictness,
        },
        "roles": role_resolution,
        "pipeline": {
            "status": pipeline_result["validation"]["status"],
            "error_count": pipeline_result["validation"]["error_count"],
            "warning_count": pipeline_result["validation"]["warning_count"],
            "confidence_level": pipeline_result["validation"]["confidence_level"],
            "assumed_count": pipeline_result["validation"]["assumed_count"],
            "errors": pipeline_errors,
            "issues": list(pipeline_result["issues"]),
        },
        "blockers": build_blockers(pipeline_errors, unresolved_s4_fields),
        "baseline_ready": baseline_ready,
    }
