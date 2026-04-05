from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PRODUCT_ROOT = Path(__file__).resolve().parents[1]
COPY_ITEMS = [
    "pyproject.toml",
    "README.md",
    "intake",
    "src",
    "tests",
    "examples",
    "specs",
]


def _copy_product_tree(target_root: Path) -> None:
    for relative in COPY_ITEMS:
        source = PRODUCT_ROOT / relative
        destination = target_root / relative
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            f"cwd={cwd}\n"
            f"cmd={' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed


def _prepare_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PROJECT_INTAKE_PYTHON", None)
    env.pop("VIRTUAL_ENV", None)
    return env


def rehearse(*, rehearsal_root: Path) -> Path:
    product_root = rehearsal_root / "sandbox"
    foreign_cwd = rehearsal_root / "foreign-cwd"

    product_root.mkdir(parents=True, exist_ok=True)
    foreign_cwd.mkdir(parents=True, exist_ok=True)
    _copy_product_tree(product_root)

    python_bin = product_root / ".venv" / "bin" / "python"
    pip_bin = product_root / ".venv" / "bin" / "pip"
    wrapper = product_root / "intake"

    _run([sys.executable, "-m", "venv", str(product_root / ".venv")], cwd=foreign_cwd)
    _run([str(pip_bin), "install", "-e", f"{product_root}[dev]"], cwd=foreign_cwd)

    env = _prepare_env()
    verify = _run([str(wrapper), "verify"], cwd=foreign_cwd, env=env)
    happy = _run([str(wrapper), "demo", "happy", "--date", "2026-04-02"], cwd=foreign_cwd, env=env)
    stress = _run([str(wrapper), "demo", "stress", "--date", "2026-04-02"], cwd=foreign_cwd, env=env)

    print(f"Rehearsal root: {product_root}")
    print(f"Editable install interpreter: {python_bin}")
    print(verify.stdout.strip())
    print(happy.stdout.strip().splitlines()[-1])
    print(stress.stdout.strip().splitlines()[-1])
    return product_root


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rehearse an extracted-root editable install in a fresh virtualenv.",
    )
    parser.add_argument(
        "--keep-root",
        type=Path,
        help="Optional directory to keep the copied rehearsal tree for inspection.",
    )
    args = parser.parse_args()

    if args.keep_root is not None:
        product_root = rehearse(rehearsal_root=args.keep_root)
        print(f"Kept rehearsal tree at {product_root}.")
        return

    with tempfile.TemporaryDirectory(prefix="network-methodology-sandbox.") as temp_dir:
        product_root = rehearse(rehearsal_root=Path(temp_dir))
        print(f"Temporary rehearsal completed successfully under {product_root}.")


if __name__ == "__main__":
    main()
