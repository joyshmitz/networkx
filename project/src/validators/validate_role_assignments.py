from __future__ import annotations

from pathlib import Path
from typing import Any

from model_utils import load_yaml, resolve_project_root


def default_fields_path() -> Path:
    return resolve_project_root() / "specs" / "dictionary" / "questionnaire_v2_fields.yaml"


def load_field_specs(path: Path | None = None) -> list[dict[str, Any]]:
    payload = load_yaml(path or default_fields_path())
    return payload.get("fields", [])


def build_person_to_roles(assignments: list[dict[str, Any]]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for entry in assignments:
        person_id = entry.get("person_id", "")
        roles = set(entry.get("roles", []))
        if person_id in mapping:
            mapping[person_id] |= roles
        else:
            mapping[person_id] = roles
    return mapping


def build_role_to_persons(person_to_roles: dict[str, set[str]]) -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for person_id, roles in person_to_roles.items():
        for role in roles:
            mapping.setdefault(role, set()).add(person_id)
    return mapping


def validate_role_assignments(
    role_assignments: dict[str, Any] | None,
    fields_path: Path | None = None,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    if role_assignments is None:
        issues.append({
            "validator": "role_assignments",
            "severity": "warning",
            "message": "No role_assignments provided — role conflict checks skipped.",
        })
        return issues

    assignments = role_assignments.get("assignments", [])
    if not assignments:
        issues.append({
            "validator": "role_assignments",
            "severity": "warning",
            "message": "Role assignments are empty — no person-to-role mapping defined.",
        })
        return issues

    person_to_roles = build_person_to_roles(assignments)
    role_to_persons = build_role_to_persons(person_to_roles)

    field_specs = load_field_specs(fields_path)

    # Check all defined roles are assigned to at least one person
    all_assigned_roles = set()
    for roles in person_to_roles.values():
        all_assigned_roles.update(roles)

    for spec in field_specs:
        owner_role = spec.get("owner_role")
        if owner_role and owner_role not in all_assigned_roles:
            issues.append({
                "validator": "role_assignments",
                "severity": "warning",
                "message": (
                    f"Field '{spec['field_id']}' owner_role '{owner_role}' "
                    f"is not assigned to any person."
                ),
            })

    # S4 conflict: owner and all reviewers collapse to one person
    for spec in field_specs:
        if spec.get("strictness") != "S4":
            continue
        field_id = spec["field_id"]
        owner_role = spec.get("owner_role")
        reviewer_roles = spec.get("reviewer_roles", [])

        if not owner_role or not reviewer_roles:
            continue

        owner_persons = role_to_persons.get(owner_role, set())
        reviewer_persons: set[str] = set()
        for rev_role in reviewer_roles:
            reviewer_persons.update(role_to_persons.get(rev_role, set()))

        if not owner_persons or not reviewer_persons:
            continue

        # If every person who owns also reviews, and no independent reviewer exists
        independent_reviewers = reviewer_persons - owner_persons
        if not independent_reviewers:
            collapsed = owner_persons & reviewer_persons
            issues.append({
                "validator": "role_assignments",
                "severity": "error",
                "message": (
                    f"S4 field '{field_id}': owner ({owner_role}) and all reviewers "
                    f"({', '.join(reviewer_roles)}) resolve to the same person(s) "
                    f"{sorted(collapsed)}. Second reviewer required."
                ),
            })

    return issues
