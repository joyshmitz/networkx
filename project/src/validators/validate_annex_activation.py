from __future__ import annotations

from pathlib import Path
from typing import Any

from model_utils import field_value_map, load_yaml, resolve_project_root


def default_annex_dir() -> Path:
    return resolve_project_root() / "specs" / "questionnaire"


def load_annex_specs(annex_dir: Path | None = None) -> list[dict[str, Any]]:
    directory = annex_dir or default_annex_dir()
    specs: list[dict[str, Any]] = []
    for path in sorted(directory.glob("annex_*.yaml")):
        specs.append(load_yaml(path))
    return specs


def _check_condition(condition: dict[str, str], flat_fields: dict[str, Any]) -> bool:
    field_id = condition.get("field_id", "")
    expected = condition.get("equals")
    return flat_fields.get(field_id) == expected


def annex_is_active(spec: dict[str, Any], flat_fields: dict[str, Any]) -> bool:
    applies_when = spec.get("applies_when", {})
    if "any_of" in applies_when:
        return any(_check_condition(c, flat_fields) for c in applies_when["any_of"])
    if "field_id" in applies_when:
        return _check_condition(applies_when, flat_fields)
    return False


def validate_annex_activation(
    requirements: dict[str, Any],
    annex_dir: Path | None = None,
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    flat_fields = field_value_map(requirements)
    specs = load_annex_specs(annex_dir)

    for spec in specs:
        annex_id = spec.get("annex_id", "unknown")
        if annex_is_active(spec, flat_fields):
            issues.append({
                "validator": "annex_activation",
                "severity": "warning",
                "message": (
                    f"Annex '{annex_id}' activation conditions are met, "
                    f"but annex data is not present in pipeline input."
                ),
            })

    return issues
