from __future__ import annotations

from pathlib import Path


TARGET_FILES = [
    "project/src/compiler/build_requirements_model.py",
    "project/src/compiler/compile_graphs.py",
    "project/src/compiler/cross_field_inference.py",
    "project/src/reports/generate_handoff_matrix.py",
    "project/src/reports/generate_network_volume_summary.py",
    "project/src/validators/validate_annex_activation.py",
    "project/src/validators/validate_connectivity.py",
    "project/src/validators/validate_cross_graph.py",
    "project/src/validators/validate_power_ports.py",
    "project/src/validators/validate_resilience.py",
    "project/src/validators/validate_role_assignments.py",
    "project/src/validators/validate_segmentation.py",
    "project/src/validators/validate_semantic_consistency.py",
    "project/src/validators/validate_stage_confidence.py",
    "project/src/validators/validate_time.py",
    "project/src/run_pipeline.py",
]

LEGACY_IMPORT_PATTERNS = [
    "from model_utils import",
    "from compiler.",
    "from reports.",
    "from validators.",
]


def test_core_modules_no_longer_use_legacy_product_imports() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []

    for relative_path in TARGET_FILES:
        file_path = repo_root / relative_path
        content = file_path.read_text(encoding="utf-8")
        for pattern in LEGACY_IMPORT_PATTERNS:
            if pattern in content:
                offenders.append(f"{relative_path}: {pattern}")

    assert offenders == []
