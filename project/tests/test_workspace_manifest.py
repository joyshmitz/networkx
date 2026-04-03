from __future__ import annotations

from pathlib import Path

from intake.compile_intake import compile_intake
from intake.evidence_status import evidence_workspace
from intake.preview_status import preview_workspace
from intake.review_packets import review_workspace
from intake.workspace_manifest import WORKSPACE_MANIFEST_SCHEMA_VERSION
from model_utils import load_yaml

from conftest import GOLDEN_DATE, copy_workspace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HAPPY_PATH = PROJECT_ROOT / "examples" / "sample_object_01"
STRESS_PATH = PROJECT_ROOT / "examples" / "sample_object_02"


def _artifact_paths(payload: dict[str, object]) -> set[str]:
    return {
        artifact["path"]
        for artifact in payload["artifacts"]
    }


def test_compile_intake_writes_workspace_manifest_for_compile_outputs(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)

    compile_intake(
        workspace,
        project_root=PROJECT_ROOT,
        compiled_on=GOLDEN_DATE,
    )

    manifest_path = workspace / "reports" / "workspace.manifest.yaml"
    payload = load_yaml(manifest_path)

    assert manifest_path.exists()
    assert payload["schema_version"] == WORKSPACE_MANIFEST_SCHEMA_VERSION
    assert payload["date_used"] == GOLDEN_DATE.isoformat()
    assert payload["object_id"] == "sample_object_01"
    assert payload["summary"]["artifact_count"] == 3
    assert payload["summary"]["by_producer"] == {"compile": 3}
    assert _artifact_paths(payload) == {
        "questionnaire.yaml",
        "reports/intake_status.yaml",
        "reports/intake_status.md",
    }


def test_preview_refreshes_workspace_manifest_with_pipeline_and_preview_outputs(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)
    (workspace / "reports" / "pipeline.manifest.yaml").unlink()
    (workspace / "reports" / "validation.summary.yaml").unlink()

    preview_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        preview_on=GOLDEN_DATE,
    )

    payload = load_yaml(workspace / "reports" / "workspace.manifest.yaml")
    paths = _artifact_paths(payload)

    assert payload["schema_version"] == WORKSPACE_MANIFEST_SCHEMA_VERSION
    assert payload["summary"]["by_producer"] == {
        "compile": 3,
        "pipeline": 6,
        "preview": 2,
    }
    assert payload["summary"]["artifact_count"] == 11
    assert {
        "questionnaire.yaml",
        "reports/intake_status.yaml",
        "reports/intake_status.md",
        "reports/requirements.compiled.yaml",
        "reports/graphs.summary.yaml",
        "reports/validation.summary.yaml",
        "reports/pipeline.manifest.yaml",
        "reports/network_volume_summary.md",
        "reports/handoff_matrix.md",
        "reports/preview_status.yaml",
        "reports/preview_status.md",
    } == paths


def test_workspace_manifest_tracks_review_and_evidence_outputs_stably(tmp_path):
    workspace = copy_workspace(tmp_path, STRESS_PATH)

    preview_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        preview_on=GOLDEN_DATE,
    )
    review_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        review_on=GOLDEN_DATE,
    )
    evidence_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        evidence_on=GOLDEN_DATE,
    )

    manifest_path = workspace / "reports" / "workspace.manifest.yaml"
    manifest_first = manifest_path.read_text(encoding="utf-8")
    payload = load_yaml(manifest_path)
    paths = _artifact_paths(payload)

    assert payload["schema_version"] == WORKSPACE_MANIFEST_SCHEMA_VERSION
    assert payload["summary"]["by_producer"]["compile"] == 3
    assert payload["summary"]["by_producer"]["pipeline"] == 6
    assert payload["summary"]["by_producer"]["preview"] == 2
    assert payload["summary"]["by_producer"]["evidence"] == 2
    assert payload["summary"]["by_producer"]["review"] >= 3
    assert "reports/reviewer_registry.yaml" in paths
    assert "reports/reviewer_registry.md" in paths
    assert "reports/review_packet._coordinator.md" in paths
    assert "reports/evidence_status.yaml" in paths
    assert "reports/evidence_status.md" in paths
    assert any(
        path.startswith("reports/review_packet.")
        and path != "reports/review_packet._coordinator.md"
        for path in paths
    )

    review_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        review_on=GOLDEN_DATE,
    )
    evidence_workspace(
        workspace,
        project_root=PROJECT_ROOT,
        evidence_on=GOLDEN_DATE,
    )
    manifest_second = manifest_path.read_text(encoding="utf-8")

    assert manifest_first == manifest_second
