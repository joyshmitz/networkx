from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

import intake.compile_intake as legacy_compile_intake
import intake.evidence_status as legacy_evidence_status
import intake.generate_intake_sheets as legacy_generate_intake_sheets
import intake.init_workspace as legacy_init_workspace
import intake.preview_status as legacy_preview_status
import intake.review_packets as legacy_review_packets
import intake.workspace_manifest as legacy_workspace_manifest
import intake.workspace_snapshot as legacy_workspace_snapshot
import intake.workspace_validation as legacy_workspace_validation
from network_methodology_sandbox.intake import compile_intake as canonical_compile_intake
from network_methodology_sandbox.intake import evidence_status as canonical_evidence_status
from network_methodology_sandbox.intake import (
    generate_intake_sheets as canonical_generate_intake_sheets,
)
from network_methodology_sandbox.intake import init_workspace as canonical_init_workspace
from network_methodology_sandbox.intake import preview_status as canonical_preview_status
from network_methodology_sandbox.intake import review_packets as canonical_review_packets
from network_methodology_sandbox.intake import workspace_manifest as canonical_workspace_manifest
from network_methodology_sandbox.intake import workspace_snapshot as canonical_workspace_snapshot
from network_methodology_sandbox.intake import (
    workspace_validation as canonical_workspace_validation,
)

from conftest import GOLDEN_DATE, copy_workspace


def test_intake_modules_are_self_hosted_in_canonical_namespace() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    checks = [
        (
            repo_root / "project/src/network_methodology_sandbox/intake/compile_intake.py",
            "from intake.compile_intake import",
            repo_root / "project/src/intake/compile_intake.py",
            "from network_methodology_sandbox.intake.compile_intake import",
            True,
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/intake/evidence_status.py",
            "from intake.evidence_status import",
            repo_root / "project/src/intake/evidence_status.py",
            "from network_methodology_sandbox.intake.evidence_status import",
            True,
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/intake/generate_intake_sheets.py",
            "from intake.generate_intake_sheets import",
            repo_root / "project/src/intake/generate_intake_sheets.py",
            "from network_methodology_sandbox.intake.generate_intake_sheets import",
            False,
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/intake/init_workspace.py",
            "from intake.init_workspace import",
            repo_root / "project/src/intake/init_workspace.py",
            "from network_methodology_sandbox.intake.init_workspace import",
            True,
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/intake/preview_status.py",
            "from intake.preview_status import",
            repo_root / "project/src/intake/preview_status.py",
            "from network_methodology_sandbox.intake.preview_status import",
            True,
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/intake/review_packets.py",
            "from intake.review_packets import",
            repo_root / "project/src/intake/review_packets.py",
            "from network_methodology_sandbox.intake.review_packets import",
            True,
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/intake/workspace_manifest.py",
            "from intake.workspace_manifest import",
            repo_root / "project/src/intake/workspace_manifest.py",
            "from network_methodology_sandbox.intake.workspace_manifest import",
            False,
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/intake/workspace_snapshot.py",
            "from intake.workspace_snapshot import",
            repo_root / "project/src/intake/workspace_snapshot.py",
            "from network_methodology_sandbox.intake.workspace_snapshot import",
            True,
        ),
        (
            repo_root / "project/src/network_methodology_sandbox/intake/workspace_validation.py",
            "from intake.workspace_validation import",
            repo_root / "project/src/intake/workspace_validation.py",
            "from network_methodology_sandbox.intake.workspace_validation import",
            False,
        ),
    ]

    for canonical_path, legacy_import, legacy_path, canonical_import, removed_path_hack in checks:
        canonical_content = canonical_path.read_text(encoding="utf-8")
        legacy_content = legacy_path.read_text(encoding="utf-8")

        assert legacy_import not in canonical_content
        assert canonical_import in legacy_content
        if removed_path_hack:
            assert "sys.path.insert(" not in canonical_content


def test_legacy_intake_wrappers_preserve_practical_surface() -> None:
    assert canonical_compile_intake.compile_intake is legacy_compile_intake.compile_intake
    assert canonical_compile_intake._count_statuses is legacy_compile_intake._count_statuses
    assert canonical_compile_intake._build_questionnaire is legacy_compile_intake._build_questionnaire
    assert canonical_compile_intake.main is legacy_compile_intake.main

    assert canonical_generate_intake_sheets.generate is legacy_generate_intake_sheets.generate
    assert canonical_generate_intake_sheets._load_yaml is legacy_generate_intake_sheets._load_yaml
    assert canonical_generate_intake_sheets.main is legacy_generate_intake_sheets.main

    assert canonical_init_workspace.init_workspace is legacy_init_workspace.init_workspace
    assert canonical_init_workspace.main is legacy_init_workspace.main

    assert canonical_preview_status.preview_workspace is legacy_preview_status.preview_workspace
    assert canonical_preview_status.main is legacy_preview_status.main

    assert canonical_review_packets.review_workspace is legacy_review_packets.review_workspace
    assert canonical_review_packets.main is legacy_review_packets.main

    assert canonical_evidence_status.evidence_workspace is legacy_evidence_status.evidence_workspace
    assert canonical_evidence_status._load_evidence_policy is legacy_evidence_status._load_evidence_policy
    assert canonical_evidence_status.main is legacy_evidence_status.main

    assert canonical_workspace_manifest.refresh_workspace_manifest is (
        legacy_workspace_manifest.refresh_workspace_manifest
    )
    assert canonical_workspace_manifest._normalize_artifact is (
        legacy_workspace_manifest._normalize_artifact
    )

    assert canonical_workspace_snapshot.build_workspace_snapshot is (
        legacy_workspace_snapshot.build_workspace_snapshot
    )
    assert canonical_workspace_snapshot.SNAPSHOT_SCHEMA_VERSION == (
        legacy_workspace_snapshot.SNAPSHOT_SCHEMA_VERSION
    )

    assert canonical_workspace_validation.IntakeCommandError is (
        legacy_workspace_validation.IntakeCommandError
    )
    assert canonical_workspace_validation.WorkspaceValidationError is (
        legacy_workspace_validation.WorkspaceValidationError
    )
    assert canonical_workspace_validation.ensure_workspace_directory is (
        legacy_workspace_validation.ensure_workspace_directory
    )


def test_canonical_intake_cli_entrypoints_resolve_project_root_from_any_cwd(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    exemplar_workspace = repo_root / "project" / "examples" / "sample_object_01"

    generate_workspace = tmp_path / "generate_workspace"
    generate_workspace.mkdir()
    shutil.copy(
        exemplar_workspace / "role_assignments.yaml",
        generate_workspace / "role_assignments.yaml",
    )

    generate_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "network_methodology_sandbox.intake.generate_intake_sheets",
            str(generate_workspace),
            "--date",
            GOLDEN_DATE.isoformat(),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert generate_result.returncode == 0, generate_result.stderr
    assert (generate_workspace / "intake" / "responses" / "sample_arch.xlsx").exists()
    assert (generate_workspace / "intake" / "generated" / "sample_arch.guide.md").exists()

    compile_workspace = copy_workspace(tmp_path, exemplar_workspace)
    compile_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "network_methodology_sandbox.intake.compile_intake",
            str(compile_workspace),
            "--date",
            GOLDEN_DATE.isoformat(),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stderr
    assert (compile_workspace / "questionnaire.yaml").exists()
    assert (compile_workspace / "reports" / "intake_status.yaml").exists()
