from __future__ import annotations
from pathlib import Path
from typing import Any

from network_methodology_sandbox.model_utils import (
    field_value_map,
    is_no,
    is_tbd,
    is_yes,
    load_yaml,
    resolve_project_root,
)


def default_mapping_path() -> Path:
    return resolve_project_root() / "specs" / "mappings" / "implementation_mapping.yaml"


def field_activation(value: Any) -> str:
    if is_yes(value):
        return "required"
    if is_no(value):
        return "inactive"
    if is_tbd(value):
        return "unresolved"
    return "baseline"


def generate_handoff_matrix(requirements: dict[str, Any], mapping_path: Path | None = None) -> str:
    mapping = load_yaml(mapping_path or default_mapping_path())
    flat_fields = field_value_map(requirements)
    lines = [
        "# Handoff Matrix",
        "",
        "| Field | Value | Activation | Artifacts | Consumers |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in mapping.get("mappings", []):
        field_id = item["field_id"]
        value = flat_fields.get(field_id, "TBD")
        activation = field_activation(value)
        artifacts = ", ".join(item.get("downstream_artifacts", []))
        consumers = ", ".join(item.get("downstream_consumers", []))
        lines.append(f"| {field_id} | {value} | {activation} | {artifacts} | {consumers} |")
    return "\n".join(lines) + "\n"
