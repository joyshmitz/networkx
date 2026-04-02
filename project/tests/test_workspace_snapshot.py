from __future__ import annotations

from pathlib import Path

from intake.workspace_snapshot import SNAPSHOT_SCHEMA_VERSION, build_workspace_snapshot

from conftest import GOLDEN_DATE, copy_workspace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HAPPY_PATH = PROJECT_ROOT / "examples" / "sample_object_01"
STRESS_PATH = PROJECT_ROOT / "examples" / "sample_object_02"


def test_snapshot_sample01_summary_and_role_resolution(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)

    snapshot = build_workspace_snapshot(
        workspace,
        project_root=PROJECT_ROOT,
        snapshot_on=GOLDEN_DATE,
    )

    assert snapshot["schema_version"] == SNAPSHOT_SCHEMA_VERSION
    assert snapshot["object_id"] == "sample_object_01"
    assert snapshot["baseline_ready"] is True
    assert snapshot["compile"]["totals"] == {
        "answered": 41,
        "tbd": 0,
        "unanswered": 0,
        "not_applicable": 0,
        "total": 41,
    }
    assert snapshot["roles"]["role_to_persons"]["project_manager"] == ["sample_pm_owner"]
    assert snapshot["roles"]["person_to_roles"]["sample_arch"] == [
        "network_engineer",
        "ot_architect",
    ]
    assert snapshot["evidence"]["status"] == "not_collected"
    assert snapshot["evidence"]["requirements"]
    assert snapshot["fields"]["unresolved_by_strictness"].get("S4", []) == []


def test_snapshot_sample02_tracks_sorted_unresolved_fields_and_person_resolution(tmp_path):
    workspace = copy_workspace(tmp_path, STRESS_PATH)

    snapshot = build_workspace_snapshot(
        workspace,
        project_root=PROJECT_ROOT,
        snapshot_on=GOLDEN_DATE,
    )

    unresolved = snapshot["fields"]["unresolved"]
    assert unresolved == sorted(unresolved, key=lambda item: (item["section"], item["field_id"]))

    unresolved_s4 = snapshot["fields"]["unresolved_by_strictness"]["S4"]
    assert [field["field_id"] for field in unresolved_s4] == [
        "sat_required",
        "control_required",
        "oob_required",
    ]

    control_required = next(field for field in unresolved_s4 if field["field_id"] == "control_required")
    assert control_required["owner_role"] == "process_engineer"
    assert control_required["owner_persons"] == ["sample2_process_telemetry"]
    assert control_required["reviewer_persons"] == [
        "sample2_ops_sec",
        "sample2_process_telemetry",
    ]

    error_validators = {issue["validator"] for issue in snapshot["pipeline"]["errors"]}
    assert error_validators == {"resilience", "time"}
    assert any(blocker["kind"] == "pipeline_error" for blocker in snapshot["blockers"])
    assert any(blocker["kind"] == "unresolved_s4" for blocker in snapshot["blockers"])


def test_snapshot_does_not_write_pipeline_outputs_by_default(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)
    pipeline_manifest = workspace / "reports" / "pipeline.manifest.yaml"
    pipeline_summary = workspace / "reports" / "validation.summary.yaml"
    pipeline_manifest.unlink()
    pipeline_summary.unlink()

    snapshot = build_workspace_snapshot(
        workspace,
        project_root=PROJECT_ROOT,
        snapshot_on=GOLDEN_DATE,
    )

    assert snapshot["pipeline"]["status"] == "ok"
    assert not pipeline_manifest.exists()
    assert not pipeline_summary.exists()


def test_snapshot_missing_workspace_raises_file_not_found(tmp_path):
    missing_workspace = tmp_path / "missing_workspace"

    try:
        build_workspace_snapshot(
            missing_workspace,
            project_root=PROJECT_ROOT,
            snapshot_on=GOLDEN_DATE,
        )
    except FileNotFoundError as exc:
        assert "Workspace not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError for missing workspace")


def test_snapshot_file_path_raises_not_a_directory(tmp_path):
    workspace_file = tmp_path / "workspace.txt"
    workspace_file.write_text("not a directory\n", encoding="utf-8")

    try:
        build_workspace_snapshot(
            workspace_file,
            project_root=PROJECT_ROOT,
            snapshot_on=GOLDEN_DATE,
        )
    except NotADirectoryError as exc:
        assert "Snapshot expects a workspace directory" in str(exc)
    else:
        raise AssertionError("Expected NotADirectoryError for file workspace path")
