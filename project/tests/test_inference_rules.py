from __future__ import annotations

from copy import deepcopy

import pytest
import yaml

from compiler.build_requirements_model import (
    apply_archetype_defaults,
    load_archetypes,
    normalize_boolish_enums,
    resolve_archetype_id,
)
from compiler.cross_field_inference import (
    InferenceRuleConflictError,
    InferenceRuleCatalogError,
    apply_cross_field_inferences,
    evaluate_condition,
    load_cross_field_rules,
)
from validators.validate_semantic_consistency import validate_semantic_consistency


class TestCrossFieldInference:
    def test_remote_ops_infers_oob_when_target_is_tbd(self):
        requirements = {
            "metadata": {"criticality_class": "low"},
            "object_profile": {"staffing_model": "remote_ops"},
            "security_access": {"oob_required": "tbd"},
        }

        normalized, assumptions = apply_cross_field_inferences(requirements)

        assert normalized["security_access"]["oob_required"] == "yes"
        assert len(assumptions) == 1
        assert assumptions[0]["field_id"] == "oob_required"
        assert assumptions[0]["kind"] == "inference"
        assert assumptions[0]["source"] == "inference:remote_ops_requires_oob"

    def test_explicit_value_is_never_overwritten(self):
        requirements = {
            "metadata": {"criticality_class": "low"},
            "object_profile": {"staffing_model": "remote_ops"},
            "security_access": {"oob_required": "no"},
        }

        normalized, assumptions = apply_cross_field_inferences(requirements)

        assert normalized["security_access"]["oob_required"] == "no"
        assert assumptions == []

    def test_concrete_archetype_default_blocks_inference(self):
        requirements = {
            "metadata": {"criticality_class": "low"},
            "object_profile": {"staffing_model": "remote_ops"},
            "security_access": {"oob_required": "yes"},
        }

        normalized, assumptions = apply_cross_field_inferences(requirements)

        assert normalized["security_access"]["oob_required"] == "yes"
        assert assumptions == []

    def test_bounded_fixpoint_supports_two_step_cascade(self):
        requirements = {
            "critical_services": {"control_required": "yes"},
            "time_sync": {
                "timing_required": "tbd",
                "timing_accuracy_class": "tens_of_us",
                "sync_protocol": "tbd",
            },
        }

        normalized, assumptions = apply_cross_field_inferences(requirements)

        assert normalized["time_sync"]["timing_required"] == "yes"
        assert normalized["time_sync"]["sync_protocol"] == "ptp"
        by_field = {item["field_id"]: item for item in assumptions}
        assert by_field["timing_required"]["pass_index"] == 1
        assert by_field["sync_protocol"]["pass_index"] == 2

    def test_conflicting_rules_fail_fast(self):
        requirements = {
            "metadata": {"criticality_class": "high"},
            "resilience": {"redundancy_target": "tbd"},
        }
        conflicting_rules = [
            {
                "rule_id": "a",
                "mode": "infer_if_tbd",
                "target_section": "resilience",
                "target_field": "redundancy_target",
                "inferred_value": "n_plus_1",
                "reason": "a",
                "when": {
                    "all_of": [
                        {"field": "metadata.criticality_class", "op": "eq", "value": "high"},
                    ]
                },
            },
            {
                "rule_id": "b",
                "mode": "infer_if_tbd",
                "target_section": "resilience",
                "target_field": "redundancy_target",
                "inferred_value": "none",
                "reason": "b",
                "when": {
                    "all_of": [
                        {"field": "metadata.criticality_class", "op": "eq", "value": "high"},
                    ]
                },
            },
        ]

        with pytest.raises(InferenceRuleConflictError, match="Conflicting cross-field inference rules"):
            apply_cross_field_inferences(requirements, rules=conflicting_rules)

    def test_rule_ids_must_be_unique(self, tmp_path):
        rules_path = tmp_path / "cross_field_rules.yaml"
        rules_path.write_text(
            yaml.safe_dump(
                {
                    "rules": [
                        {"rule_id": "dup", "mode": "infer_if_tbd"},
                        {"rule_id": "dup", "mode": "flag_if_conflicts"},
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        with pytest.raises(InferenceRuleCatalogError, match="duplicate rule_id"):
            load_cross_field_rules(rules_path)

    def test_archetype_defaults_and_inference_rules_remain_internally_consistent(self):
        archetypes = load_archetypes()
        rules = load_cross_field_rules()
        conflict_rules = [rule for rule in rules if rule.get("mode") == "flag_if_conflicts"]
        selector_seed_by_archetype = {
            "small_remote_site": {
                "metadata": {"criticality_class": "low"},
                "critical_services": {"iiot_required": "no", "video_required": "no"},
                "power_environment": {"poe_budget_class": "none"},
            },
            "video_heavy_site": {
                "critical_services": {"iiot_required": "no", "video_required": "yes"},
            },
            "resilient_telemetry_site": {
                "metadata": {"criticality_class": "high"},
                "critical_services": {"iiot_required": "no", "video_required": "no"},
                "power_environment": {"poe_budget_class": "none"},
            },
            "mixed_iiot_site": {
                "critical_services": {"iiot_required": "yes"},
            },
        }
        violations: list[str] = []

        for archetype_id, archetype in archetypes.items():
            questionnaire = deepcopy(selector_seed_by_archetype[archetype_id])
            assert resolve_archetype_id(questionnaire) == archetype_id

            normalized, _ = apply_archetype_defaults(questionnaire, archetype)
            normalized, _ = apply_cross_field_inferences(normalized)
            normalized = normalize_boolish_enums(normalized)

            for rule in conflict_rules:
                if evaluate_condition(rule["when"], normalized):
                    violations.append(f"{archetype_id}:{rule['rule_id']}")

        assert violations == []


class TestSemanticConsistency:
    def test_explicit_no_conflicts_with_remote_ops_even_if_staffing_is_assumed(self):
        requirements = {
            "object_profile": {"staffing_model": "remote_ops"},
            "security_access": {"oob_required": "no"},
        }
        assumptions = [
            {
                "section": "object_profile",
                "field_id": "staffing_model",
                "assumed_value": "remote_ops",
                "source": "archetype:small_remote_site",
            }
        ]

        issues = validate_semantic_consistency(requirements, assumptions)

        assert any(issue["validator"] == "semantic_consistency" for issue in issues)
        assert any("without OOB" in issue["message"] for issue in issues)

    def test_all_assumption_conflict_is_not_reported_as_human_contradiction(self):
        requirements = {
            "metadata": {"criticality_class": "high"},
            "resilience": {"redundancy_target": "none"},
        }
        assumptions = [
            {
                "section": "metadata",
                "field_id": "criticality_class",
                "assumed_value": "high",
                "source": "archetype:test",
            },
            {
                "section": "resilience",
                "field_id": "redundancy_target",
                "assumed_value": "none",
                "source": "inference:test_rule",
            },
        ]

        issues = validate_semantic_consistency(requirements, assumptions)

        assert issues == []
