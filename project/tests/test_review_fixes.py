"""Tests for the 4 review findings from the Codex review."""

from __future__ import annotations

import pytest

from compiler.build_requirements_model import (
    build_requirements_model,
    detect_questionnaire_version,
    load_archetypes,
)
from model_utils import merge_missing_values_tracked


# ---------------------------------------------------------------------------
# P1: Malformed sections must hard-fail, not coerce to {}
# ---------------------------------------------------------------------------

class TestMalformedSectionRejection:
    def test_string_section_raises(self):
        questionnaire = {
            "object_profile": "oops",
            "governance": {},
            "version": "0.2.0",
        }
        with pytest.raises(ValueError, match="must be a mapping.*got str"):
            build_requirements_model(questionnaire)

    def test_list_section_raises(self):
        questionnaire = {
            "object_profile": {},
            "governance": {},
            "acceptance_criteria": ["fat", "sat"],
            "version": "0.2.0",
        }
        with pytest.raises(ValueError, match="must be a mapping.*got list"):
            build_requirements_model(questionnaire)

    def test_int_section_raises(self):
        questionnaire = {
            "object_profile": {},
            "governance": {},
            "resilience": 42,
            "version": "0.2.0",
        }
        with pytest.raises(ValueError, match="must be a mapping.*got int"):
            build_requirements_model(questionnaire)

    def test_none_section_is_allowed(self):
        """A missing section (None) is OK — it gets empty dict, not a crash."""
        questionnaire = {
            "object_profile": {},
            "governance": {},
            "version": "0.2.0",
            # all other sections are absent → None → {}
        }
        requirements, assumptions = build_requirements_model(questionnaire)
        assert "metadata" in requirements


# ---------------------------------------------------------------------------
# P1: TBD values must survive compilation, not be replaced by defaults
# ---------------------------------------------------------------------------

class TestTbdPreservation:
    def test_tbd_not_replaced_by_archetype_default(self):
        questionnaire = {
            "object_profile": {"staffing_model": "remote_ops", "growth_horizon_months": 36},
            "governance": {"evidence_maturity_class": "mixed", "waiver_policy_class": "controlled"},
            "critical_services": {
                "telemetry_required": "yes",
                "control_required": "tbd",
                "video_required": "no",
                "iiot_required": "no",
                "local_archiving_required": "tbd",
            },
            "metadata": {
                "object_id": "test",
                "object_name": "Test",
                "object_type": "substation",
                "project_stage": "concept",
                "criticality_class": "low",
            },
            "version": "0.2.0",
        }
        requirements, assumptions = build_requirements_model(questionnaire)
        assert requirements["critical_services"]["control_required"] == "tbd"
        assert requirements["critical_services"]["local_archiving_required"] == "tbd"
        # no assumptions for fields that had tbd
        assumed_fields = {a["field_id"] for a in assumptions}
        assert "control_required" not in assumed_fields
        assert "local_archiving_required" not in assumed_fields

    def test_truly_missing_field_gets_default(self):
        questionnaire = {
            "object_profile": {"staffing_model": "remote_ops", "growth_horizon_months": 36},
            "governance": {"evidence_maturity_class": "mixed", "waiver_policy_class": "controlled"},
            "critical_services": {
                "telemetry_required": "yes",
                # control_required entirely absent
                "video_required": "no",
                "iiot_required": "no",
                "local_archiving_required": "yes",
            },
            "metadata": {
                "object_id": "test",
                "object_name": "Test",
                "object_type": "substation",
                "project_stage": "concept",
                "criticality_class": "low",
            },
            "version": "0.2.0",
        }
        requirements, assumptions = build_requirements_model(questionnaire)
        # missing field should get archetype default
        assert requirements["critical_services"]["control_required"] != "tbd"
        assumed_fields = {a["field_id"] for a in assumptions}
        assert "control_required" in assumed_fields


# ---------------------------------------------------------------------------
# P2: Resilient telemetry site must not default local_archiving to yes
# ---------------------------------------------------------------------------

class TestResilientArchetypeConsistency:
    def test_local_archiving_default_is_no(self):
        archetypes = load_archetypes()
        resilient = archetypes["resilient_telemetry_site"]
        assert resilient["defaults"]["local_archiving_required"] == "no"

    def test_topology_seed_has_no_archive_node(self):
        archetypes = load_archetypes()
        resilient = archetypes["resilient_telemetry_site"]
        seed_roles = {n["role"] for n in resilient["topology_seed"]["nodes"]}
        assert "local_archive" not in seed_roles


# ---------------------------------------------------------------------------
# P3: Missing vs null distinction in assumption tracking
# ---------------------------------------------------------------------------

class TestMissingVsNullTracking:
    def test_absent_key_tracked_as_missing(self):
        base = {"existing_field": "value"}
        defaults = {"absent_field": "default_value"}
        merged, assumed = merge_missing_values_tracked(base, defaults, "test_section", "test_arch")
        assert len(assumed) == 1
        assert assumed[0]["original_value"] == "__missing__"
        assert assumed[0]["assumed_value"] == "default_value"

    def test_null_key_tracked_as_null(self):
        base = {"null_field": None}
        defaults = {"null_field": "default_value"}
        merged, assumed = merge_missing_values_tracked(base, defaults, "test_section", "test_arch")
        assert len(assumed) == 1
        assert assumed[0]["original_value"] is None
        assert assumed[0]["assumed_value"] == "default_value"

    def test_empty_string_tracked_as_empty(self):
        base = {"empty_field": ""}
        defaults = {"empty_field": "default_value"}
        merged, assumed = merge_missing_values_tracked(base, defaults, "test_section", "test_arch")
        assert len(assumed) == 1
        assert assumed[0]["original_value"] == ""

    def test_tbd_not_tracked_as_assumed(self):
        base = {"tbd_field": "tbd"}
        defaults = {"tbd_field": "default_value"}
        merged, assumed = merge_missing_values_tracked(base, defaults, "test_section", "test_arch")
        assert len(assumed) == 0
        assert merged["tbd_field"] == "tbd"

    def test_concrete_value_not_replaced(self):
        base = {"answered_field": "concrete_answer"}
        defaults = {"answered_field": "default_value"}
        merged, assumed = merge_missing_values_tracked(base, defaults, "test_section", "test_arch")
        assert len(assumed) == 0
        assert merged["answered_field"] == "concrete_answer"


# ---------------------------------------------------------------------------
# Codex review Wave 2: sparse v2 detection
# ---------------------------------------------------------------------------

class TestSparseV2Detection:
    def test_version_prefix_detects_v2(self):
        assert detect_questionnaire_version({"version": "0.2.0"}) == "v2"

    def test_version_prefix_0_2_1(self):
        assert detect_questionnaire_version({"version": "0.2.1"}) == "v2"

    def test_single_v2_marker_section(self):
        assert detect_questionnaire_version({"governance": {}}) == "v2"

    def test_sparse_questionnaire_compiles(self):
        """A sparse v2 questionnaire with only metadata + version should compile."""
        questionnaire = {
            "version": "0.2.0",
            "metadata": {
                "object_id": "sparse_test",
                "object_name": "Sparse",
                "object_type": "substation",
                "project_stage": "concept",
                "criticality_class": "low",
            },
        }
        requirements, assumptions = build_requirements_model(questionnaire)
        assert requirements["metadata"]["object_id"] == "sparse_test"
        # all other sections should be defaulted
        assert len(assumptions) > 0

    def test_v1_still_detected(self):
        assert detect_questionnaire_version({"functional_scope": {}}) == "v1"

    def test_unknown_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Unknown questionnaire"):
            detect_questionnaire_version({"random_key": "value"})


# ---------------------------------------------------------------------------
# Codex review: boolish flags in archetype resolution
# ---------------------------------------------------------------------------

class TestBoolishArchetypeResolution:
    def test_unquoted_yes_video_resolves_video_heavy(self):
        """PyYAML parses unquoted 'yes' as True. Archetype resolution must handle it."""
        questionnaire = {
            "object_profile": {},
            "governance": {},
            "version": "0.2.0",
            "critical_services": {
                "video_required": True,  # PyYAML bool
                "telemetry_required": True,
                "control_required": False,
                "iiot_required": False,
                "local_archiving_required": False,
            },
            "metadata": {
                "object_id": "bool_test",
                "object_name": "Bool Test",
                "object_type": "substation",
                "project_stage": "concept",
                "criticality_class": "low",
            },
        }
        requirements, _ = build_requirements_model(questionnaire)
        assert requirements["metadata"]["resolved_archetype"] == "video_heavy_site"

    def test_unquoted_yes_iiot_resolves_mixed(self):
        questionnaire = {
            "object_profile": {},
            "governance": {},
            "version": "0.2.0",
            "critical_services": {
                "iiot_required": True,
                "telemetry_required": True,
                "control_required": False,
                "video_required": False,
                "local_archiving_required": False,
            },
            "metadata": {
                "object_id": "bool_test",
                "object_name": "Bool Test",
                "object_type": "substation",
                "project_stage": "concept",
                "criticality_class": "low",
            },
        }
        requirements, _ = build_requirements_model(questionnaire)
        assert requirements["metadata"]["resolved_archetype"] == "mixed_iiot_site"


# ---------------------------------------------------------------------------
# Codex review: sparse v2 survives schema validation
# ---------------------------------------------------------------------------

class TestSparseV2SchemaValidation:
    def test_sparse_v2_passes_schema(self):
        from pathlib import Path
        questionnaire = {
            "version": "0.2.0",
            "metadata": {
                "object_id": "sparse_schema",
                "object_name": "Sparse Schema Test",
                "object_type": "substation",
                "project_stage": "concept",
                "criticality_class": "low",
            },
        }
        requirements, assumptions = build_requirements_model(questionnaire)
        schema_path = Path(__file__).resolve().parents[1] / "specs" / "requirements" / "object_requirements_v2.schema.yaml"
        from model_utils import load_yaml
        schema = load_yaml(schema_path)
        from compiler.build_requirements_model import validate_requirements_model
        # should not raise
        validate_requirements_model(requirements, schema=schema)
        assert len(assumptions) > 0
