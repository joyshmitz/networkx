from __future__ import annotations

from pathlib import Path

from run_pipeline import _manifest_path


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
