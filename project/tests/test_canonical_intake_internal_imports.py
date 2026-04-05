from __future__ import annotations

from pathlib import Path


TARGET_FILES = [
    "project/src/network_methodology_sandbox/intake/workspace_manifest.py",
    "project/src/network_methodology_sandbox/intake/workspace_snapshot.py",
    "project/src/network_methodology_sandbox/intake/init_workspace.py",
    "project/src/network_methodology_sandbox/intake/generate_intake_sheets.py",
    "project/src/network_methodology_sandbox/intake/compile_intake.py",
    "project/src/network_methodology_sandbox/intake/preview_status.py",
    "project/src/network_methodology_sandbox/intake/review_packets.py",
    "project/src/network_methodology_sandbox/intake/evidence_status.py",
    "project/src/network_methodology_sandbox/run_pipeline.py",
]

REMOVED_LEGACY_FILES = [
    "project/src/intake/workspace_manifest.py",
    "project/src/intake/workspace_snapshot.py",
    "project/src/intake/init_workspace.py",
    "project/src/intake/generate_intake_sheets.py",
    "project/src/intake/compile_intake.py",
    "project/src/intake/preview_status.py",
    "project/src/intake/review_packets.py",
    "project/src/intake/evidence_status.py",
]

LEGACY_IMPORT_PATTERNS = [
    "from intake.",
    "from model_utils import",
    "from run_pipeline import",
    "from validators.",
]


def test_intake_family_no_longer_uses_legacy_product_imports() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []

    for relative_path in TARGET_FILES:
        file_path = repo_root / relative_path
        content = file_path.read_text(encoding="utf-8")
        for pattern in LEGACY_IMPORT_PATTERNS:
            if pattern in content:
                offenders.append(f"{relative_path}: {pattern}")

    assert offenders == []


def test_legacy_intake_paths_are_removed() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    for relative_path in REMOVED_LEGACY_FILES:
        assert not (repo_root / relative_path).exists()
