from __future__ import annotations

from pathlib import Path

from network_methodology_sandbox import model_utils as canonical_model_utils
import model_utils as legacy_model_utils


def test_model_utils_canonical_module_is_self_hosted() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    canonical_path = repo_root / "project/src/network_methodology_sandbox/model_utils.py"
    legacy_path = repo_root / "project/src/model_utils.py"

    canonical_content = canonical_path.read_text(encoding="utf-8")
    legacy_content = legacy_path.read_text(encoding="utf-8")

    assert "from model_utils import" not in canonical_content
    assert "from network_methodology_sandbox.model_utils import" in legacy_content


def test_legacy_model_utils_wrapper_preserves_behavior() -> None:
    assert canonical_model_utils.resolve_project_root() == legacy_model_utils.resolve_project_root()
    assert canonical_model_utils.is_yes(True) is legacy_model_utils.is_yes(True)
    assert canonical_model_utils.is_no(False) is legacy_model_utils.is_no(False)
    assert canonical_model_utils.is_tbd(None) is legacy_model_utils.is_tbd(None)
