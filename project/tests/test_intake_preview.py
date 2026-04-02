from __future__ import annotations

from pathlib import Path

from intake.preview_status import preview_workspace
from intake.workspace_snapshot import SNAPSHOT_SCHEMA_VERSION
from model_utils import load_yaml

from conftest import GOLDEN_DATE, copy_workspace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HAPPY_PATH = PROJECT_ROOT / "examples" / "sample_object_01"
STRESS_PATH = PROJECT_ROOT / "examples" / "sample_object_02"


def test_preview_sample01_is_baseline_ready(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)
    (workspace / "reports" / "pipeline.manifest.yaml").unlink()
    (workspace / "reports" / "validation.summary.yaml").unlink()

    result = preview_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        preview_on=GOLDEN_DATE,
    )

    yaml_report = workspace / "reports" / "preview_status.yaml"
    markdown_report = workspace / "reports" / "preview_status.md"
    pipeline_manifest = workspace / "reports" / "pipeline.manifest.yaml"
    validation_summary = workspace / "reports" / "validation.summary.yaml"
    payload = load_yaml(yaml_report)

    assert yaml_report.exists()
    assert markdown_report.exists()
    assert pipeline_manifest.exists()
    assert validation_summary.exists()
    assert result["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert payload["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert result["baseline_ready"] is True
    assert payload["baseline_ready"] is True
    assert result["compile"] == {
        "answered": 41,
        "tbd": 0,
        "unanswered": 0,
        "not_applicable": 0,
        "total": 41,
    }
    assert result["unresolved_s4_fields"] == []
    assert payload["unresolved_s4_fields"] == []
    assert result["pipeline"]["error_count"] == 0
    assert "baseline_ready: true" in markdown_report.read_text(encoding="utf-8")


def test_preview_sample02_reports_blockers_without_failing_preview(tmp_path):
    workspace = copy_workspace(tmp_path, STRESS_PATH)

    result = preview_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        preview_on=GOLDEN_DATE,
    )

    yaml_report = workspace / "reports" / "preview_status.yaml"
    payload = load_yaml(yaml_report)

    assert yaml_report.exists()
    assert result["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert payload["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert result["baseline_ready"] is False
    assert payload["baseline_ready"] is False
    assert result["pipeline"]["status"] == "failed"
    assert any(blocker["kind"] == "pipeline_error" for blocker in result["blockers"])
    assert result["unresolved_s4_fields"]

    unresolved_s4_ids = {field["field_id"] for field in result["unresolved_s4_fields"]}
    assert unresolved_s4_ids == {"control_required", "oob_required", "sat_required"}

    error_validators = {issue["validator"] for issue in result["pipeline"]["errors"]}
    assert error_validators == {"resilience", "time"}
