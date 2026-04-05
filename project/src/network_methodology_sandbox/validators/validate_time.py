from __future__ import annotations

from typing import Any
import networkx as nx
from network_methodology_sandbox.model_utils import is_yes


def validate_time(requirements: dict[str, Any], physical_graph: nx.Graph) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    timing = requirements.get("time_sync", {})

    if is_yes(timing.get("timing_required")) and not timing.get("sync_protocol"):
        issues.append(
            {
                "validator": "time",
                "severity": "error",
                "message": "Timing service is required, but sync_protocol is missing.",
            }
        )

    if timing.get("sync_protocol") == "ptp":
        if not any(attrs.get("timing_capability") == "ptp" for _, attrs in physical_graph.nodes(data=True)):
            issues.append(
                {
                    "validator": "time",
                    "severity": "error",
                    "message": "PTP is selected, but no PTP-capable component exists in the physical graph.",
                }
            )
    return issues
