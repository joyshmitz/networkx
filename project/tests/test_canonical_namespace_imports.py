from __future__ import annotations

import subprocess
import sys
from pathlib import Path


CANONICAL_MODULES = [
    "network_methodology_sandbox.model_utils",
    "network_methodology_sandbox.run_pipeline",
    "network_methodology_sandbox.compiler.build_requirements_model",
    "network_methodology_sandbox.compiler.compile_graphs",
    "network_methodology_sandbox.compiler.cross_field_inference",
    "network_methodology_sandbox.intake.init_workspace",
    "network_methodology_sandbox.intake.generate_intake_sheets",
    "network_methodology_sandbox.intake.compile_intake",
    "network_methodology_sandbox.intake.preview_status",
    "network_methodology_sandbox.intake.review_packets",
    "network_methodology_sandbox.intake.evidence_status",
    "network_methodology_sandbox.reports.generate_handoff_matrix",
    "network_methodology_sandbox.reports.generate_network_volume_summary",
    "network_methodology_sandbox.validators.validate_annex_activation",
    "network_methodology_sandbox.validators.validate_connectivity",
    "network_methodology_sandbox.validators.validate_cross_graph",
    "network_methodology_sandbox.validators.validate_power_ports",
    "network_methodology_sandbox.validators.validate_resilience",
    "network_methodology_sandbox.validators.validate_role_assignments",
    "network_methodology_sandbox.validators.validate_segmentation",
    "network_methodology_sandbox.validators.validate_semantic_consistency",
    "network_methodology_sandbox.validators.validate_stage_confidence",
    "network_methodology_sandbox.validators.validate_time",
]


def test_canonical_namespace_import_surface_is_complete(tmp_path: Path) -> None:
    code = "\n".join(
        [
            "import importlib",
            f"modules = {CANONICAL_MODULES!r}",
            "for name in modules:",
            "    importlib.import_module(name)",
            "print('ok')",
            "",
        ]
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "ok"
