from __future__ import annotations

from pathlib import Path

import compiler.build_requirements_model as legacy_build_requirements_model
import compiler.compile_graphs as legacy_compile_graphs
import compiler.cross_field_inference as legacy_cross_field_inference
import reports.generate_handoff_matrix as legacy_generate_handoff_matrix
import reports.generate_network_volume_summary as legacy_generate_network_volume_summary
from network_methodology_sandbox.compiler import build_requirements_model as canonical_build_requirements_model
from network_methodology_sandbox.compiler import compile_graphs as canonical_compile_graphs
from network_methodology_sandbox.compiler import cross_field_inference as canonical_cross_field_inference
from network_methodology_sandbox.reports import generate_handoff_matrix as canonical_generate_handoff_matrix
from network_methodology_sandbox.reports import (
    generate_network_volume_summary as canonical_generate_network_volume_summary,
)


def test_compiler_and_reports_canonical_modules_are_self_hosted() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    checks = [
        (
            repo_root / "project/src/network_methodology_sandbox/compiler/build_requirements_model.py",
            "from compiler.build_requirements_model import",
            repo_root / "project/src/compiler/build_requirements_model.py",
            "from network_methodology_sandbox.compiler.build_requirements_model import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/compiler/compile_graphs.py",
            "from compiler.compile_graphs import",
            repo_root / "project/src/compiler/compile_graphs.py",
            "from network_methodology_sandbox.compiler.compile_graphs import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/compiler/cross_field_inference.py",
            "from compiler.cross_field_inference import",
            repo_root / "project/src/compiler/cross_field_inference.py",
            "from network_methodology_sandbox.compiler.cross_field_inference import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/reports/generate_handoff_matrix.py",
            "from reports.generate_handoff_matrix import",
            repo_root / "project/src/reports/generate_handoff_matrix.py",
            "from network_methodology_sandbox.reports.generate_handoff_matrix import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/reports/generate_network_volume_summary.py",
            "from reports.generate_network_volume_summary import",
            repo_root / "project/src/reports/generate_network_volume_summary.py",
            "from network_methodology_sandbox.reports.generate_network_volume_summary import",
        ),
    ]

    for canonical_path, legacy_import, legacy_path, canonical_import in checks:
        canonical_content = canonical_path.read_text(encoding="utf-8")
        legacy_content = legacy_path.read_text(encoding="utf-8")

        assert legacy_import not in canonical_content
        assert canonical_import in legacy_content


def test_legacy_compiler_and_reports_wrappers_preserve_behavior(tmp_path: Path) -> None:
    assert (
        canonical_build_requirements_model.default_requirements_schema_path()
        == legacy_build_requirements_model.default_requirements_schema_path()
    )
    assert canonical_build_requirements_model.main is legacy_build_requirements_model.main

    assert canonical_compile_graphs._service_transport_zone("strict_isolation", True) == (
        legacy_compile_graphs._service_transport_zone("strict_isolation", True)
    )
    assert canonical_compile_graphs._service_source_zone("flat", "VIDEO") == (
        legacy_compile_graphs._service_source_zone("flat", "VIDEO")
    )
    assert canonical_compile_graphs.main is legacy_compile_graphs.main

    assert canonical_cross_field_inference.default_cross_field_rules_path() == (
        legacy_cross_field_inference.default_cross_field_rules_path()
    )

    assert canonical_generate_handoff_matrix.field_activation("yes") == (
        legacy_generate_handoff_matrix.field_activation("yes")
    )

    requirements = {
        "metadata": {
            "object_id": "OBJ-001",
            "object_name": "Object",
            "object_type": "site",
            "project_stage": "draft",
            "resolved_archetype": "small_remote_site",
        },
        "critical_services": {
            "telemetry_required": "yes",
            "control_required": "no",
            "video_required": "no",
            "iiot_required": "no",
            "local_archiving_required": "no",
        },
        "security_access": {
            "security_zone_model": "segmented",
            "remote_access_profile": "vpn",
        },
        "resilience": {
            "redundancy_target": "none",
            "degraded_mode_profile": "manual_fallback",
        },
        "time_sync": {
            "sync_protocol": "ntp",
            "timing_accuracy_class": "seconds",
        },
        "power_environment": {
            "power_source_model": "single_ups",
            "cabinet_constraint_class": "standard",
        },
        "operations": {
            "support_model": "local",
        },
    }

    assert canonical_generate_network_volume_summary.generate_network_volume_summary(requirements) == (
        legacy_generate_network_volume_summary.generate_network_volume_summary(requirements)
    )
    assert canonical_generate_network_volume_summary.main is legacy_generate_network_volume_summary.main
