from __future__ import annotations

from typing import Any

import networkx as nx


def validate_cross_graph(
    logical: nx.DiGraph,
    service: nx.DiGraph,
    interface: nx.DiGraph,
    requirements: dict[str, Any],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []

    logical_zones = {n for n, a in logical.nodes(data=True) if a.get("node_type") == "zone"}

    # Service graph zone nodes must exist in logical graph
    for node in service.nodes:
        if str(node).startswith("service::") or node == "LOCAL_ARCHIVE":
            continue
        if node not in logical_zones:
            issues.append({
                "validator": "cross_graph",
                "severity": "error",
                "message": (
                    f"Service graph references zone '{node}' "
                    f"that does not exist in the logical graph."
                ),
            })

    # Interface graph consumers should match enabled services
    from model_utils import enabled_services
    active_services = set(enabled_services(requirements))
    interface_consumers = {
        n for n in interface.nodes
        if n not in {"network_volume", "operations"}
    }
    for consumer in interface_consumers:
        if consumer not in active_services and consumer != "askoe":
            issues.append({
                "validator": "cross_graph",
                "severity": "warning",
                "message": (
                    f"Interface graph has consumer '{consumer}' "
                    f"that is not an enabled service."
                ),
            })

    return issues
