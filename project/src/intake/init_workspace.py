#!/usr/bin/env python3
"""Initialize a new intake workspace with a clean role_assignments.yaml scaffold."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from network_methodology_sandbox.intake.workspace_validation import (
    IntakeCommandError,
    ensure_init_target,
    resolve_object_id,
)
from network_methodology_sandbox.model_utils import resolve_project_root

TEMPLATE_PATH = Path("specs/questionnaire/role_assignments.template.yaml")
TEMPLATE_METADATA_KEYS = (
    "version",
    "questionnaire_id",
    "template_id",
    "description_uk",
    "rules",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


def _render_role_assignments(template: dict[str, Any], *, object_id: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in TEMPLATE_METADATA_KEYS:
        if key in template:
            payload[key] = template[key]
    payload["object_id"] = object_id
    payload["assignments"] = []
    return payload


def init_workspace(
    workspace_path: Path,
    *,
    project_root: Path | None = None,
    object_id: str | None = None,
) -> dict[str, Any]:
    project_root = project_root or resolve_project_root()
    resolved_workspace = ensure_init_target(workspace_path)
    resolved_object_id = resolve_object_id(
        resolved_workspace,
        explicit_object_id=object_id,
    )
    template = _load_yaml(project_root / TEMPLATE_PATH)
    resolved_workspace.mkdir(parents=True, exist_ok=True)
    payload = _render_role_assignments(template, object_id=resolved_object_id)

    output_path = resolved_workspace / "role_assignments.yaml"
    output_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    return {
        "workspace": str(resolved_workspace),
        "object_id": resolved_object_id,
        "role_assignments_path": str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize a new intake workspace.",
    )
    parser.add_argument("workspace_path", help="Workspace directory to initialize.")
    parser.add_argument(
        "--object-id",
        help="Optional machine-safe object_id. Defaults to the workspace directory name.",
    )
    args = parser.parse_args()

    try:
        result = init_workspace(
            Path(args.workspace_path),
            object_id=args.object_id,
        )
    except IntakeCommandError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    print("Workspace initialized. Edit role_assignments.yaml, then run:")
    print(f"project/intake generate {result['workspace']}")


if __name__ == "__main__":
    main()
