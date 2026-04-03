from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook

from intake.evidence_status import EVIDENCE_SCHEMA_VERSION, evidence_workspace
from intake.review_packets import review_workspace
from model_utils import load_yaml

from conftest import GOLDEN_DATE, copy_workspace, find_evidence_field, find_review_item

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HAPPY_PATH = PROJECT_ROOT / "examples" / "sample_object_01"
STRESS_PATH = PROJECT_ROOT / "examples" / "sample_object_02"


def _set_source_ref(workspace: Path, field_id: str, source_ref: str) -> None:
    responses_dir = workspace / "intake" / "responses"
    for workbook_path in sorted(responses_dir.glob("*.xlsx")):
        workbook = load_workbook(workbook_path)
        worksheet = workbook["intake"]
        for row in range(7, worksheet.max_row + 1):
            if worksheet.cell(row, 1).value == field_id:
                worksheet.cell(row, 8).value = source_ref
                workbook.save(workbook_path)
                return
    raise AssertionError(f"Field {field_id!r} not found in any intake workbook")


def _set_field_raw_value(workspace: Path, field_id: str, raw_value: str) -> None:
    responses_dir = workspace / "intake" / "responses"
    for workbook_path in sorted(responses_dir.glob("*.xlsx")):
        workbook = load_workbook(workbook_path)
        worksheet = workbook["intake"]
        for row in range(7, worksheet.max_row + 1):
            if worksheet.cell(row, 1).value == field_id:
                worksheet.cell(row, 5).value = raw_value
                worksheet.cell(row, 6).value = None
                workbook.save(workbook_path)
                return
    raise AssertionError(f"Field {field_id!r} not found in any intake workbook")


def test_evidence_status_sample01_is_advisory_only_and_writes_reports(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)

    result = evidence_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        evidence_on=GOLDEN_DATE,
    )

    yaml_report = workspace / "reports" / "evidence_status.yaml"
    markdown_report = workspace / "reports" / "evidence_status.md"
    payload = load_yaml(yaml_report)

    assert yaml_report.exists()
    assert markdown_report.exists()
    assert result["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert payload["schema_version"] == EVIDENCE_SCHEMA_VERSION
    assert result["metadata"]["project_stage"] == "concept"
    assert result["summary"]["selected_field_count"] > 0
    assert result["summary"]["advisory_gap_count"] > 0
    assert result["summary"]["blocking_eligible_count"] == 0
    assert all(field["blocking_eligible"] is False for field in result["fields"])
    assert "Blocking-eligible fields: 0" in markdown_report.read_text(encoding="utf-8")


def test_evidence_status_derives_reference_structured_and_workspace_artifact(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)
    _set_source_ref(workspace, "control_required", "site survey notebook 2026-04-02")
    _set_source_ref(workspace, "oob_required", "path=evidence/oob_basis.md")
    _set_source_ref(workspace, "sat_required", "path=evidence/sat_basis.md")
    artifact_dir = workspace / "evidence"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "sat_basis.md").write_text("SAT basis\n", encoding="utf-8")

    result = evidence_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        evidence_on=GOLDEN_DATE,
    )

    control_required = find_evidence_field(result, "control_required")
    oob_required = find_evidence_field(result, "oob_required")
    sat_required = find_evidence_field(result, "sat_required")

    assert control_required["evidence_strength"] == "reference_only"
    assert control_required["advisory_gap"] is True
    assert control_required["gap_reason"] == "weak evidence: reference_only < structured_ref"
    assert control_required["review_routing_required"] is False

    assert oob_required["evidence_strength"] == "structured_ref"
    assert oob_required["advisory_gap"] is False
    assert oob_required["workspace_artifacts"] == []

    assert sat_required["evidence_strength"] == "workspace_artifact"
    assert sat_required["advisory_gap"] is False
    assert sat_required["workspace_artifacts"] == ["evidence/sat_basis.md"]


def test_review_packets_include_evidence_gap_for_unresolved_selected_field(tmp_path):
    workspace = copy_workspace(tmp_path, STRESS_PATH)

    result = review_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        review_on=GOLDEN_DATE,
    )

    item = find_review_item(result, source_kind="evidence_gap", source_key="control_required")
    assert item["routing_state"] == "assigned"
    assert item["primary_role"] == "process_engineer"
    assert item["primary_person"] == "sample2_process_telemetry"
    assert item["review_item_id"] == "sample_object_02.evidence_gap.control_required.process_engineer"
    assert "missing evidence" in item["review_reasons"]


def test_evidence_status_marks_blocking_eligible_in_detailed_design(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)
    _set_field_raw_value(workspace, "project_stage", "detailed_design")

    result = evidence_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        evidence_on=GOLDEN_DATE,
    )

    control_required = find_evidence_field(result, "control_required")
    sat_required = find_evidence_field(result, "sat_required")

    assert result["metadata"]["project_stage"] == "detailed_design"
    assert result["summary"]["blocking_eligible_count"] > 0
    assert control_required["blocking_eligible"] is True
    assert sat_required["blocking_eligible"] is True
