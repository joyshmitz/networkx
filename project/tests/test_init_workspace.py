from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from conftest import GOLDEN_DATE as FIXED_DATE
from network_methodology_sandbox.intake.compile_intake import compile_intake
from network_methodology_sandbox.intake.generate_intake_sheets import generate
from network_methodology_sandbox.intake.init_workspace import init_workspace
from network_methodology_sandbox.intake.workspace_validation import (
    WorkspaceValidationError,
    intake_command_label,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROLE_ASSIGNMENTS = (
    PROJECT_ROOT / "examples" / "sample_object_01" / "role_assignments.yaml"
)
INTAKE_COMMAND = intake_command_label()


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TestInitWorkspace:
    def test_happy_path_materializes_clean_scaffold(self, tmp_path):
        workspace = tmp_path / "nova_stantsiia"

        result = init_workspace(
            workspace,
            project_root=PROJECT_ROOT,
        )

        role_assignments = workspace / "role_assignments.yaml"
        assert role_assignments.exists()
        payload = _load_yaml(role_assignments)
        assert result["object_id"] == "nova_stantsiia"
        assert payload["object_id"] == "nova_stantsiia"
        assert payload["assignments"] == []
        assert payload["questionnaire_id"] == "core_questionnaire_v2"
        assert "rules" in payload
        assert "description_uk" in payload

    def test_already_initialized_workspace_fails_clearly(self, tmp_path):
        workspace = tmp_path / "already_init"
        init_workspace(workspace, project_root=PROJECT_ROOT)

        with pytest.raises(WorkspaceValidationError, match="already initialized"):
            init_workspace(workspace, project_root=PROJECT_ROOT)

    def test_empty_directory_is_allowed(self, tmp_path):
        workspace = tmp_path / "empty_dir"
        workspace.mkdir()

        result = init_workspace(workspace, project_root=PROJECT_ROOT)

        assert result["object_id"] == "empty_dir"
        assert (workspace / "role_assignments.yaml").exists()

    def test_invalid_object_id_is_rejected(self, tmp_path):
        workspace = tmp_path / "Нова станція"

        with pytest.raises(WorkspaceValidationError, match="Invalid object_id"):
            init_workspace(workspace, project_root=PROJECT_ROOT)

    def test_explicit_object_id_allows_non_ascii_workspace_path(self, tmp_path):
        workspace = tmp_path / "Нова_станція"

        result = init_workspace(
            workspace,
            project_root=PROJECT_ROOT,
            object_id="nova_stantsiia",
        )

        payload = _load_yaml(workspace / "role_assignments.yaml")
        assert result["object_id"] == "nova_stantsiia"
        assert payload["object_id"] == "nova_stantsiia"

    def test_nonempty_uninitialized_directory_is_rejected(self, tmp_path):
        workspace = tmp_path / "partial"
        workspace.mkdir()
        (workspace / "notes.txt").write_text("draft", encoding="utf-8")

        with pytest.raises(WorkspaceValidationError, match="new or empty workspace"):
            init_workspace(workspace, project_root=PROJECT_ROOT)

    def test_file_path_is_rejected(self, tmp_path):
        workspace_file = tmp_path / "not_a_directory"
        workspace_file.write_text("draft", encoding="utf-8")

        with pytest.raises(WorkspaceValidationError, match="init expects a directory path"):
            init_workspace(workspace_file, project_root=PROJECT_ROOT)


class TestWorkspaceCommandValidation:
    def test_generate_missing_workspace_suggests_init(self, tmp_path):
        with pytest.raises(
            WorkspaceValidationError,
            match=rf"{re.escape(INTAKE_COMMAND)} init",
        ):
            generate(
                tmp_path / "missing_workspace",
                project_root=PROJECT_ROOT,
                generated_on=FIXED_DATE,
            )

    def test_compile_missing_role_assignments_is_clear(self, tmp_path):
        workspace = tmp_path / "missing_role_assignments"
        workspace.mkdir()

        with pytest.raises(WorkspaceValidationError, match="missing role_assignments.yaml"):
            compile_intake(
                workspace,
                project_root=PROJECT_ROOT,
                compiled_on=FIXED_DATE,
            )

    def test_compile_without_generated_workbooks_is_clear(self, tmp_path):
        workspace = tmp_path / "no_workbooks"
        init_workspace(workspace, project_root=PROJECT_ROOT)

        sample_payload = _load_yaml(SAMPLE_ROLE_ASSIGNMENTS)
        payload = _load_yaml(workspace / "role_assignments.yaml")
        payload["assignments"] = sample_payload["assignments"]
        (workspace / "role_assignments.yaml").write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        with pytest.raises(
            WorkspaceValidationError,
            match=rf"Run: {re.escape(INTAKE_COMMAND)} generate",
        ):
            compile_intake(
                workspace,
                project_root=PROJECT_ROOT,
                compiled_on=FIXED_DATE,
            )

    def test_generate_requires_at_least_one_assignment(self, tmp_path):
        workspace = tmp_path / "empty_assignments"
        init_workspace(workspace, project_root=PROJECT_ROOT)

        with pytest.raises(WorkspaceValidationError, match="Add at least one assignment"):
            generate(
                workspace,
                project_root=PROJECT_ROOT,
                generated_on=FIXED_DATE,
            )

    def test_init_generate_compile_smoke_path(self, tmp_path):
        workspace = tmp_path / "smoke_workspace"
        init_workspace(
            workspace,
            project_root=PROJECT_ROOT,
            object_id="smoke_workspace",
        )

        sample_payload = _load_yaml(SAMPLE_ROLE_ASSIGNMENTS)
        payload = _load_yaml(workspace / "role_assignments.yaml")
        payload["assignments"] = sample_payload["assignments"]
        (workspace / "role_assignments.yaml").write_text(
            yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        generate(
            workspace,
            project_root=PROJECT_ROOT,
            generated_on=FIXED_DATE,
        )
        result = compile_intake(
            workspace,
            project_root=PROJECT_ROOT,
            compiled_on=FIXED_DATE,
        )

        assert result["object_id"] == "smoke_workspace"
        assert (workspace / "questionnaire.yaml").exists()
