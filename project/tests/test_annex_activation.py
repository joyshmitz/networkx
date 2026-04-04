"""Tests for annex activation validator."""

from __future__ import annotations

from network_methodology_sandbox.validators.validate_annex_activation import (
    annex_is_active,
    validate_annex_activation,
)


def _reqs(**overrides):
    base = {
        "critical_services": {
            "telemetry_required": "yes",
            "control_required": "no",
            "video_required": "no",
            "iiot_required": "no",
            "local_archiving_required": "no",
        },
        "time_sync": {"timing_required": "no", "sync_protocol": "ntp", "timing_accuracy_class": "relaxed_ms"},
        "resilience": {"redundancy_target": "none", "degraded_mode_profile": "best_effort",
                       "mttr_target_class": "same_day", "common_cause_separation_required": "no"},
    }
    for key, val in overrides.items():
        if isinstance(val, dict) and key in base and isinstance(base[key], dict):
            base[key].update(val)
        else:
            base[key] = val
    return base


class TestAnnexIsActive:
    def test_simple_condition_met(self):
        spec = {"annex_id": "cctv", "applies_when": {"field_id": "video_required", "equals": "yes"}}
        assert annex_is_active(spec, {"video_required": "yes"}) is True

    def test_simple_condition_not_met(self):
        spec = {"annex_id": "cctv", "applies_when": {"field_id": "video_required", "equals": "yes"}}
        assert annex_is_active(spec, {"video_required": "no"}) is False

    def test_simple_condition_tbd(self):
        spec = {"annex_id": "cctv", "applies_when": {"field_id": "video_required", "equals": "yes"}}
        assert annex_is_active(spec, {"video_required": "tbd"}) is False

    def test_any_of_one_match(self):
        spec = {"annex_id": "ha", "applies_when": {
            "any_of": [
                {"field_id": "redundancy_target", "equals": "n_plus_1"},
                {"field_id": "redundancy_target", "equals": "no_spof"},
            ]
        }}
        assert annex_is_active(spec, {"redundancy_target": "n_plus_1"}) is True

    def test_any_of_no_match(self):
        spec = {"annex_id": "ha", "applies_when": {
            "any_of": [
                {"field_id": "redundancy_target", "equals": "n_plus_1"},
                {"field_id": "redundancy_target", "equals": "no_spof"},
            ]
        }}
        assert annex_is_active(spec, {"redundancy_target": "none"}) is False

    def test_missing_field(self):
        spec = {"annex_id": "cctv", "applies_when": {"field_id": "video_required", "equals": "yes"}}
        assert annex_is_active(spec, {}) is False


class TestValidateAnnexActivation:
    def test_no_services_no_warnings(self):
        issues = validate_annex_activation(_reqs())
        annex_issues = [i for i in issues if i["validator"] == "annex_activation"]
        assert len(annex_issues) == 0

    def test_video_triggers_cctv(self):
        issues = validate_annex_activation(_reqs(
            critical_services={"video_required": "yes", "telemetry_required": "yes",
                               "control_required": "no", "iiot_required": "no",
                               "local_archiving_required": "no"},
        ))
        annex_ids = [i["message"] for i in issues if i["validator"] == "annex_activation"]
        assert any("cctv" in m for m in annex_ids)

    def test_iiot_triggers_iiot_annex(self):
        issues = validate_annex_activation(_reqs(
            critical_services={"iiot_required": "yes", "telemetry_required": "yes",
                               "control_required": "no", "video_required": "no",
                               "local_archiving_required": "no"},
        ))
        annex_ids = [i["message"] for i in issues if i["validator"] == "annex_activation"]
        assert any("iiot" in m for m in annex_ids)

    def test_timing_triggers_time_annex(self):
        issues = validate_annex_activation(_reqs(
            time_sync={"timing_required": "yes", "sync_protocol": "ntp", "timing_accuracy_class": "relaxed_ms"},
        ))
        annex_ids = [i["message"] for i in issues if i["validator"] == "annex_activation"]
        assert any("time" in m for m in annex_ids)

    def test_high_redundancy_triggers_ha(self):
        issues = validate_annex_activation(_reqs(
            resilience={"redundancy_target": "n_plus_1", "degraded_mode_profile": "telemetry_survives",
                        "mttr_target_class": "four_hours", "common_cause_separation_required": "no"},
        ))
        annex_ids = [i["message"] for i in issues if i["validator"] == "annex_activation"]
        assert any("ha" in m for m in annex_ids)

    def test_tbd_does_not_trigger(self):
        issues = validate_annex_activation(_reqs(
            critical_services={"video_required": "tbd", "telemetry_required": "tbd",
                               "control_required": "tbd", "iiot_required": "tbd",
                               "local_archiving_required": "tbd"},
            time_sync={"timing_required": "tbd", "sync_protocol": "tbd", "timing_accuracy_class": "tbd"},
            resilience={"redundancy_target": "tbd", "degraded_mode_profile": "tbd",
                        "mttr_target_class": "tbd", "common_cause_separation_required": "tbd"},
        ))
        annex_issues = [i for i in issues if i["validator"] == "annex_activation"]
        assert len(annex_issues) == 0
