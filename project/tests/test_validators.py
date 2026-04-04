"""Tests for all validators."""

from __future__ import annotations

import networkx as nx

from validators.validate_connectivity import validate_connectivity
from validators.validate_segmentation import validate_segmentation
from validators.validate_resilience import validate_resilience
from validators.validate_power_ports import validate_power_ports
from validators.validate_semantic_consistency import validate_semantic_consistency
from validators.validate_time import validate_time
from validators.validate_stage_confidence import (
    derive_confidence_level,
    summarize_assumptions,
    validate_stage_confidence,
)


def _issues_by(issues, severity=None, validator=None):
    return [i for i in issues
            if (severity is None or i["severity"] == severity)
            and (validator is None or i["validator"] == validator)]


# ---------------------------------------------------------------------------
# Connectivity
# ---------------------------------------------------------------------------

class TestConnectivity:
    def test_empty_graph_is_error(self):
        g = nx.Graph()
        issues = validate_connectivity(g, {})
        assert len(_issues_by(issues, "error")) == 1
        assert "empty" in issues[0]["message"].lower()

    def test_connected_graph_no_issues(self):
        g = nx.Graph()
        g.add_edge("sw_a", "fw_a")
        g.add_edge("fw_a", "wan_a", role="wan_edge")
        for n in g.nodes:
            g.nodes[n]["node_type"] = "device"
        issues = validate_connectivity(g, {})
        assert len(_issues_by(issues, "error")) == 0

    def test_disconnected_graph_is_error(self):
        g = nx.Graph()
        g.add_node("sw_a", node_type="device")
        g.add_node("sw_b", node_type="device")
        issues = validate_connectivity(g, {})
        assert any("not connected" in i["message"] for i in issues)

    def test_wan_required_but_no_wan_node(self):
        g = nx.Graph()
        g.add_node("sw_a", node_type="device", role="access_switch")
        reqs = {"external_transport": {"wan_required": "yes"}}
        issues = validate_connectivity(g, reqs)
        assert any("wan_edge" in i["message"] for i in issues)

    def test_object_node_excluded_from_transport_check(self):
        g = nx.Graph()
        g.add_node("obj", node_type="object")
        g.add_node("sw_a", node_type="device")
        g.add_node("fw_a", node_type="device")
        g.add_edge("sw_a", "fw_a")
        issues = validate_connectivity(g, {})
        errors = _issues_by(issues, "error")
        # should not complain about disconnected obj node
        assert not any("not connected" in i["message"] for i in errors)


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

class TestSegmentation:
    def test_empty_graph_is_error(self):
        g = nx.DiGraph()
        issues = validate_segmentation(g, {})
        assert len(_issues_by(issues, "error")) == 1

    def test_dmz_required_but_missing(self):
        g = nx.DiGraph()
        g.add_node("OT")
        g.add_node("MGMT")
        reqs = {"security_access": {"security_zone_model": "dmz_centric"},
                "metadata": {"criticality_class": "low"}}
        issues = validate_segmentation(g, reqs)
        assert any("DMZ" in i["message"] for i in _issues_by(issues, "error"))

    def test_strict_isolation_no_ot_external(self):
        g = nx.DiGraph()
        g.add_node("OT")
        g.add_node("EXTERNAL")
        g.add_node("DMZ")
        g.add_edge("OT", "EXTERNAL")
        reqs = {"security_access": {"security_zone_model": "strict_isolation"},
                "metadata": {"criticality_class": "low"}}
        issues = validate_segmentation(g, reqs)
        assert any("forbids" in i["message"] for i in _issues_by(issues, "error"))

    def test_tbd_zone_with_video_no_error(self):
        """tbd zone model + video=yes should not error about missing VIDEO zone."""
        g = nx.DiGraph()
        g.add_node("OT", node_type="zone")
        reqs = {
            "security_access": {"security_zone_model": "tbd"},
            "critical_services": {"video_required": "yes", "iiot_required": "no"},
            "metadata": {"criticality_class": "low"},
        }
        issues = validate_segmentation(g, reqs)
        assert not any("VIDEO zone is missing" in i["message"] for i in issues)

    def test_tbd_zone_with_iiot_no_error(self):
        g = nx.DiGraph()
        g.add_node("OT", node_type="zone")
        reqs = {
            "security_access": {"security_zone_model": "tbd"},
            "critical_services": {"video_required": "no", "iiot_required": "yes"},
            "metadata": {"criticality_class": "low"},
        }
        issues = validate_segmentation(g, reqs)
        assert not any("IIOT zone is missing" in i["message"] for i in issues)

    def test_high_crit_shared_ok_warns(self):
        g = nx.DiGraph()
        g.add_node("OT")
        g.add_node("MGMT")
        reqs = {
            "security_access": {"security_zone_model": "segmented"},
            "external_transport": {"transport_separation_policy": "shared_ok"},
            "metadata": {"criticality_class": "high"},
        }
        issues = validate_segmentation(g, reqs)
        assert any("shared_ok" in i["message"] for i in _issues_by(issues, "warning"))

    def test_high_crit_flat_warns(self):
        g = nx.DiGraph()
        g.add_node("OT")
        reqs = {
            "security_access": {"security_zone_model": "flat"},
            "metadata": {"criticality_class": "high"},
        }
        issues = validate_segmentation(g, reqs)
        assert any("flat zone model" in i["message"] for i in _issues_by(issues, "warning"))


# ---------------------------------------------------------------------------
# Resilience
# ---------------------------------------------------------------------------

class TestResilience:
    def _minimal_graphs(self):
        pg = nx.Graph()
        pg.add_node("sw_a", node_type="device")
        pg.add_node("fw_a", node_type="device")
        pg.add_edge("sw_a", "fw_a")
        fg = nx.Graph()
        fg.add_node("power_primary", domain_type="power_domain")
        fg.add_node("carrier_a", domain_type="carrier_domain")
        return pg, fg

    def test_remote_ops_tbd_oob_warns(self):
        pg, fg = self._minimal_graphs()
        reqs = {
            "metadata": {"criticality_class": "low"},
            "resilience": {"redundancy_target": "none"},
            "object_profile": {"staffing_model": "remote_ops"},
            "security_access": {"oob_required": "tbd"},
            "external_transport": {"carrier_diversity_target": "single_path_allowed"},
        }
        issues = validate_resilience(pg, fg, reqs)
        assert any("confirmed OOB access" in i["message"] for i in _issues_by(issues, "warning"))

    def test_high_crit_single_path_warns(self):
        pg, fg = self._minimal_graphs()
        reqs = {
            "metadata": {"criticality_class": "high"},
            "resilience": {"redundancy_target": "uplink_backup", "degraded_mode_profile": "telemetry_survives",
                           "mttr_target_class": "four_hours"},
            "object_profile": {"staffing_model": "local_ops"},
            "security_access": {"oob_required": "yes"},
            "external_transport": {"carrier_diversity_target": "single_path_allowed"},
        }
        issues = validate_resilience(pg, fg, reqs)
        assert any("single_path" in i["message"] for i in _issues_by(issues, "warning"))

    def test_high_crit_best_effort_warns(self):
        pg, fg = self._minimal_graphs()
        reqs = {
            "metadata": {"criticality_class": "mission_critical"},
            "resilience": {"redundancy_target": "uplink_backup", "degraded_mode_profile": "best_effort",
                           "mttr_target_class": "four_hours"},
            "object_profile": {"staffing_model": "local_ops"},
            "security_access": {"oob_required": "yes"},
            "external_transport": {"carrier_diversity_target": "dual_carrier_required"},
        }
        issues = validate_resilience(pg, fg, reqs)
        assert any("best_effort" in i["message"] for i in _issues_by(issues, "warning"))

    def test_high_crit_same_day_mttr_warns(self):
        pg, fg = self._minimal_graphs()
        reqs = {
            "metadata": {"criticality_class": "high"},
            "resilience": {"redundancy_target": "uplink_backup", "degraded_mode_profile": "telemetry_survives",
                           "mttr_target_class": "same_day"},
            "object_profile": {"staffing_model": "local_ops"},
            "security_access": {"oob_required": "yes"},
            "external_transport": {"carrier_diversity_target": "dual_carrier_required"},
        }
        issues = validate_resilience(pg, fg, reqs)
        assert any("same_day" in i["message"] for i in _issues_by(issues, "warning"))

    def test_wan_no_with_dual_carrier_flags_missing_domains(self):
        pg = nx.Graph()
        pg.add_node("sw_a", node_type="device")
        fg = nx.Graph()
        fg.add_node("power_primary", domain_type="power_domain")
        # no carrier domains at all (wan_required=no)
        reqs = {
            "metadata": {"criticality_class": "medium"},
            "resilience": {"redundancy_target": "none"},
            "object_profile": {"staffing_model": "local_ops"},
            "security_access": {"oob_required": "yes"},
            "external_transport": {"carrier_diversity_target": "dual_carrier_required"},
        }
        issues = validate_resilience(pg, fg, reqs)
        assert any("carrier" in i["message"].lower() for i in _issues_by(issues, "error"))

    def test_no_spof_with_bridge_errors(self):
        pg = nx.Graph()
        pg.add_node("sw_a", node_type="device")
        pg.add_node("fw_a", node_type="device")
        pg.add_node("wan_a", node_type="device", role="wan_edge")
        pg.add_node("wan_b", node_type="device", role="wan_edge")
        pg.add_edge("sw_a", "fw_a")
        pg.add_edge("fw_a", "wan_a")
        pg.add_edge("fw_a", "wan_b")
        # sw_a -- fw_a is a bridge
        fg = nx.Graph()
        fg.add_node("carrier_a", domain_type="carrier_domain")
        fg.add_node("carrier_b", domain_type="carrier_domain")
        reqs = {
            "metadata": {"criticality_class": "high"},
            "resilience": {"redundancy_target": "no_spof", "degraded_mode_profile": "telemetry_survives",
                           "mttr_target_class": "four_hours", "common_cause_separation_required": "no"},
            "object_profile": {"staffing_model": "local_ops"},
            "security_access": {"oob_required": "yes"},
            "external_transport": {"carrier_diversity_target": "dual_carrier_required"},
        }
        issues = validate_resilience(pg, fg, reqs)
        assert any("bridges" in i["message"] for i in _issues_by(issues, "error"))

    def test_clean_medium_crit_no_issues(self):
        pg = nx.Graph()
        pg.add_node("sw_a", node_type="device", role="access_switch")
        pg.add_node("fw_a", node_type="device", role="firewall")
        pg.add_node("wan_a", node_type="device", role="wan_edge")
        pg.add_node("wan_b", node_type="device", role="wan_edge")
        pg.add_edge("sw_a", "fw_a")
        pg.add_edge("fw_a", "wan_a")
        pg.add_edge("sw_a", "wan_b")
        fg = nx.Graph()
        fg.add_node("power_primary", domain_type="power_domain")
        fg.add_node("carrier_a", domain_type="carrier_domain")
        fg.add_node("carrier_b", domain_type="carrier_domain")
        reqs = {
            "metadata": {"criticality_class": "medium"},
            "resilience": {"redundancy_target": "uplink_backup", "degraded_mode_profile": "telemetry_survives",
                           "mttr_target_class": "four_hours", "common_cause_separation_required": "no"},
            "object_profile": {"staffing_model": "local_ops"},
            "security_access": {"oob_required": "yes"},
            "external_transport": {"carrier_diversity_target": "dual_carrier_preferred"},
        }
        issues = validate_resilience(pg, fg, reqs)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Power/PoE
# ---------------------------------------------------------------------------

class TestPowerPorts:
    def test_poe_required_no_source_model(self):
        g = nx.Graph()
        reqs = {"power_environment": {"poe_required": "yes"}, "critical_services": {}}
        issues = validate_power_ports(reqs, g)
        assert any("power_source_model" in i["message"] for i in issues)

    def test_poe_required_budget_none(self):
        g = nx.Graph()
        reqs = {"power_environment": {"poe_required": "yes", "poe_budget_class": "none",
                                       "power_source_model": "ac_dc_hybrid"},
                "critical_services": {}}
        issues = validate_power_ports(reqs, g)
        assert any("poe_budget_class" in i["message"] for i in issues)

    def test_poe_tbd_budget_no_false_error(self):
        """poe_budget_class: tbd should not trigger 'budget is none' error."""
        g = nx.Graph()
        reqs = {"power_environment": {"poe_required": "yes", "poe_budget_class": "tbd",
                                       "power_source_model": "ac_dc_hybrid"},
                "critical_services": {}}
        issues = validate_power_ports(reqs, g)
        assert not any("poe_budget_class" in i["message"] for i in issues)

    def test_video_poe_no_capable_node(self):
        g = nx.Graph()
        g.add_node("sw_a", supports_poe=False)
        reqs = {"power_environment": {"poe_required": "yes", "poe_budget_class": "medium",
                                       "power_source_model": "ac_dc_hybrid"},
                "critical_services": {"video_required": "yes"}}
        issues = validate_power_ports(reqs, g)
        assert any("PoE-capable" in i["message"] for i in issues)


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

class TestTime:
    def test_timing_required_no_protocol(self):
        g = nx.Graph()
        reqs = {"time_sync": {"timing_required": "yes"}}
        issues = validate_time(reqs, g)
        assert any("sync_protocol" in i["message"] for i in issues)

    def test_ptp_without_capable_node(self):
        g = nx.Graph()
        g.add_node("sw_a", timing_capability="ntp")
        reqs = {"time_sync": {"timing_required": "yes", "sync_protocol": "ptp",
                               "timing_accuracy_class": "tens_of_us"}}
        issues = validate_time(reqs, g)
        assert any("PTP-capable" in i["message"] for i in issues)

    def test_ptp_with_capable_node_ok(self):
        g = nx.Graph()
        g.add_node("gm", timing_capability="ptp")
        reqs = {"time_sync": {"timing_required": "yes", "sync_protocol": "ptp",
                               "timing_accuracy_class": "tens_of_us"}}
        issues = validate_time(reqs, g)
        assert not any("PTP-capable" in i["message"] for i in issues)

    def test_timing_tbd_no_errors(self):
        g = nx.Graph()
        reqs = {"time_sync": {"timing_required": "tbd", "sync_protocol": "tbd",
                               "timing_accuracy_class": "tbd"}}
        issues = validate_time(reqs, g)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Stage confidence
# ---------------------------------------------------------------------------

class TestStageConfidence:
    def test_concept_mixed_is_indicative(self):
        reqs = {"metadata": {"project_stage": "concept"},
                "governance": {"evidence_maturity_class": "mixed"}}
        assert derive_confidence_level(reqs) == "indicative"

    def test_detailed_design_field_verified_is_binding(self):
        reqs = {"metadata": {"project_stage": "detailed_design"},
                "governance": {"evidence_maturity_class": "field_verified"}}
        assert derive_confidence_level(reqs) == "binding"

    def test_concept_assumption_heavy_warns(self):
        reqs = {"metadata": {"project_stage": "concept"},
                "governance": {"evidence_maturity_class": "assumption_heavy"}}
        issues = validate_stage_confidence(reqs, [])
        assert any("indicative" in i["message"] for i in _issues_by(issues, "warning"))

    def test_detailed_design_assumption_heavy_errors(self):
        reqs = {"metadata": {"project_stage": "detailed_design"},
                "governance": {"evidence_maturity_class": "assumption_heavy"}}
        issues = validate_stage_confidence(reqs, [])
        assert any("not acceptable" in i["message"] for i in _issues_by(issues, "error"))

    def test_many_tbd_fields_warns(self):
        reqs = {
            "metadata": {"project_stage": "concept"},
            "governance": {"evidence_maturity_class": "mixed"},
            "critical_services": {"control_required": "tbd", "video_required": "tbd",
                                   "iiot_required": "tbd", "local_archiving_required": "tbd"},
        }
        issues = validate_stage_confidence(reqs, [])
        assert any("tbd" in i["message"].lower() for i in _issues_by(issues, "warning"))

    def test_late_stage_tbd_errors(self):
        reqs = {
            "metadata": {"project_stage": "build_commission"},
            "governance": {"evidence_maturity_class": "mostly_confirmed"},
            "critical_services": {"control_required": "tbd"},
        }
        issues = validate_stage_confidence(reqs, [])
        assert any("tbd" in i["message"].lower() and "build_commission" in i["message"]
                    for i in _issues_by(issues, "error"))

    def test_high_assumptions_warns(self):
        assumptions = [{"field_id": f"field_{i}", "section": "test", "original_value": "__missing__",
                        "assumed_value": "val", "source": "archetype:test"} for i in range(8)]
        reqs = {"metadata": {"project_stage": "concept"},
                "governance": {"evidence_maturity_class": "mixed"}}
        issues = validate_stage_confidence(reqs, assumptions)
        assert any("archetype defaults" in i["message"] for i in _issues_by(issues, "warning"))

    def test_assumption_summary_distinguishes_inference_from_defaults(self):
        assumptions = [
            {"field_id": "a", "section": "s", "assumed_value": "x", "source": "archetype:test"},
            {"field_id": "b", "section": "s", "assumed_value": "y", "source": "inference:test_rule"},
        ]
        summary = summarize_assumptions(assumptions)
        assert summary == {
            "total": 2,
            "archetype_default_count": 1,
            "inference_count": 1,
            "other_count": 0,
        }

    def test_clean_no_stage_issues(self):
        reqs = {"metadata": {"project_stage": "detailed_design"},
                "governance": {"evidence_maturity_class": "field_verified"}}
        issues = validate_stage_confidence(reqs, [])
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Semantic consistency
# ---------------------------------------------------------------------------

class TestSemanticConsistency:
    def test_high_crit_no_redundancy_error(self):
        reqs = {
            "metadata": {"criticality_class": "high"},
            "resilience": {"redundancy_target": "none"},
        }
        issues = validate_semantic_consistency(reqs, [])
        assert any("redundancy_target='none'" in i["message"] for i in _issues_by(issues, "error"))

    def test_remote_ops_no_oob_warns(self):
        reqs = {
            "object_profile": {"staffing_model": "remote_ops"},
            "security_access": {"oob_required": "no"},
        }
        issues = validate_semantic_consistency(reqs, [])
        assert any("without OOB" in i["message"] for i in _issues_by(issues, "warning"))

    def test_tens_of_us_without_ptp_errors(self):
        reqs = {
            "time_sync": {"sync_protocol": "ntp", "timing_accuracy_class": "tens_of_us"},
        }
        issues = validate_semantic_consistency(reqs, [])
        assert any("requires PTP" in i["message"] for i in _issues_by(issues, "error"))

    def test_strict_zone_without_audit_logging_warns(self):
        reqs = {
            "security_access": {
                "security_zone_model": "strict_isolation",
                "audit_logging_required": "no",
            }
        }
        issues = validate_semantic_consistency(reqs, [])
        assert any("audit_logging_required='yes'" in i["message"] for i in _issues_by(issues, "warning"))
