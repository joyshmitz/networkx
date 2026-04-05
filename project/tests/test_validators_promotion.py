from __future__ import annotations

import validators.validate_annex_activation as legacy_validate_annex_activation
import validators.validate_connectivity as legacy_validate_connectivity
import validators.validate_cross_graph as legacy_validate_cross_graph
import validators.validate_power_ports as legacy_validate_power_ports
import validators.validate_resilience as legacy_validate_resilience
import validators.validate_role_assignments as legacy_validate_role_assignments
import validators.validate_segmentation as legacy_validate_segmentation
import validators.validate_semantic_consistency as legacy_validate_semantic_consistency
import validators.validate_stage_confidence as legacy_validate_stage_confidence
import validators.validate_time as legacy_validate_time
from pathlib import Path

from network_methodology_sandbox.validators import validate_annex_activation as canonical_validate_annex_activation
from network_methodology_sandbox.validators import validate_connectivity as canonical_validate_connectivity
from network_methodology_sandbox.validators import validate_cross_graph as canonical_validate_cross_graph
from network_methodology_sandbox.validators import validate_power_ports as canonical_validate_power_ports
from network_methodology_sandbox.validators import validate_resilience as canonical_validate_resilience
from network_methodology_sandbox.validators import validate_role_assignments as canonical_validate_role_assignments
from network_methodology_sandbox.validators import validate_segmentation as canonical_validate_segmentation
from network_methodology_sandbox.validators import (
    validate_semantic_consistency as canonical_validate_semantic_consistency,
)
from network_methodology_sandbox.validators import validate_stage_confidence as canonical_validate_stage_confidence
from network_methodology_sandbox.validators import validate_time as canonical_validate_time


def test_validator_modules_are_self_hosted_in_canonical_namespace() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    checks = [
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_annex_activation.py",
            "from validators.validate_annex_activation import",
            repo_root / "project/src/validators/validate_annex_activation.py",
            "from network_methodology_sandbox.validators.validate_annex_activation import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_connectivity.py",
            "from validators.validate_connectivity import",
            repo_root / "project/src/validators/validate_connectivity.py",
            "from network_methodology_sandbox.validators.validate_connectivity import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_cross_graph.py",
            "from validators.validate_cross_graph import",
            repo_root / "project/src/validators/validate_cross_graph.py",
            "from network_methodology_sandbox.validators.validate_cross_graph import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_power_ports.py",
            "from validators.validate_power_ports import",
            repo_root / "project/src/validators/validate_power_ports.py",
            "from network_methodology_sandbox.validators.validate_power_ports import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_resilience.py",
            "from validators.validate_resilience import",
            repo_root / "project/src/validators/validate_resilience.py",
            "from network_methodology_sandbox.validators.validate_resilience import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_role_assignments.py",
            "from validators.validate_role_assignments import",
            repo_root / "project/src/validators/validate_role_assignments.py",
            "from network_methodology_sandbox.validators.validate_role_assignments import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_segmentation.py",
            "from validators.validate_segmentation import",
            repo_root / "project/src/validators/validate_segmentation.py",
            "from network_methodology_sandbox.validators.validate_segmentation import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_semantic_consistency.py",
            "from validators.validate_semantic_consistency import",
            repo_root / "project/src/validators/validate_semantic_consistency.py",
            "from network_methodology_sandbox.validators.validate_semantic_consistency import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_stage_confidence.py",
            "from validators.validate_stage_confidence import",
            repo_root / "project/src/validators/validate_stage_confidence.py",
            "from network_methodology_sandbox.validators.validate_stage_confidence import",
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/validators/validate_time.py",
            "from validators.validate_time import",
            repo_root / "project/src/validators/validate_time.py",
            "from network_methodology_sandbox.validators.validate_time import",
        ),
    ]

    for canonical_path, legacy_import, legacy_path, canonical_import in checks:
        canonical_content = canonical_path.read_text(encoding="utf-8")
        legacy_content = legacy_path.read_text(encoding="utf-8")

        assert legacy_import not in canonical_content
        assert canonical_import in legacy_content


def test_legacy_validator_wrappers_preserve_practical_surface() -> None:
    assert canonical_validate_annex_activation.default_annex_dir is legacy_validate_annex_activation.default_annex_dir
    assert canonical_validate_annex_activation.annex_is_active is legacy_validate_annex_activation.annex_is_active
    assert canonical_validate_annex_activation._check_condition is legacy_validate_annex_activation._check_condition

    assert canonical_validate_connectivity.validate_connectivity is legacy_validate_connectivity.validate_connectivity
    assert canonical_validate_cross_graph.validate_cross_graph is legacy_validate_cross_graph.validate_cross_graph
    assert canonical_validate_power_ports.validate_power_ports is legacy_validate_power_ports.validate_power_ports
    assert canonical_validate_resilience.validate_resilience is legacy_validate_resilience.validate_resilience

    assert canonical_validate_role_assignments.default_fields_path is legacy_validate_role_assignments.default_fields_path
    assert canonical_validate_role_assignments.build_person_to_roles is legacy_validate_role_assignments.build_person_to_roles
    assert canonical_validate_role_assignments.build_role_to_persons is legacy_validate_role_assignments.build_role_to_persons
    assert canonical_validate_role_assignments.validate_role_assignments is legacy_validate_role_assignments.validate_role_assignments

    assert canonical_validate_segmentation.validate_segmentation is legacy_validate_segmentation.validate_segmentation
    assert canonical_validate_semantic_consistency.validate_semantic_consistency is (
        legacy_validate_semantic_consistency.validate_semantic_consistency
    )
    assert canonical_validate_stage_confidence.summarize_assumptions is (
        legacy_validate_stage_confidence.summarize_assumptions
    )
    assert canonical_validate_stage_confidence.derive_confidence_level is (
        legacy_validate_stage_confidence.derive_confidence_level
    )
    assert canonical_validate_stage_confidence.validate_stage_confidence is (
        legacy_validate_stage_confidence.validate_stage_confidence
    )
    assert canonical_validate_time.validate_time is legacy_validate_time.validate_time
