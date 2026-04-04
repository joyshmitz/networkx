from __future__ import annotations

import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTAKE_WRAPPER = PROJECT_ROOT / "intake"


def _write_python_shim(path: Path, marker_path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "#!/bin/sh",
                f"printf '%s\\n' \"$0\" > {shlex.quote(str(marker_path))}",
                f"exec {shlex.quote(sys.executable)} \"$@\"",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class TestIntakeLauncher:
    def test_canonical_namespace_entrypoints_are_executable(self, tmp_path: Path) -> None:
        commands = [
            [sys.executable, "-m", "network_methodology_sandbox.intake.init_workspace", "--help"],
            [sys.executable, "-m", "network_methodology_sandbox.run_pipeline", "--help"],
        ]

        for command in commands:
            completed = subprocess.run(
                command,
                cwd=tmp_path,
                text=True,
                capture_output=True,
                check=False,
            )
            assert completed.returncode == 0, completed.stderr
            assert "usage:" in completed.stdout

    def test_wrapper_prefers_project_intake_python_override(self, tmp_path: Path) -> None:
        marker = tmp_path / "override-python.txt"
        shim = _write_python_shim(tmp_path / "override-python", marker)
        workspace = tmp_path / "override-workspace"

        env = os.environ.copy()
        env["PROJECT_INTAKE_PYTHON"] = str(shim)
        env.pop("VIRTUAL_ENV", None)

        completed = subprocess.run(
            [
                str(INTAKE_WRAPPER),
                "init",
                str(workspace),
                "--object-id",
                "override_workspace",
            ],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        assert marker.read_text(encoding="utf-8").strip() == str(shim)
        assert (workspace / "role_assignments.yaml").exists()

    def test_wrapper_prefers_active_virtualenv_over_repo_fallback(self, tmp_path: Path) -> None:
        fake_venv = tmp_path / "active-venv"
        fake_bin = fake_venv / "bin"
        fake_bin.mkdir(parents=True)

        marker = tmp_path / "active-venv-python.txt"
        shim = _write_python_shim(fake_bin / "python", marker)
        workspace = tmp_path / "venv-workspace"

        env = os.environ.copy()
        env.pop("PROJECT_INTAKE_PYTHON", None)
        env["VIRTUAL_ENV"] = str(fake_venv)

        completed = subprocess.run(
            [
                str(INTAKE_WRAPPER),
                "init",
                str(workspace),
                "--object-id",
                "venv_workspace",
            ],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        assert marker.read_text(encoding="utf-8").strip() == str(shim)
        assert (workspace / "role_assignments.yaml").exists()

    def test_wrapper_reports_non_executable_override_clearly(self, tmp_path: Path) -> None:
        env = os.environ.copy()
        env["PROJECT_INTAKE_PYTHON"] = str(tmp_path / "missing-python")
        env.pop("VIRTUAL_ENV", None)

        completed = subprocess.run(
            [
                str(INTAKE_WRAPPER),
                "verify",
            ],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert completed.returncode == 1
        assert completed.stdout == ""
        assert "PROJECT_INTAKE_PYTHON is not executable" in completed.stderr
