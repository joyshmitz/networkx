from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import yaml
from model_utils import enabled_services, is_yes, load_yaml, resolve_project_root


@dataclass
class GraphBundle:
    physical: nx.Graph
    logical: nx.DiGraph
    service: nx.DiGraph
    failure_domain: nx.Graph
    interface: nx.DiGraph


def default_archetypes_path() -> Path:
    return resolve_project_root() / "specs" / "archetypes" / "station_archetypes.yaml"


def default_equipment_catalog_path() -> Path:
    return resolve_project_root() / "specs" / "archetypes" / "equipment_catalog.yaml"


def load_archetype_catalog(path: Path | None = None) -> dict[str, Any]:
    payload = load_yaml(path or default_archetypes_path())
    return {item["archetype_id"]: item for item in payload.get("archetypes", [])}


def load_equipment_catalog(path: Path | None = None) -> dict[str, Any]:
    payload = load_yaml(path or default_equipment_catalog_path())
    return {item["equipment_id"]: item for item in payload.get("equipment", [])}


def equipment_node_attrs(equipment_catalog: dict[str, Any], equipment_id: str) -> dict[str, Any]:
    return {
        key: value
        for key, value in equipment_catalog[equipment_id].items()
        if key not in {"equipment_id", "role"}
    }


def resolved_archetype(requirements: dict[str, Any]) -> str:
    return requirements.get("metadata", {}).get("resolved_archetype", "small_remote_site")


def add_seed_nodes_and_edges(
    graph: nx.Graph | nx.DiGraph,
    requirements: dict[str, Any],
    archetype: dict[str, Any],
    equipment_catalog: dict[str, Any],
) -> None:
    seed = archetype.get("topology_seed", {})
    object_id = requirements.get("metadata", {}).get("object_id", "unknown_object")
    graph.add_node(object_id, role="object", node_type="object")

    wan_enabled = is_yes(requirements.get("external_transport", {}).get("wan_required"))
    archiving_enabled = is_yes(requirements.get("critical_services", {}).get("local_archiving_required"))
    skip_nodes: set[str] = set()

    for node in seed.get("nodes", []):
        attrs = dict(node)
        node_id = attrs.pop("node_id")
        if attrs.get("role") == "wan_edge" and not wan_enabled:
            skip_nodes.add(node_id)
            continue
        if attrs.get("role") == "local_archive" and not archiving_enabled:
            skip_nodes.add(node_id)
            continue
        equipment_id = attrs.get("equipment_id")
        if equipment_id and equipment_id in equipment_catalog:
            attrs.update(equipment_catalog[equipment_id])
        graph.add_node(node_id, **attrs)

    for edge in seed.get("edges", []):
        if edge["source"] in skip_nodes or edge["target"] in skip_nodes:
            continue
        graph.add_edge(edge["source"], edge["target"], **{k: v for k, v in edge.items() if k not in {"source", "target"}})


def ensure_node(
    graph: nx.Graph | nx.DiGraph,
    node_id: str,
    **attrs: Any,
) -> None:
    if graph.has_node(node_id):
        graph.nodes[node_id].update(attrs)
    else:
        graph.add_node(node_id, **attrs)


def first_node_by_role(graph: nx.Graph | nx.DiGraph, *roles: str) -> str | None:
    for node_id, attrs in graph.nodes(data=True):
        if attrs.get("role") in roles:
            return node_id
    return None


def should_have_secondary_path(requirements: dict[str, Any]) -> bool:
    redundancy_target = requirements.get("resilience", {}).get("redundancy_target")
    carrier_target = requirements.get("external_transport", {}).get("carrier_diversity_target")
    return redundancy_target in {"uplink_backup", "active_node_backup", "n_plus_1", "no_spof"} or carrier_target in {
        "dual_carrier_preferred",
        "dual_carrier_required",
        "common_cause_separated",
    }


def enrich_physical_graph(
    graph: nx.Graph, requirements: dict[str, Any], equipment_catalog: dict[str, Any]
) -> None:
    access_node = first_node_by_role(graph, "access_switch", "core_switch")
    firewall_node = first_node_by_role(graph, "firewall")

    if access_node is None:
        ensure_node(
            graph,
            "sw_access_a",
            role="access_switch",
            equipment_id="sw_access_generic",
            **equipment_node_attrs(equipment_catalog, "sw_access_generic"),
        )
        access_node = "sw_access_a"

    if firewall_node is None:
        ensure_node(
            graph,
            "fw_edge_a",
            role="firewall",
            equipment_id="fw_edge_generic",
            **equipment_node_attrs(equipment_catalog, "fw_edge_generic"),
        )
        firewall_node = "fw_edge_a"
        graph.add_edge(access_node, firewall_node, edge_role="site_uplink")

    if is_yes(requirements.get("critical_services", {}).get("video_required")):
        ensure_node(graph, "video_cluster", role="video_cluster", service="video")
        graph.add_edge("video_cluster", access_node, edge_role="video_access")

    archiving_required = is_yes(requirements.get("critical_services", {}).get("local_archiving_required"))
    has_archive_node = first_node_by_role(graph, "local_archive")
    if archiving_required and not has_archive_node:
        ensure_node(
            graph,
            "nvr_local",
            role="local_archive",
            equipment_id="nvr_generic",
            **equipment_node_attrs(equipment_catalog, "nvr_generic"),
        )
        graph.add_edge("nvr_local", access_node, edge_role="local_archive_access")
    elif not archiving_required and has_archive_node:
        graph.remove_node(has_archive_node)

    if is_yes(requirements.get("critical_services", {}).get("iiot_required")) and not first_node_by_role(
        graph, "iiot_edge"
    ):
        ensure_node(
            graph,
            "iiot_edge_local",
            role="iiot_edge",
            equipment_id="local_compute_generic",
            **equipment_node_attrs(equipment_catalog, "local_compute_generic"),
        )
        graph.add_edge("iiot_edge_local", access_node, edge_role="edge_access")

    wan_enabled = is_yes(requirements.get("external_transport", {}).get("wan_required"))
    if wan_enabled and should_have_secondary_path(requirements):
        ensure_node(graph, "wan_backup", role="wan_edge", carrier="carrier_b")
        if requirements.get("resilience", {}).get("redundancy_target") in {"active_node_backup", "n_plus_1", "no_spof"}:
            ensure_node(
                graph,
                "fw_edge_b",
                role="firewall",
                equipment_id="fw_edge_generic",
                **equipment_node_attrs(equipment_catalog, "fw_edge_generic"),
            )
            graph.add_edge(access_node, "fw_edge_b", edge_role="site_uplink_backup")
            graph.add_edge("fw_edge_b", "wan_backup", edge_role="external_uplink_backup")
        else:
            graph.add_edge(firewall_node, "wan_backup", edge_role="external_uplink_backup")

    if requirements.get("time_sync", {}).get("sync_protocol") == "ptp":
        ensure_node(
            graph,
            "gm_time",
            role="grandmaster",
            equipment_id="gm_time_generic",
            **equipment_node_attrs(equipment_catalog, "gm_time_generic"),
        )
        graph.add_edge("gm_time", access_node, edge_role="time_sync")


def compile_physical_graph(requirements: dict[str, Any]) -> nx.Graph:
    graph = nx.Graph(graph_type="physical")
    graph.graph["resolved_archetype"] = resolved_archetype(requirements)
    archetype = load_archetype_catalog()[resolved_archetype(requirements)]
    equipment_catalog = load_equipment_catalog()
    add_seed_nodes_and_edges(graph, requirements, archetype, equipment_catalog)
    enrich_physical_graph(graph, requirements, equipment_catalog)
    return graph


def compile_logical_graph(requirements: dict[str, Any]) -> nx.DiGraph:
    graph = nx.DiGraph(graph_type="logical")
    zone_model = requirements.get("security_access", {}).get("security_zone_model", "segmented")
    zones = ["OT"]

    if zone_model != "tbd":
        if zone_model in {"segmented", "dmz_centric", "strict_isolation"}:
            zones.append("MGMT")
        if zone_model in {"dmz_centric", "strict_isolation"}:
            zones.append("DMZ")
        if is_yes(requirements.get("critical_services", {}).get("video_required")):
            zones.append("VIDEO")
        if is_yes(requirements.get("critical_services", {}).get("iiot_required")):
            zones.append("IIOT")
        if is_yes(requirements.get("external_transport", {}).get("wan_required")):
            zones.append("EXTERNAL")

    for zone in zones:
        graph.add_node(zone, node_type="zone", zone_model=zone_model)

    if zone_model in {"tbd", "flat"}:
        # tbd: unresolved — only OT zone, no inter-zone edges
        # flat: no segmentation, just OT-EXTERNAL if present
        if zone_model == "flat" and "EXTERNAL" in graph:
            graph.add_edge("OT", "EXTERNAL", boundary="flat")
            graph.add_edge("EXTERNAL", "OT", boundary="flat")
    elif zone_model == "segmented":
        graph.add_edge("MGMT", "OT", boundary="managed")
        graph.add_edge("OT", "MGMT", boundary="managed")
        if "VIDEO" in graph:
            graph.add_edge("VIDEO", "OT", boundary="shared_transport")
        if "IIOT" in graph:
            graph.add_edge("IIOT", "OT", boundary="shared_transport")
        if "EXTERNAL" in graph:
            graph.add_edge("OT", "EXTERNAL", boundary="edge")
    elif zone_model in {"dmz_centric", "strict_isolation"}:
        graph.add_edge("MGMT", "DMZ", boundary="managed")
        graph.add_edge("DMZ", "OT", boundary="controlled")
        if "VIDEO" in graph:
            graph.add_edge("VIDEO", "DMZ", boundary="controlled")
        if "IIOT" in graph:
            graph.add_edge("IIOT", "DMZ", boundary="controlled")
        if "EXTERNAL" in graph:
            graph.add_edge("DMZ", "EXTERNAL", boundary="edge")

    return graph


def _service_source_zone(zone_model: str, preferred: str) -> str:
    if zone_model in {"flat", "tbd"}:
        return "OT"
    return preferred


def _service_transport_zone(zone_model: str, wan_required: bool) -> str | None:
    if not wan_required or zone_model == "tbd":
        return None
    if zone_model in {"dmz_centric", "strict_isolation"}:
        return "DMZ"
    return "EXTERNAL"


def compile_service_graph(requirements: dict[str, Any]) -> nx.DiGraph:
    graph = nx.DiGraph(graph_type="service")
    zone_model = requirements.get("security_access", {}).get("security_zone_model", "segmented")
    wan_required = is_yes(requirements.get("external_transport", {}).get("wan_required"))

    for service_name in enabled_services(requirements):
        service_node = f"service::{service_name}"
        graph.add_node(service_node, node_type="service", service=service_name)

        if service_name == "telemetry":
            graph.add_edge("OT", service_node, path_role="source")
            transport_zone = _service_transport_zone(zone_model, wan_required)
            if transport_zone:
                graph.add_edge(service_node, transport_zone, path_role="transport")
        elif service_name == "control":
            source = _service_source_zone(zone_model, "MGMT")
            graph.add_edge(source, service_node, path_role="source")
            graph.add_edge(service_node, "OT", path_role="control_target")
        elif service_name == "video":
            source = _service_source_zone(zone_model, "VIDEO")
            graph.add_edge(source, service_node, path_role="source")
            transport_zone = _service_transport_zone(zone_model, wan_required)
            if transport_zone:
                graph.add_edge(service_node, transport_zone, path_role="transport")
        elif service_name == "iiot_edge":
            source = _service_source_zone(zone_model, "IIOT")
            graph.add_edge(source, service_node, path_role="source")
            transport_zone = _service_transport_zone(zone_model, wan_required)
            if transport_zone:
                graph.add_edge(service_node, transport_zone, path_role="transport")
        elif service_name == "local_archiving":
            graph.add_edge("OT", service_node, path_role="source")
            graph.add_edge(service_node, "LOCAL_ARCHIVE", path_role="local_sink")

    return graph


def compile_failure_domain_graph(requirements: dict[str, Any]) -> nx.Graph:
    graph = nx.Graph(graph_type="failure_domain")
    graph.add_node("power_primary", domain_type="power_domain")
    graph.add_node("cabinet_primary", domain_type="cabinet_domain")

    wan_enabled = is_yes(requirements.get("external_transport", {}).get("wan_required"))
    if wan_enabled:
        graph.add_node("carrier_a", domain_type="carrier_domain")
    if wan_enabled and should_have_secondary_path(requirements):
        graph.add_node("carrier_b", domain_type="carrier_domain")
    if requirements.get("resilience", {}).get("redundancy_target") in {"active_node_backup", "n_plus_1", "no_spof"}:
        graph.add_node("power_secondary", domain_type="power_domain")
        graph.add_node("cabinet_secondary", domain_type="cabinet_domain")

    graph.add_edge("cabinet_primary", "power_primary")
    if graph.has_node("carrier_b"):
        graph.add_edge("carrier_a", "carrier_b", relation="diversity_target")
    return graph


def compile_interface_graph(requirements: dict[str, Any]) -> nx.DiGraph:
    graph = nx.DiGraph(graph_type="interface")
    graph.add_node("network_volume", node_type="producer")
    graph.add_node("operations", node_type="consumer")
    graph.add_edge("network_volume", "operations", reason="baseline")

    if is_yes(requirements.get("critical_services", {}).get("telemetry_required")):
        graph.add_node("telemetry", node_type="consumer")
        graph.add_edge("network_volume", "telemetry", reason="transport_baseline")
        graph.add_node("askoe", node_type="consumer")
        graph.add_edge("network_volume", "askoe", reason="transport_baseline")
    if is_yes(requirements.get("critical_services", {}).get("video_required")):
        graph.add_node("video", node_type="consumer")
        graph.add_edge("network_volume", "video", reason="video_transport")
    if is_yes(requirements.get("critical_services", {}).get("iiot_required")):
        graph.add_node("iiot_edge", node_type="consumer")
        graph.add_edge("network_volume", "iiot_edge", reason="iiot_integration")
    return graph


def compile_all_graphs(requirements: dict[str, Any]) -> GraphBundle:
    return GraphBundle(
        physical=compile_physical_graph(requirements),
        logical=compile_logical_graph(requirements),
        service=compile_service_graph(requirements),
        failure_domain=compile_failure_domain_graph(requirements),
        interface=compile_interface_graph(requirements),
    )


def summarize_graph_bundle(bundle: GraphBundle) -> dict[str, Any]:
    return {
        "resolved_archetype": bundle.physical.graph.get("resolved_archetype"),
        "physical": {
            "nodes": bundle.physical.number_of_nodes(),
            "edges": bundle.physical.number_of_edges(),
        },
        "logical": {
            "nodes": bundle.logical.number_of_nodes(),
            "edges": bundle.logical.number_of_edges(),
        },
        "service": {
            "nodes": bundle.service.number_of_nodes(),
            "edges": bundle.service.number_of_edges(),
        },
        "failure_domain": {
            "nodes": bundle.failure_domain.number_of_nodes(),
            "edges": bundle.failure_domain.number_of_edges(),
        },
        "interface": {
            "nodes": bundle.interface.number_of_nodes(),
            "edges": bundle.interface.number_of_edges(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile NetworkX graph bundle")
    parser.add_argument("requirements", type=Path)
    args = parser.parse_args()

    requirements = load_yaml(args.requirements)
    bundle = compile_all_graphs(requirements)
    summary = summarize_graph_bundle(bundle)
    print(yaml.safe_dump(summary, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    main()
