from __future__ import annotations

from pathlib import Path

from network_methodology_sandbox import run_pipeline as canonical_run_pipeline
import run_pipeline as legacy_run_pipeline


def test_run_pipeline_canonical_module_is_self_hosted() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    canonical_path = repo_root / "project/src/network_methodology_sandbox/run_pipeline.py"
    legacy_path = repo_root / "project/src/run_pipeline.py"

    canonical_content = canonical_path.read_text(encoding="utf-8")
    legacy_content = legacy_path.read_text(encoding="utf-8")

    assert "from run_pipeline import" not in canonical_content
    assert "from network_methodology_sandbox.run_pipeline import" in legacy_content


def test_legacy_run_pipeline_wrapper_preserves_manifest_path_behavior(tmp_path: Path) -> None:
    base = tmp_path / "repo"
    target = base / "project" / "reports" / "validation.summary.yaml"
    target.parent.mkdir(parents=True)
    target.write_text("status: ok\n", encoding="utf-8")

    assert canonical_run_pipeline._manifest_path(target, base_dir=base) == (
        legacy_run_pipeline._manifest_path(target, base_dir=base)
    )
