from __future__ import annotations

from typing import Any

from network_methodology_sandbox.compiler.cross_field_inference import (
    collect_condition_field_refs,
    evaluate_condition,
    field_ref,
    get_field_value,
    load_cross_field_rules,
)
from network_methodology_sandbox.model_utils import is_tbd


def validate_semantic_consistency(
    requirements: dict[str, Any],
    assumptions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    assumed_fields = {
        field_ref(str(item["section"]), str(item["field_id"]))
        for item in assumptions
        if item.get("section") and item.get("field_id")
    }
    issues: list[dict[str, Any]] = []

    for rule in load_cross_field_rules():
        if rule.get("mode") != "flag_if_conflicts":
            continue

        if not evaluate_condition(rule["when"], requirements):
            continue

        implicated_fields = set(rule.get("source_fields", []))
        implicated_fields.update(collect_condition_field_refs(rule["when"]))
        implicated_fields.add(field_ref(rule["target_section"], rule["target_field"]))

        has_explicit_input = any(
            reference not in assumed_fields and not is_tbd(get_field_value(requirements, reference))
            for reference in implicated_fields
        )
        if not has_explicit_input:
            continue

        issues.append(
            {
                "validator": "semantic_consistency",
                "severity": rule.get("severity", "warning"),
                "message": rule["message"],
                "issue_code": rule["rule_id"],
            }
        )

    return issues
