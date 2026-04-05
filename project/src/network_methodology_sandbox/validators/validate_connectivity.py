from __future__ import annotations

from typing import Any

import networkx as nx
from network_methodology_sandbox.model_utils import is_yes


def validate_connectivity(graph: nx.Graph, requirements: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if graph.number_of_nodes() == 0:
        issues.append(
            {
                "validator": "connectivity",
                "severity": "error",
                "message": "Physical graph is empty.",
            }
        )
        return issues

    transport_nodes = [node for node, attrs in graph.nodes(data=True) if attrs.get("node_type") != "object"]
    transport_graph = graph.subgraph(transport_nodes).copy()

    if transport_graph.number_of_nodes() == 0:
        issues.append(
            {
                "validator": "connectivity",
                "severity": "error",
                "message": "Physical graph has no transport nodes after excluding object metadata nodes.",
            }
        )
        return issues

    if not nx.is_connected(transport_graph):
        issues.append(
            {
                "validator": "connectivity",
                "severity": "error",
                "message": "Physical graph is not connected.",
            }
        )

    if is_yes(requirements.get("external_transport", {}).get("wan_required")):
        wan_nodes = [node for node, attrs in graph.nodes(data=True) if attrs.get("role") == "wan_edge"]
        if not wan_nodes:
            issues.append(
                {
                    "validator": "connectivity",
                    "severity": "error",
                    "message": "WAN transport is required, but no wan_edge nodes exist in the physical graph.",
                }
            )
        process_node = next(
            (node for node, attrs in graph.nodes(data=True) if attrs.get("role") == "process_cluster"),
            None,
        )
        if process_node and wan_nodes and not any(nx.has_path(graph, process_node, wan_node) for wan_node in wan_nodes):
            issues.append(
                {
                    "validator": "connectivity",
                    "severity": "error",
                    "message": "Process cluster has no physical path to any WAN edge.",
                }
            )
    return issues
