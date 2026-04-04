from __future__ import annotations

from typing import Any
import networkx as nx
from model_utils import is_yes


def validate_power_ports(requirements: dict[str, Any], physical_graph: nx.Graph) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    power_environment = requirements.get("power_environment", {})
    services = requirements.get("critical_services", {})

    if is_yes(power_environment.get("poe_required")) and not power_environment.get("power_source_model"):
        issues.append(
            {
                "validator": "power_ports",
                "severity": "error",
                "message": "PoE is required, but power_source_model is not defined.",
            }
        )

    if is_yes(services.get("video_required")) and is_yes(power_environment.get("poe_required")):
        if not any(attrs.get("supports_poe") for _, attrs in physical_graph.nodes(data=True)):
            issues.append(
                {
                    "validator": "power_ports",
                    "severity": "error",
                    "message": "Video/PoE workload exists, but no PoE-capable switching node is modeled.",
                }
            )
    return issues
