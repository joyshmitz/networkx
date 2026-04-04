from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def resolve_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping in {path}, got {type(data).__name__}")
    return data


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def is_yes(value: Any) -> bool:
    return value is True or value == "yes"


def is_no(value: Any) -> bool:
    return value is False or value == "no"


def is_tbd(value: Any) -> bool:
    return value is None or value == "tbd"


def merge_missing_values_tracked(
    base: dict[str, Any],
    defaults: dict[str, Any],
    section: str,
    archetype_id: str,
) -> tuple[dict[str, Any], list[dict[str, str | Any]]]:
    merged = dict(base)
    assumed: list[dict[str, str | Any]] = []
    for key, default_value in defaults.items():
        present = key in merged
        current = merged.get(key)
        if not present or current in ("", None):
            merged[key] = default_value
            assumed.append({
                "kind": "archetype_default",
                "field_id": key,
                "section": section,
                "original_value": "__missing__" if not present else current,
                "assumed_value": default_value,
                "source": f"archetype:{archetype_id}",
            })
    return merged, assumed


def field_value_map(requirements: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for _, section in requirements.items():
        if not isinstance(section, dict):
            continue
        flat.update(section)
    return flat


def enabled_services(requirements: dict[str, Any]) -> list[str]:
    services = requirements.get("critical_services", {})
    service_map = {
        "telemetry_required": "telemetry",
        "control_required": "control",
        "video_required": "video",
        "iiot_required": "iiot_edge",
        "local_archiving_required": "local_archiving",
    }
    return [name for field_id, name in service_map.items() if is_yes(services.get(field_id))]
