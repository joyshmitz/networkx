"""Tests for graph compilation logic."""

from __future__ import annotations

import networkx as nx

from compiler.compile_graphs import (
    compile_all_graphs,
    compile_failure_domain_graph,
    compile_logical_graph,
    compile_physical_graph,
    compile_service_graph,
    compile_interface_graph,
    summarize_graph_bundle,
)


def _base_requirements(**overrides) -> dict:
    """Minimal valid v2 requirements for graph compilation."""
    reqs = {
        "metadata": {
            "object_id": "test_obj",
            "object_name": "Test",
            "object_type": "substation",
            "project_stage": "concept",
            "criticality_class": "medium",
            "questionnaire_version": "0.2.0",
            "resolved_archetype": "small_remote_site",
        },
        "object_profile": {"staffing_model": "remote_ops", "growth_horizon_months": 36},
        "critical_services": {
            "telemetry_required": "yes",
            "control_required": "no",
            "video_required": "no",
            "iiot_required": "no",
            "local_archiving_required": "no",
        },
        "external_transport": {
            "wan_required": "yes",
            "carrier_diversity_target": "single_path_allowed",
            "transport_separation_policy": "logical_separation",
        },
        "security_access": {
            "security_zone_model": "segmented",
            "remote_access_profile": "controlled_vpn",
            "contractor_access_policy": "escorted_only",
            "audit_logging_required": "yes",
            "oob_required": "yes",
        },
        "time_sync": {
            "timing_required": "yes",
            "sync_protocol": "ntp",
            "timing_accuracy_class": "relaxed_ms",
        },
        "power_environment": {
            "power_source_model": "ac_dc_hybrid",
            "cabinet_constraint_class": "new_standard",
            "environmental_constraint_class": "industrial_indoor",
            "poe_required": "no",
            "poe_budget_class": "none",
        },
        "resilience": {
            "redundancy_target": "uplink_backup",
            "degraded_mode_profile": "telemetry_survives",
            "mttr_target_class": "four_hours",
            "common_cause_separation_required": "no",
        },
        "operations": {
            "support_model": "hybrid",
            "maintenance_window_model": "planned_only",
            "operations_handoff_required": "yes",
            "asbuilt_package_required": "yes",
        },
        "acceptance_criteria": {
            "fat_required": "yes",
            "sat_required": "yes",
            "acceptance_evidence_class": "test_records",
        },
        "governance": {
            "evidence_maturity_class": "mixed",
            "waiver_policy_class": "controlled",
        },
        "known_unknowns": {},
    }
    for key, val in overrides.items():
        if isinstance(val, dict) and key in reqs and isinstance(reqs[key], dict):
            reqs[key].update(val)
        else:
            reqs[key] = val
    return reqs


# ---------------------------------------------------------------------------
# Physical graph
# ---------------------------------------------------------------------------

class TestPhysicalGraph:
    def test_basic_topology_has_nodes_and_edges(self):
        g = compile_physical_graph(_base_requirements())
        assert g.number_of_nodes() >= 4
        assert g.number_of_edges() >= 3

    def test_video_adds_cluster_node(self):
        reqs = _base_requirements(
            critical_services={"video_required": "yes", "telemetry_required": "yes",
                               "control_required": "no", "iiot_required": "no",
                               "local_archiving_required": "no"},
        )
        g = compile_physical_graph(reqs)
        roles = {attrs.get("role") for _, attrs in g.nodes(data=True)}
        assert "video_cluster" in roles

    def test_video_with_archiving_adds_nvr(self):
        reqs = _base_requirements(
            critical_services={"video_required": "yes", "telemetry_required": "yes",
                               "control_required": "no", "iiot_required": "no",
                               "local_archiving_required": "yes"},
        )
        g = compile_physical_graph(reqs)
        roles = {attrs.get("role") for _, attrs in g.nodes(data=True)}
        assert "local_archive" in roles

    def test_iiot_adds_edge_node(self):
        reqs = _base_requirements(
            critical_services={"iiot_required": "yes", "telemetry_required": "yes",
                               "control_required": "no", "video_required": "no",
                               "local_archiving_required": "no"},
        )
        g = compile_physical_graph(reqs)
        roles = {attrs.get("role") for _, attrs in g.nodes(data=True)}
        assert "iiot_edge" in roles

    def test_redundancy_adds_secondary_path(self):
        reqs = _base_requirements(
            resilience={"redundancy_target": "n_plus_1", "degraded_mode_profile": "telemetry_survives",
                        "mttr_target_class": "four_hours", "common_cause_separation_required": "no"},
        )
        g = compile_physical_graph(reqs)
        wan_nodes = [n for n, a in g.nodes(data=True) if a.get("role") == "wan_edge"]
        assert len(wan_nodes) >= 2

    def test_ptp_adds_grandmaster(self):
        reqs = _base_requirements(
            time_sync={"timing_required": "yes", "sync_protocol": "ptp", "timing_accuracy_class": "tens_of_us"},
        )
        g = compile_physical_graph(reqs)
        roles = {attrs.get("role") for _, attrs in g.nodes(data=True)}
        assert "grandmaster" in roles

    def test_wan_no_skips_wan_seed_nodes(self):
        reqs = _base_requirements(
            external_transport={"wan_required": "no",
                                "carrier_diversity_target": "single_path_allowed",
                                "transport_separation_policy": "logical_separation"},
        )
        g = compile_physical_graph(reqs)
        roles = {attrs.get("role") for _, attrs in g.nodes(data=True)}
        assert "wan_edge" not in roles

    def test_wan_yes_has_wan_seed_nodes(self):
        g = compile_physical_graph(_base_requirements())
        roles = {attrs.get("role") for _, attrs in g.nodes(data=True)}
        assert "wan_edge" in roles

    def test_tbd_services_not_added(self):
        reqs = _base_requirements(
            critical_services={"video_required": "tbd", "telemetry_required": "yes",
                               "control_required": "tbd", "iiot_required": "tbd",
                               "local_archiving_required": "tbd"},
        )
        g = compile_physical_graph(reqs)
        roles = {attrs.get("role") for _, attrs in g.nodes(data=True)}
        assert "video_cluster" not in roles
        assert "iiot_edge" not in roles


# ---------------------------------------------------------------------------
# Logical graph
# ---------------------------------------------------------------------------

class TestLogicalGraph:
    def test_segmented_has_mgmt(self):
        g = compile_logical_graph(_base_requirements())
        assert "MGMT" in g
        assert "OT" in g

    def test_dmz_centric_has_dmz(self):
        reqs = _base_requirements(security_access={"security_zone_model": "dmz_centric",
                                                    "remote_access_profile": "controlled_vpn",
                                                    "contractor_access_policy": "escorted_only",
                                                    "audit_logging_required": "yes",
                                                    "oob_required": "yes"})
        g = compile_logical_graph(reqs)
        assert "DMZ" in g

    def test_flat_has_no_mgmt(self):
        reqs = _base_requirements(security_access={"security_zone_model": "flat",
                                                    "remote_access_profile": "none",
                                                    "contractor_access_policy": "forbidden",
                                                    "audit_logging_required": "no",
                                                    "oob_required": "no"})
        g = compile_logical_graph(reqs)
        assert "MGMT" not in g

    def test_video_adds_video_zone(self):
        reqs = _base_requirements(
            critical_services={"video_required": "yes", "telemetry_required": "yes",
                               "control_required": "no", "iiot_required": "no",
                               "local_archiving_required": "no"},
        )
        g = compile_logical_graph(reqs)
        assert "VIDEO" in g

    def test_wan_adds_external_zone(self):
        g = compile_logical_graph(_base_requirements())
        assert "EXTERNAL" in g

    def test_tbd_zone_model_only_ot(self):
        reqs = _base_requirements(security_access={"security_zone_model": "tbd",
                                                    "remote_access_profile": "tbd",
                                                    "contractor_access_policy": "tbd",
                                                    "audit_logging_required": "tbd",
                                                    "oob_required": "tbd"})
        g = compile_logical_graph(reqs)
        assert "OT" in g
        assert "MGMT" not in g
        assert "DMZ" not in g
        assert g.number_of_edges() == 0

    def test_no_wan_no_external(self):
        reqs = _base_requirements(
            external_transport={"wan_required": "no",
                                "carrier_diversity_target": "single_path_allowed",
                                "transport_separation_policy": "logical_separation"},
        )
        g = compile_logical_graph(reqs)
        assert "EXTERNAL" not in g


# ---------------------------------------------------------------------------
# Service graph
# ---------------------------------------------------------------------------

class TestServiceGraph:
    def test_telemetry_service_present(self):
        g = compile_service_graph(_base_requirements())
        assert "service::telemetry" in g

    def test_disabled_services_absent(self):
        g = compile_service_graph(_base_requirements())
        assert "service::video" not in g
        assert "service::iiot_edge" not in g

    def test_tbd_zone_model_routes_through_ot(self):
        reqs = _base_requirements(security_access={"security_zone_model": "tbd",
                                                    "remote_access_profile": "tbd",
                                                    "contractor_access_policy": "tbd",
                                                    "audit_logging_required": "tbd",
                                                    "oob_required": "tbd"})
        g = compile_service_graph(reqs)
        # telemetry service should route from OT, not from MGMT or DMZ
        if "service::telemetry" in g:
            assert g.has_edge("OT", "service::telemetry")

    def test_no_wan_no_transport_edges(self):
        reqs = _base_requirements(
            external_transport={"wan_required": "no",
                                "carrier_diversity_target": "single_path_allowed",
                                "transport_separation_policy": "logical_separation"},
        )
        g = compile_service_graph(reqs)
        # no transport edges to EXTERNAL or DMZ
        for u, v, data in g.edges(data=True):
            assert data.get("path_role") != "transport" or v not in {"EXTERNAL", "DMZ"}

    def test_tbd_services_not_compiled(self):
        reqs = _base_requirements(
            critical_services={"telemetry_required": "tbd", "control_required": "tbd",
                               "video_required": "tbd", "iiot_required": "tbd",
                               "local_archiving_required": "tbd"},
        )
        g = compile_service_graph(reqs)
        service_nodes = [n for n in g.nodes if str(n).startswith("service::")]
        assert len(service_nodes) == 0


# ---------------------------------------------------------------------------
# Failure domain graph
# ---------------------------------------------------------------------------

class TestFailureDomainGraph:
    def test_baseline_has_primary_domains(self):
        g = compile_failure_domain_graph(_base_requirements())
        assert "power_primary" in g
        assert "cabinet_primary" in g
        assert "carrier_a" in g

    def test_redundancy_adds_secondary_carrier(self):
        reqs = _base_requirements(
            resilience={"redundancy_target": "n_plus_1", "degraded_mode_profile": "telemetry_survives",
                        "mttr_target_class": "four_hours", "common_cause_separation_required": "no"},
        )
        g = compile_failure_domain_graph(reqs)
        assert "carrier_b" in g

    def test_wan_no_skips_carrier_domains(self):
        reqs = _base_requirements(
            external_transport={"wan_required": "no",
                                "carrier_diversity_target": "dual_carrier_required",
                                "transport_separation_policy": "logical_separation"},
        )
        g = compile_failure_domain_graph(reqs)
        carrier_nodes = [n for n, a in g.nodes(data=True) if a.get("domain_type") == "carrier_domain"]
        assert len(carrier_nodes) == 0

    def test_no_spof_adds_secondary_power_cabinet(self):
        reqs = _base_requirements(
            resilience={"redundancy_target": "no_spof", "degraded_mode_profile": "telemetry_survives",
                        "mttr_target_class": "four_hours", "common_cause_separation_required": "yes"},
        )
        g = compile_failure_domain_graph(reqs)
        assert "power_secondary" in g
        assert "cabinet_secondary" in g


# ---------------------------------------------------------------------------
# Interface graph
# ---------------------------------------------------------------------------

class TestInterfaceGraph:
    def test_baseline_has_operations(self):
        g = compile_interface_graph(_base_requirements())
        assert "operations" in g
        assert g.has_edge("network_volume", "operations")

    def test_telemetry_adds_consumers(self):
        g = compile_interface_graph(_base_requirements())
        assert "telemetry" in g
        assert "askoe" in g


# ---------------------------------------------------------------------------
# Bundle summary
# ---------------------------------------------------------------------------

class TestGraphBundle:
    def test_compile_all_returns_bundle(self):
        bundle = compile_all_graphs(_base_requirements())
        assert isinstance(bundle.physical, nx.Graph)
        assert isinstance(bundle.logical, nx.DiGraph)
        assert isinstance(bundle.service, nx.DiGraph)

    def test_summary_has_all_graphs(self):
        bundle = compile_all_graphs(_base_requirements())
        summary = summarize_graph_bundle(bundle)
        for key in ("physical", "logical", "service", "failure_domain", "interface"):
            assert key in summary
            assert "nodes" in summary[key]
            assert "edges" in summary[key]
