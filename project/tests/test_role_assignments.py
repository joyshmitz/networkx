"""Tests for role assignment validator."""

from __future__ import annotations

from validators.validate_role_assignments import (
    build_person_to_roles,
    build_role_to_persons,
    validate_role_assignments,
)


def _issues_by(issues, severity=None):
    return [i for i in issues if severity is None or i["severity"] == severity]


class TestPersonRoleMapping:
    def test_build_person_to_roles(self):
        assignments = [
            {"person_id": "p1", "roles": ["role_a", "role_b"]},
            {"person_id": "p2", "roles": ["role_c"]},
        ]
        mapping = build_person_to_roles(assignments)
        assert mapping["p1"] == {"role_a", "role_b"}
        assert mapping["p2"] == {"role_c"}

    def test_duplicate_person_id_unions_roles(self):
        assignments = [
            {"person_id": "p1", "roles": ["role_a"]},
            {"person_id": "p1", "roles": ["role_b"]},
        ]
        mapping = build_person_to_roles(assignments)
        assert mapping["p1"] == {"role_a", "role_b"}

    def test_build_role_to_persons(self):
        p2r = {"p1": {"role_a", "role_b"}, "p2": {"role_a"}}
        r2p = build_role_to_persons(p2r)
        assert r2p["role_a"] == {"p1", "p2"}
        assert r2p["role_b"] == {"p1"}


class TestValidateRoleAssignments:
    def test_none_warns(self):
        issues = validate_role_assignments(None)
        assert len(_issues_by(issues, "warning")) == 1
        assert "skipped" in issues[0]["message"]

    def test_empty_assignments_warns(self):
        issues = validate_role_assignments({"assignments": []})
        assert len(_issues_by(issues, "warning")) == 1
        assert "empty" in issues[0]["message"]

    def test_unassigned_owner_role_warns(self):
        # process_engineer not assigned
        ra = {"assignments": [
            {"person_id": "p1", "roles": ["project_manager"]},
        ]}
        issues = validate_role_assignments(ra)
        warnings = _issues_by(issues, "warning")
        assert any("process_engineer" in w["message"] for w in warnings)

    def test_s4_conflict_single_person_errors(self):
        # object_id is S4: owner=project_manager, reviewer=ot_architect
        # If one person holds both roles, that's a conflict
        ra = {"assignments": [
            {"person_id": "solo", "roles": ["project_manager", "ot_architect"]},
        ]}
        issues = validate_role_assignments(ra)
        errors = _issues_by(issues, "error")
        assert any("object_id" in e["message"] and "solo" in e["message"] for e in errors)

    def test_s4_no_conflict_with_independent_reviewer(self):
        # owner=project_manager on p1, reviewer=ot_architect on p2 → no conflict
        ra = {"assignments": [
            {"person_id": "p1", "roles": ["project_manager"]},
            {"person_id": "p2", "roles": ["ot_architect"]},
        ]}
        issues = validate_role_assignments(ra)
        errors = _issues_by(issues, "error")
        s4_errors = [e for e in errors if "S4" in e["message"]]
        # object_id: owner=project_manager(p1), reviewer=ot_architect(p2) → independent
        assert not any("object_id" in e["message"] for e in s4_errors)

    def test_s4_conflict_with_partial_overlap(self):
        # If p1 holds both owner and reviewer role, but p2 also holds reviewer → independent reviewer exists
        ra = {"assignments": [
            {"person_id": "p1", "roles": ["project_manager", "ot_architect"]},
            {"person_id": "p2", "roles": ["ot_architect"]},
        ]}
        issues = validate_role_assignments(ra)
        errors = _issues_by(issues, "error")
        # p2 is independent reviewer for ot_architect → no conflict for object_id
        assert not any("object_id" in e["message"] for e in errors)

    def test_full_coverage_no_warnings(self):
        """All 12 roles assigned → no 'not assigned' warnings."""
        all_roles = [
            "project_manager", "object_owner", "process_engineer",
            "ot_architect", "network_engineer", "cybersecurity_engineer",
            "cabinet_power_engineer", "telemetry_engineer", "video_engineer",
            "iiot_engineer", "operations_engineer", "commissioning_engineer",
        ]
        ra = {"assignments": [
            {"person_id": f"p{i}", "roles": [role]}
            for i, role in enumerate(all_roles)
        ]}
        issues = validate_role_assignments(ra)
        unassigned = [w for w in _issues_by(issues, "warning") if "not assigned" in w["message"]]
        assert len(unassigned) == 0
