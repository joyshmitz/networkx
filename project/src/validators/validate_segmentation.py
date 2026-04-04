from __future__ import annotations

from typing import Any

import networkx as nx
from network_methodology_sandbox.model_utils import is_yes


def validate_segmentation(graph: nx.DiGraph, requirements: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if graph.number_of_nodes() == 0:
        issues.append(
            {
                "validator": "segmentation",
                "severity": "error",
                "message": "Logical graph has no zone model nodes.",
            }
        )
        return issues

    zone_model = requirements.get("security_access", {}).get("security_zone_model")
    services = requirements.get("critical_services", {})

    if zone_model in {"dmz_centric", "strict_isolation"} and "DMZ" not in graph:
        issues.append(
            {
                "validator": "segmentation",
                "severity": "error",
                "message": "Selected security_zone_model requires a DMZ node, but DMZ is missing.",
            }
        )

    if zone_model == "strict_isolation" and graph.has_edge("OT", "EXTERNAL"):
        issues.append(
            {
                "validator": "segmentation",
                "severity": "error",
                "message": "Strict isolation forbids direct OT -> EXTERNAL adjacency.",
            }
        )

    if is_yes(services.get("video_required")) and zone_model not in {"flat", "tbd"} and "VIDEO" not in graph:
        issues.append(
            {
                "validator": "segmentation",
                "severity": "error",
                "message": "Video service is required, but VIDEO zone is missing.",
            }
        )

    if is_yes(services.get("iiot_required")) and zone_model not in {"flat", "tbd"} and "IIOT" not in graph:
        issues.append(
            {
                "validator": "segmentation",
                "severity": "error",
                "message": "IIoT service is required, but IIOT zone is missing.",
            }
        )

    if is_yes(requirements.get("security_access", {}).get("oob_required")) and zone_model != "tbd" and "MGMT" not in graph:
        issues.append(
            {
                "validator": "segmentation",
                "severity": "warning",
                "message": "OOB/management is required, but logical graph has no MGMT zone.",
            }
        )

    return issues
