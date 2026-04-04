from __future__ import annotations

from pathlib import Path


TARGET_FILES = [
    "project/tests/conftest.py",
    "project/tests/test_annex_activation.py",
    "project/tests/test_compile_graphs.py",
    "project/tests/test_compile_intake.py",
    "project/tests/test_cross_graph.py",
    "project/tests/test_generate_intake.py",
    "project/tests/test_inference_rules.py",
    "project/tests/test_init_workspace.py",
    "project/tests/test_intake_branch_gates.py",
    "project/tests/test_intake_evidence.py",
    "project/tests/test_intake_happy_path_golden.py",
    "project/tests/test_intake_preview.py",
    "project/tests/test_intake_review.py",
    "project/tests/test_pipeline_e2e.py",
    "project/tests/test_review_fixes.py",
    "project/tests/test_role_assignments.py",
    "project/tests/test_run_pipeline_manifest.py",
    "project/tests/test_validators.py",
    "project/tests/test_workspace_manifest.py",
    "project/tests/test_workspace_snapshot.py",
]

LEGACY_IMPORT_PATTERNS = [
    "from compiler.",
    "from intake.",
    "from validators.",
    "from reports.",
    "from model_utils import",
    "from run_pipeline import",
    "import compiler",
    "import intake",
    "import validators",
    "import reports",
    "import model_utils",
    "import run_pipeline",
    "sys.path.insert(",
]


def test_functional_tests_use_canonical_namespace_imports() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []

    for relative_path in TARGET_FILES:
        content = (repo_root / relative_path).read_text(encoding="utf-8")
        for pattern in LEGACY_IMPORT_PATTERNS:
            if pattern in content:
                offenders.append(f"{relative_path}: {pattern}")

    assert offenders == []
