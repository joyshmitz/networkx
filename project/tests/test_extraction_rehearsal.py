from __future__ import annotations

import os
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INTAKE_WRAPPER = PROJECT_ROOT / "intake"
EXAMPLES_ROOT = PROJECT_ROOT / "examples"


def _copy_wrapper(target_root: Path) -> Path:
    wrapper_path = target_root / "intake"
    shutil.copy2(INTAKE_WRAPPER, wrapper_path)
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IXUSR)
    return wrapper_path


def _write_python_shim(path: Path, marker_path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _prepare_extracted_root(tmp_path: Path) -> tuple[Path, Path]:
    product_root = tmp_path / "sandbox"
    product_root.mkdir()
    wrapper_path = _copy_wrapper(product_root)
    return product_root, wrapper_path


class TestExtractionRehearsal:
    def test_extracted_layout_wrapper_prefers_product_local_venv(self, tmp_path: Path) -> None:
        product_root, wrapper_path = _prepare_extracted_root(tmp_path)
        marker = tmp_path / "product-local-python.txt"
        shim = _write_python_shim(product_root / ".venv" / "bin" / "python", marker)
        workspace = tmp_path / "rehearsal_workspace"

        env = os.environ.copy()
        env.pop("PROJECT_INTAKE_PYTHON", None)
        env.pop("VIRTUAL_ENV", None)

        completed = subprocess.run(
            [
                str(wrapper_path),
                "init",
                str(workspace),
                "--object-id",
                "rehearsal_workspace",
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

    def test_extracted_layout_wrapper_uses_product_root_for_verify_and_messages(
        self,
        tmp_path: Path,
    ) -> None:
        product_root, wrapper_path = _prepare_extracted_root(tmp_path)
        tests_dir = product_root / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_extracted_layout_probe.py").write_text(
            "def test_extracted_layout_probe():\n"
            "    assert True\n",
            encoding="utf-8",
        )

        env = os.environ.copy()
        env["PROJECT_INTAKE_PYTHON"] = sys.executable
        env.pop("VIRTUAL_ENV", None)

        verify = subprocess.run(
            [str(wrapper_path), "verify"],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert verify.returncode == 0, verify.stderr
        assert "1 passed" in verify.stdout

        workspace = tmp_path / "fresh_workspace"
        init = subprocess.run(
            [
                str(wrapper_path),
                "init",
                str(workspace),
                "--object-id",
                "fresh_workspace",
            ],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

        assert init.returncode == 0, init.stderr
        assert "intake generate" in init.stdout
        assert "project/intake generate" not in init.stdout

    def test_extracted_layout_wrapper_replays_examples_from_product_root(
        self,
        tmp_path: Path,
    ) -> None:
        product_root, wrapper_path = _prepare_extracted_root(tmp_path)
        shutil.copytree(EXAMPLES_ROOT / "sample_object_01", product_root / "examples" / "sample_object_01")
        shutil.copytree(EXAMPLES_ROOT / "sample_object_02", product_root / "examples" / "sample_object_02")

        env = os.environ.copy()
        env["PROJECT_INTAKE_PYTHON"] = sys.executable
        env.pop("VIRTUAL_ENV", None)

        happy = subprocess.run(
            [str(wrapper_path), "demo", "happy", "--date", "2026-04-02"],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert happy.returncode == 0, happy.stderr
        assert "Happy-path demo completed successfully" in happy.stdout

        stress = subprocess.run(
            [str(wrapper_path), "demo", "stress", "--date", "2026-04-02"],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert stress.returncode == 0, stress.stderr
        assert "Stress demo produced the expected domain validation failure" in stress.stdout
