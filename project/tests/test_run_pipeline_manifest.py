from __future__ import annotations

from pathlib import Path

import pytest

from model_utils import load_yaml
from run_pipeline import _manifest_path, execute_pipeline

from conftest import copy_workspace

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HAPPY_PATH = PROJECT_ROOT / "examples" / "sample_object_01"


def test_manifest_path_prefers_relative_path_under_base(tmp_path):
    base = tmp_path / "repo"
    target = base / "project" / "specs" / "requirements" / "object_requirements_v2.schema.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("schema: test\n", encoding="utf-8")

    assert _manifest_path(target, base_dir=base) == (
        "project/specs/requirements/object_requirements_v2.schema.yaml"
    )


def test_manifest_path_falls_back_to_absolute_outside_base(tmp_path):
    base = tmp_path / "repo"
    base.mkdir()
    external = tmp_path / "external" / "questionnaire.yaml"
    external.parent.mkdir(parents=True)
    external.write_text("version: 0.2.0\n", encoding="utf-8")

    assert _manifest_path(external, base_dir=base) == str(external.resolve())


def test_execute_pipeline_manifest_uses_intake_compiled_date(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)

    execute_pipeline(workspace / "questionnaire.yaml")

    payload = load_yaml(workspace / "reports" / "workspace.manifest.yaml")

    assert payload["date_used"] == "2026-04-02"
    assert payload["summary"]["by_producer"]["pipeline"] == 6


def test_execute_pipeline_requires_manifest_date_source(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)
    (workspace / "reports" / "intake_status.yaml").unlink()

    with pytest.raises(ValueError, match="Pipeline manifest date_used requires"):
        execute_pipeline(workspace / "questionnaire.yaml")

    assert not (workspace / "reports" / "workspace.manifest.yaml").exists()


def test_execute_pipeline_skips_manifest_contract_when_write_outputs_disabled(tmp_path):
    workspace = copy_workspace(tmp_path, HAPPY_PATH)
    (workspace / "reports" / "intake_status.yaml").unlink()

    result = execute_pipeline(
        workspace / "questionnaire.yaml",
        write_outputs=False,
    )

    assert result["validation"]["status"] == "ok"
    assert not (workspace / "reports" / "workspace.manifest.yaml").exists()
