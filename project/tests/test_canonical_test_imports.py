from __future__ import annotations

from pathlib import Path


TARGET_FILES = [
    "tests/conftest.py",
    "tests/test_annex_activation.py",
    "tests/test_compile_graphs.py",
    "tests/test_compile_intake.py",
    "tests/test_cross_graph.py",
    "tests/test_generate_intake.py",
    "tests/test_inference_rules.py",
    "tests/test_init_workspace.py",
    "tests/test_intake_branch_gates.py",
    "tests/test_intake_evidence.py",
    "tests/test_intake_happy_path_golden.py",
    "tests/test_intake_preview.py",
    "tests/test_intake_review.py",
    "tests/test_pipeline_e2e.py",
    "tests/test_review_fixes.py",
    "tests/test_role_assignments.py",
    "tests/test_run_pipeline_manifest.py",
    "tests/test_validators.py",
    "tests/test_workspace_manifest.py",
    "tests/test_workspace_snapshot.py",
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
    product_root = Path(__file__).resolve().parents[1]
    offenders: list[str] = []

    for relative_path in TARGET_FILES:
        content = (product_root / relative_path).read_text(encoding="utf-8")
        for pattern in LEGACY_IMPORT_PATTERNS:
            if pattern in content:
                offenders.append(f"{relative_path}: {pattern}")

    assert offenders == []
