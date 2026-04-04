from __future__ import annotations

from pathlib import Path


TARGET_FILES = [
    "project/src/intake/workspace_manifest.py",
    "project/src/intake/workspace_snapshot.py",
    "project/src/intake/init_workspace.py",
    "project/src/intake/generate_intake_sheets.py",
    "project/src/intake/compile_intake.py",
    "project/src/intake/preview_status.py",
    "project/src/intake/review_packets.py",
    "project/src/intake/evidence_status.py",
    "project/src/run_pipeline.py",
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
