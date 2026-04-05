from __future__ import annotations

import subprocess
import sys
from pathlib import Path


LEGACY_MODULES = [
    "model_utils",
    "run_pipeline",
    "compiler",
    "compiler.build_requirements_model",
    "intake",
    "intake.compile_intake",
    "reports",
    "reports.generate_network_volume_summary",
    "validators",
    "validators.validate_time",
]


def test_legacy_modules_are_not_installed_in_clean_environment(tmp_path: Path) -> None:
    code = "\n".join(
        [
            "import importlib",
            "import sys",
            f"modules = {LEGACY_MODULES!r}",
            "for name in modules:",
            "    try:",
            "        importlib.import_module(name)",
            "    except ModuleNotFoundError:",
            "        continue",
            "    else:",
            "        print(name)",
            "        sys.exit(1)",
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

    assert completed.returncode == 0, (
        f"Legacy modules still importable:\nstdout={completed.stdout}\nstderr={completed.stderr}"
    )
    assert completed.stdout.strip() == "ok"
