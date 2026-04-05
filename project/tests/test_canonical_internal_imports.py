from __future__ import annotations

from pathlib import Path


TARGET_FILES = [
    "src/network_methodology_sandbox/compiler/build_requirements_model.py",
    "src/network_methodology_sandbox/compiler/compile_graphs.py",
    "src/network_methodology_sandbox/compiler/cross_field_inference.py",
    "src/network_methodology_sandbox/reports/generate_handoff_matrix.py",
    "src/network_methodology_sandbox/reports/generate_network_volume_summary.py",
    "src/network_methodology_sandbox/validators/validate_annex_activation.py",
    "src/network_methodology_sandbox/validators/validate_connectivity.py",
    "src/network_methodology_sandbox/validators/validate_cross_graph.py",
    "src/network_methodology_sandbox/validators/validate_power_ports.py",
    "src/network_methodology_sandbox/validators/validate_resilience.py",
    "src/network_methodology_sandbox/validators/validate_role_assignments.py",
    "src/network_methodology_sandbox/validators/validate_segmentation.py",
    "src/network_methodology_sandbox/validators/validate_semantic_consistency.py",
    "src/network_methodology_sandbox/validators/validate_stage_confidence.py",
    "src/network_methodology_sandbox/validators/validate_time.py",
    "src/network_methodology_sandbox/run_pipeline.py",
]

REMOVED_LEGACY_FILES = [
    "src/compiler/build_requirements_model.py",
    "src/compiler/compile_graphs.py",
    "src/compiler/cross_field_inference.py",
    "src/reports/generate_handoff_matrix.py",
    "src/reports/generate_network_volume_summary.py",
    "src/validators/validate_annex_activation.py",
    "src/validators/validate_connectivity.py",
    "src/validators/validate_cross_graph.py",
    "src/validators/validate_power_ports.py",
    "src/validators/validate_resilience.py",
    "src/validators/validate_role_assignments.py",
    "src/validators/validate_segmentation.py",
    "src/validators/validate_semantic_consistency.py",
    "src/validators/validate_stage_confidence.py",
    "src/validators/validate_time.py",
    "src/run_pipeline.py",
]

LEGACY_IMPORT_PATTERNS = [
    "from model_utils import",
    "from compiler.",
    "from reports.",
    "from validators.",
]


def test_core_modules_no_longer_use_legacy_product_imports() -> None:
    product_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []

    for relative_path in TARGET_FILES:
        file_path = product_root / relative_path
        content = file_path.read_text(encoding="utf-8")
        for pattern in LEGACY_IMPORT_PATTERNS:
            if pattern in content:
                offenders.append(f"{relative_path}: {pattern}")

    assert offenders == []


def test_legacy_core_paths_are_removed() -> None:
    product_root = Path(__file__).resolve().parents[1]

    for relative_path in REMOVED_LEGACY_FILES:
        assert not (product_root / relative_path).exists()
