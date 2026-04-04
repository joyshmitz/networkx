"""End-to-end pipeline tests using real sample questionnaires."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml
import pytest

from network_methodology_sandbox.model_utils import load_yaml
from network_methodology_sandbox.compiler.build_requirements_model import (
    build_requirements_model,
    validate_requirements_model,
)
from network_methodology_sandbox.compiler.compile_graphs import (
    compile_all_graphs,
    summarize_graph_bundle,
)
from network_methodology_sandbox.run_pipeline import run_validators, summarize_validation


SAMPLE_01 = Path(__file__).resolve().parents[1] / "examples" / "sample_object_01" / "questionnaire.yaml"
SAMPLE_02 = Path(__file__).resolve().parents[1] / "examples" / "sample_object_02" / "questionnaire.yaml"
SCHEMA = Path(__file__).resolve().parents[1] / "specs" / "requirements" / "object_requirements_v2.schema.yaml"


def _run_full_pipeline(questionnaire_path: Path) -> dict[str, Any]:
    questionnaire = load_yaml(questionnaire_path)
    requirements, assumptions = build_requirements_model(questionnaire)
    schema = load_yaml(SCHEMA)
    validate_requirements_model(requirements, schema=schema)
    role_assignments = None
    auto_role_assignments = questionnaire_path.parent / "role_assignments.yaml"
    if auto_role_assignments.exists():
        role_assignments = load_yaml(auto_role_assignments)
    bundle = compile_all_graphs(requirements)
    graph_summary = summarize_graph_bundle(bundle)
    issues = run_validators(
        requirements,
        graph_summary,
        bundle,
        assumptions,
        role_assignments=role_assignments,
    )
    return {
        "requirements": requirements,
        "assumptions": assumptions,
        "graph_summary": graph_summary,
        "issues": issues,
        "validation": summarize_validation(issues),
    }


# ---------------------------------------------------------------------------
# Sample 01: happy path
# ---------------------------------------------------------------------------

class TestSample01:
    @pytest.fixture(autouse=True)
    def _run(self):
        self.result = _run_full_pipeline(SAMPLE_01)

    def test_status_ok(self):
        assert self.result["validation"]["status"] == "ok"

    def test_no_errors(self):
        assert self.result["validation"]["error_count"] == 0

    def test_zero_assumptions(self):
        assert len(self.result["assumptions"]) == 0

    def test_resolved_archetype(self):
        assert self.result["requirements"]["metadata"]["resolved_archetype"] == "video_heavy_site"

    def test_physical_graph_nontrivial(self):
        assert self.result["graph_summary"]["physical"]["nodes"] >= 5
        assert self.result["graph_summary"]["physical"]["edges"] >= 4

    def test_all_graph_types_present(self):
        for key in ("physical", "logical", "service", "failure_domain", "interface"):
            assert self.result["graph_summary"][key]["nodes"] > 0

    def test_schema_valid(self):
        # should not raise
        schema = load_yaml(SCHEMA)
        validate_requirements_model(self.result["requirements"], schema=schema)


# ---------------------------------------------------------------------------
# Sample 02: stress test
# ---------------------------------------------------------------------------

class TestSample02:
    @pytest.fixture(autouse=True)
    def _run(self):
        self.result = _run_full_pipeline(SAMPLE_02)

    def test_status_failed(self):
        assert self.result["validation"]["status"] == "failed"

    def test_has_errors(self):
        assert self.result["validation"]["error_count"] >= 2

    def test_has_warnings(self):
        assert self.result["validation"]["warning_count"] >= 5

    def test_expected_assumptions_from_unanswered_fields(self):
        assumed_fields = {item["field_id"] for item in self.result["assumptions"]}
        assert assumed_fields == {
            "support_model",
            "maintenance_window_model",
            "asbuilt_package_required",
            "fat_required",
            "sat_required",
            "oob_required",
        }

    def test_remaining_tbd_fields_preserved(self):
        reqs = self.result["requirements"]
        assert reqs["critical_services"]["control_required"] == "tbd"
        assert reqs["security_access"]["oob_required"] == "yes"
        assert reqs["power_environment"]["poe_budget_class"] == "tbd"

    def test_unanswered_fields_are_filled_from_archetype_defaults(self):
        reqs = self.result["requirements"]
        assert reqs["operations"]["support_model"] == "hybrid"
        assert reqs["operations"]["maintenance_window_model"] == "planned_only"
        assert reqs["operations"]["asbuilt_package_required"] == "yes"
        assert reqs["acceptance_criteria"]["fat_required"] == "yes"
        assert reqs["acceptance_criteria"]["sat_required"] == "yes"

    def test_resolved_archetype_is_resilient(self):
        assert self.result["requirements"]["metadata"]["resolved_archetype"] == "resilient_telemetry_site"

    def test_inferred_oob_requirement_is_marked_as_inference(self):
        oob_assumption = next(
            item for item in self.result["assumptions"] if item["field_id"] == "oob_required"
        )
        assert oob_assumption["kind"] == "inference"
        assert oob_assumption["source"] == "inference:remote_ops_requires_oob"

    def test_criticality_redundancy_conflict_caught(self):
        errors = [i for i in self.result["issues"] if i["severity"] == "error"]
        assert any("redundancy_target" in i["message"] for i in errors)

    def test_time_accuracy_conflict_caught(self):
        errors = [i for i in self.result["issues"] if i["severity"] == "error"]
        assert any("PTP" in i["message"] for i in errors)

    def test_no_false_poe_budget_error(self):
        """poe_budget_class=tbd should NOT trigger 'budget is none' error."""
        errors = [i for i in self.result["issues"] if i["severity"] == "error"]
        assert not any("poe_budget_class is set to none" in i["message"] for i in errors)

    def test_stage_confidence_present(self):
        warnings = [i for i in self.result["issues"] if i["severity"] == "warning"
                     and i["validator"] == "stage_confidence"]
        assert len(warnings) >= 1

    def test_role_assignments_autoloaded(self):
        assert not any(
            issue["validator"] == "role_assignments"
            for issue in self.result["issues"]
        )

    def test_schema_valid_with_tbd(self):
        schema = load_yaml(SCHEMA)
        validate_requirements_model(self.result["requirements"], schema=schema)
