from __future__ import annotations

import os
import re
from pathlib import Path

from network_methodology_sandbox.model_utils import resolve_project_root

OBJECT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")


class IntakeCommandError(ValueError):
    """Raised for user-facing intake command errors that should not show a traceback."""


class WorkspaceValidationError(IntakeCommandError):
    """Raised when a human-facing workspace command gets invalid workspace input."""


def intake_command_label() -> str:
    overridden = os.environ.get("NETWORK_METHODOLOGY_SANDBOX_INTAKE_COMMAND")
    if overridden:
        return overridden

    project_root = resolve_project_root()
    if project_root.name == "project" and (project_root.parent / "networkx").is_dir():
        return "project/intake"
    return "intake"


def validate_object_id(object_id: str) -> str:
    normalized = object_id.strip()
    if OBJECT_ID_PATTERN.fullmatch(normalized):
        return normalized
    raise WorkspaceValidationError(
        "Invalid object_id: "
        f"{object_id!r}. Use 2-64 chars: lowercase ASCII letters, digits, '_' or '-', "
        "starting with a letter. Example: nova_stantsiia"
    )


def resolve_object_id(
    workspace_path: Path,
    *,
    explicit_object_id: str | None = None,
) -> str:
    candidate = explicit_object_id if explicit_object_id is not None else workspace_path.name
    return validate_object_id(candidate)


def _init_command(workspace_path: Path) -> str:
    return f"{intake_command_label()} init {workspace_path}"


def _generate_command(workspace_path: Path) -> str:
    return f"{intake_command_label()} generate {workspace_path}"


def ensure_workspace_directory(
    workspace_path: Path,
    *,
    command_name: str,
    suggest_init: bool = False,
) -> Path:
    resolved = workspace_path.resolve()
    if not resolved.exists():
        message = f"Workspace not found: {resolved}"
        if suggest_init:
            message += f"\nTo create a new workspace: {_init_command(resolved)}"
        raise WorkspaceValidationError(message)
    if not resolved.is_dir():
        raise WorkspaceValidationError(
            f"{command_name} expects a workspace directory, got: {resolved}"
        )
    return resolved


def ensure_workspace_initialized(
    workspace_path: Path,
    *,
    command_name: str,
    suggest_init: bool = False,
) -> Path:
    resolved = ensure_workspace_directory(
        workspace_path,
        command_name=command_name,
        suggest_init=suggest_init,
    )
    role_assignments_path = resolved / "role_assignments.yaml"
    if not role_assignments_path.exists():
        message = f"Workspace is missing role_assignments.yaml: {role_assignments_path}"
        if suggest_init:
            message += f"\nTo create a new workspace: {_init_command(resolved)}"
        raise WorkspaceValidationError(message)
    if not role_assignments_path.is_file():
        raise WorkspaceValidationError(
            f"Expected role_assignments.yaml to be a file, got: {role_assignments_path}"
        )
    return resolved


def ensure_compile_inputs(workspace_path: Path) -> tuple[Path, list[Path]]:
    resolved = ensure_workspace_initialized(
        workspace_path,
        command_name="compile",
        suggest_init=True,
    )
    responses_dir = resolved / "intake" / "responses"
    xlsx_files = sorted(responses_dir.glob("*.xlsx"))
    if xlsx_files:
        return resolved, xlsx_files

    if not responses_dir.exists():
        raise WorkspaceValidationError(
            f"Workspace is missing generated intake response files: {responses_dir}\n"
            f"Run: {_generate_command(resolved)}"
        )
    raise WorkspaceValidationError(
        f"No .xlsx intake response files found in {responses_dir}\n"
        f"Run: {_generate_command(resolved)}"
    )


def ensure_init_target(workspace_path: Path) -> Path:
    resolved = workspace_path.resolve()
    if not resolved.exists():
        return resolved
    if not resolved.is_dir():
        raise WorkspaceValidationError(
            f"init expects a directory path, got: {resolved}"
        )

    role_assignments_path = resolved / "role_assignments.yaml"
    if role_assignments_path.exists():
        raise WorkspaceValidationError(
            "Workspace already initialized. "
            f"To regenerate workbooks: {_generate_command(resolved)}\n"
            "To re-initialize: delete role_assignments.yaml first."
        )

    if any(resolved.iterdir()):
        raise WorkspaceValidationError(
            f"init expects a new or empty workspace directory: {resolved}"
        )

    return resolved
