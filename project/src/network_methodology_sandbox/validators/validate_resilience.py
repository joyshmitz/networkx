from __future__ import annotations

from typing import Any

import networkx as nx
from network_methodology_sandbox.model_utils import is_tbd, is_yes


def validate_resilience(
    physical_graph: nx.Graph, failure_graph: nx.Graph, requirements: dict[str, Any]
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if physical_graph.number_of_nodes() == 0:
        issues.append(
            {
                "validator": "resilience",
                "severity": "error",
                "message": "Physical graph is empty; resilience cannot be evaluated.",
            }
        )
        return issues

    redundancy_target = requirements.get("resilience", {}).get("redundancy_target")
    carrier_target = requirements.get("external_transport", {}).get("carrier_diversity_target")
    staffing_model = requirements.get("object_profile", {}).get("staffing_model")

    oob_required = requirements.get("security_access", {}).get("oob_required")
    # Cross-field inference normally upgrades remote_ops + tbd OOB into an
    # explicit inferred "yes" earlier in the build path. Keep this warning as
    # a fallback if that inference rule is disabled, removed, or bypassed.
    if staffing_model == "remote_ops" and is_tbd(oob_required):
        issues.append(
            {
                "validator": "resilience",
                "severity": "warning",
                "message": "Remote-ops staffing without confirmed OOB access creates weak recovery assumptions.",
            }
        )

    wan_nodes = [node for node, attrs in physical_graph.nodes(data=True) if attrs.get("role") == "wan_edge"]
    if redundancy_target in {"uplink_backup", "active_node_backup", "n_plus_1", "no_spof"} and len(wan_nodes) < 2:
        issues.append(
            {
                "validator": "resilience",
                "severity": "error",
                "message": f"Redundancy target '{redundancy_target}' requires at least two WAN edges.",
            }
        )

    if carrier_target in {"dual_carrier_required", "common_cause_separated"}:
        carrier_domains = [node for node, attrs in failure_graph.nodes(data=True) if attrs.get("domain_type") == "carrier_domain"]
        if len(carrier_domains) < 2:
            issues.append(
                {
                    "validator": "resilience",
                    "severity": "error",
                    "message": "Carrier diversity target requires at least two carrier domains.",
                }
            )

    if redundancy_target == "no_spof":
        bridges = list(nx.bridges(physical_graph))
        if bridges:
            issues.append(
                {
                    "validator": "resilience",
                    "severity": "error",
                    "message": f"No-SPOF target violated: physical graph still has bridges {bridges}.",
                }
            )

    if is_yes(requirements.get("resilience", {}).get("common_cause_separation_required")):
        required_domains = {"power_secondary", "cabinet_secondary"}
        if not required_domains.issubset(set(failure_graph.nodes)):
            issues.append(
                {
                    "validator": "resilience",
                    "severity": "warning",
                    "message": "Common-cause separation is required, but secondary power/cabinet domains are not modeled.",
                }
            )
    return issues
