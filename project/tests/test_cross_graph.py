"""Tests for cross-graph consistency validator."""

from __future__ import annotations

import networkx as nx

from validators.validate_cross_graph import validate_cross_graph


def _issues_by(issues, severity=None):
    return [i for i in issues if severity is None or i["severity"] == severity]


class TestServiceZoneConsistency:
    def test_consistent_zones_no_errors(self):
        logical = nx.DiGraph()
        logical.add_node("OT", node_type="zone")
        logical.add_node("MGMT", node_type="zone")
        logical.add_node("EXTERNAL", node_type="zone")

        service = nx.DiGraph()
        service.add_node("service::telemetry", node_type="service")
        service.add_node("OT")
        service.add_node("EXTERNAL")
        service.add_edge("OT", "service::telemetry")
        service.add_edge("service::telemetry", "EXTERNAL")

        interface = nx.DiGraph()
        interface.add_node("network_volume")
        interface.add_node("operations")

        reqs = {"critical_services": {"telemetry_required": "yes", "control_required": "no",
                                       "video_required": "no", "iiot_required": "no",
                                       "local_archiving_required": "no"}}
        issues = validate_cross_graph(logical, service, interface, reqs)
        assert len(_issues_by(issues, "error")) == 0

    def test_phantom_zone_in_service_graph(self):
        logical = nx.DiGraph()
        logical.add_node("OT", node_type="zone")

        service = nx.DiGraph()
        service.add_node("service::telemetry", node_type="service")
        service.add_node("OT")
        service.add_node("DMZ")  # not in logical
        service.add_edge("OT", "service::telemetry")
        service.add_edge("service::telemetry", "DMZ")

        interface = nx.DiGraph()
        interface.add_node("network_volume")
        interface.add_node("operations")

        reqs = {"critical_services": {"telemetry_required": "yes", "control_required": "no",
                                       "video_required": "no", "iiot_required": "no",
                                       "local_archiving_required": "no"}}
        issues = validate_cross_graph(logical, service, interface, reqs)
        errors = _issues_by(issues, "error")
        assert len(errors) == 1
        assert "DMZ" in errors[0]["message"]

    def test_local_archive_not_flagged(self):
        """LOCAL_ARCHIVE is a service sink, not a zone — should not be flagged."""
        logical = nx.DiGraph()
        logical.add_node("OT", node_type="zone")

        service = nx.DiGraph()
        service.add_node("service::local_archiving", node_type="service")
        service.add_node("OT")
        service.add_node("LOCAL_ARCHIVE")
        service.add_edge("OT", "service::local_archiving")
        service.add_edge("service::local_archiving", "LOCAL_ARCHIVE")

        interface = nx.DiGraph()
        interface.add_node("network_volume")
        interface.add_node("operations")

        reqs = {"critical_services": {"telemetry_required": "no", "control_required": "no",
                                       "video_required": "no", "iiot_required": "no",
                                       "local_archiving_required": "yes"}}
        issues = validate_cross_graph(logical, service, interface, reqs)
        assert len(_issues_by(issues, "error")) == 0


class TestInterfaceConsumerConsistency:
    def test_unknown_consumer_warns(self):
        logical = nx.DiGraph()
        service = nx.DiGraph()

        interface = nx.DiGraph()
        interface.add_node("network_volume")
        interface.add_node("operations")
        interface.add_node("phantom_service")
        interface.add_edge("network_volume", "phantom_service")

        reqs = {"critical_services": {"telemetry_required": "no", "control_required": "no",
                                       "video_required": "no", "iiot_required": "no",
                                       "local_archiving_required": "no"}}
        issues = validate_cross_graph(logical, service, interface, reqs)
        warnings = _issues_by(issues, "warning")
        assert any("phantom_service" in w["message"] for w in warnings)

    def test_askoe_not_flagged(self):
        """askoe is a known consumer coupled to telemetry, not a separate service."""
        logical = nx.DiGraph()
        service = nx.DiGraph()

        interface = nx.DiGraph()
        interface.add_node("network_volume")
        interface.add_node("operations")
        interface.add_node("telemetry")
        interface.add_node("askoe")

        reqs = {"critical_services": {"telemetry_required": "yes", "control_required": "no",
                                       "video_required": "no", "iiot_required": "no",
                                       "local_archiving_required": "no"}}
        issues = validate_cross_graph(logical, service, interface, reqs)
        warnings = _issues_by(issues, "warning")
        assert not any("askoe" in w["message"] for w in warnings)
