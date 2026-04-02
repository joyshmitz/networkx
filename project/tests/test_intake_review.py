from __future__ import annotations

from pathlib import Path

import yaml

from intake.review_packets import review_workspace
from model_utils import load_yaml

from conftest import GOLDEN_DATE, copy_workspace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STRESS_PATH = PROJECT_ROOT / "examples" / "sample_object_02"


def _review_item(
    result: dict[str, object],
    *,
    source_kind: str,
    source_key: str,
) -> dict[str, object]:
    for item in result["review_items"]:  # type: ignore[index]
        if item["source_kind"] == source_kind and item["source_key"] == source_key:
            return item
    raise AssertionError(f"Missing review item for {source_kind=} {source_key=}")


def _rewrite_roles_for_second_reviewer_case(workspace: Path) -> None:
    payload = load_yaml(workspace / "role_assignments.yaml")
    assignments = payload["assignments"]

    for assignment in assignments:
        roles = set(assignment["roles"])
        if assignment["person_id"] == "sample2_iiot_commissioning":
            roles.update({"object_owner", "operations_engineer"})
        elif assignment["person_id"] == "sample2_pm_owner":
            roles.discard("object_owner")
        elif assignment["person_id"] == "sample2_ops_sec":
            roles.discard("operations_engineer")
        assignment["roles"] = sorted(roles)

    (workspace / "role_assignments.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def test_review_routes_assigned_field_items_to_primary_and_secondary_people(tmp_path):
    workspace = copy_workspace(tmp_path, STRESS_PATH)

    result = review_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        review_on=GOLDEN_DATE,
    )

    registry_yaml = workspace / "reports" / "reviewer_registry.yaml"
    registry_md = workspace / "reports" / "reviewer_registry.md"
    coordinator_packet = workspace / "reports" / "review_packet._coordinator.md"

    assert registry_yaml.exists()
    assert registry_md.exists()
    assert coordinator_packet.exists()

    item = _review_item(result, source_kind="field", source_key="oob_required")
    assert item["routing_state"] == "assigned"
    assert item["primary_role"] == "operations_engineer"
    assert item["primary_person"] == "sample2_ops_sec"
    assert item["secondary_persons"] == ["sample2_arch"]
    assert item["priority"] == "critical"
    assert item["review_item_id"] == "sample_object_02.field.oob_required.operations_engineer"

    reviewer_registry = load_yaml(registry_yaml)
    reviewer_entry = next(
        reviewer
        for reviewer in reviewer_registry["reviewers"]
        if reviewer["person_id"] == "sample2_ops_sec"
    )
    assert item["review_item_id"] in reviewer_entry["primary_item_ids"]
    assert (workspace / "reports" / "review_packet.sample2_ops_sec.md").exists()
    assert (workspace / "reports" / "review_packet.sample2_arch.md").exists()


def test_review_sends_ambiguous_validator_issue_to_coordinator(tmp_path):
    workspace = copy_workspace(tmp_path, STRESS_PATH)

    result = review_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        review_on=GOLDEN_DATE,
    )

    item = _review_item(
        result,
        source_kind="validator_issue",
        source_key="time:ptp_required_for_timing_accuracy",
    )
    assert item["routing_state"] == "coordinator_escalation"
    assert item["primary_role"] == "coordinator"
    assert item["primary_person"] is None
    assert item["field_id"] == "timing_accuracy_class"
    assert item["related_field_ids"] == ["timing_accuracy_class", "sync_protocol"]
    assert "multiple fields" in item["escalation_reason"]

    coordinator_text = (workspace / "reports" / "review_packet._coordinator.md").read_text(
        encoding="utf-8"
    )
    assert item["review_item_id"] in coordinator_text


def test_review_marks_second_reviewer_required_when_s4_owner_and_reviewers_collapse(tmp_path):
    workspace = copy_workspace(tmp_path, STRESS_PATH)
    _rewrite_roles_for_second_reviewer_case(workspace)

    result = review_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        review_on=GOLDEN_DATE,
    )

    item = _review_item(result, source_kind="field", source_key="sat_required")
    assert item["routing_state"] == "second_reviewer_required"
    assert item["primary_role"] == "commissioning_engineer"
    assert item["primary_person"] == "sample2_iiot_commissioning"
    assert item["secondary_persons"] == []
    assert "independent reviewer" in item["escalation_reason"]

    coordinator_text = (workspace / "reports" / "review_packet._coordinator.md").read_text(
        encoding="utf-8"
    )
    assert item["review_item_id"] in coordinator_text
    assert (workspace / "reports" / "review_packet.sample2_iiot_commissioning.md").exists()


def test_review_generation_is_stable_across_repeated_runs(tmp_path):
    workspace = copy_workspace(tmp_path, STRESS_PATH)

    result_first = review_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        review_on=GOLDEN_DATE,
    )
    registry_first = (workspace / "reports" / "reviewer_registry.yaml").read_text(
        encoding="utf-8"
    )

    result_second = review_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        review_on=GOLDEN_DATE,
    )
    registry_second = (workspace / "reports" / "reviewer_registry.yaml").read_text(
        encoding="utf-8"
    )

    ids_first = [item["review_item_id"] for item in result_first["review_items"]]
    ids_second = [item["review_item_id"] for item in result_second["review_items"]]

    assert ids_first == ids_second
    assert len(ids_first) == len(set(ids_first))
    assert registry_first == registry_second
