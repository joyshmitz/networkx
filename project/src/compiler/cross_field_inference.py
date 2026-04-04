from __future__ import annotations

from pathlib import Path
from typing import Any

from network_methodology_sandbox.model_utils import (
    is_no,
    is_tbd,
    is_yes,
    load_yaml,
    resolve_project_root,
)


class InferenceRuleConflictError(ValueError):
    """Raised when multiple inference rules derive incompatible values for one target."""


class InferenceRuleCatalogError(ValueError):
    """Raised when the inference rule catalog contains an invalid rule."""


def default_cross_field_rules_path() -> Path:
    return resolve_project_root() / "specs" / "inference" / "cross_field_rules.yaml"


def load_cross_field_rules(path: Path | None = None) -> list[dict[str, Any]]:
    payload = load_yaml(path or default_cross_field_rules_path())
    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        raise InferenceRuleCatalogError("cross_field_rules.yaml must contain a top-level 'rules' list.")
    seen_rule_ids: set[str] = set()
    for index, rule in enumerate(rules, start=1):
        rule_id = rule.get("rule_id")
        if not isinstance(rule_id, str) or not rule_id:
            raise InferenceRuleCatalogError(
                f"cross_field_rules.yaml rule #{index} must define a non-empty string rule_id."
            )
        if rule_id in seen_rule_ids:
            raise InferenceRuleCatalogError(
                f"cross_field_rules.yaml contains duplicate rule_id: {rule_id!r}."
            )
        seen_rule_ids.add(rule_id)
    return rules


def field_ref(section: str, field_id: str) -> str:
    return f"{section}.{field_id}"


def split_field_ref(reference: str) -> tuple[str, str]:
    try:
        section, field_id = reference.split(".", 1)
    except ValueError as exc:
        raise InferenceRuleCatalogError(
            f"Field reference must use '<section>.<field_id>' format, got: {reference!r}"
        ) from exc
    return section, field_id


def get_field_value(requirements: dict[str, Any], reference: str) -> Any:
    section, field_id = split_field_ref(reference)
    section_payload = requirements.get(section, {})
    if not isinstance(section_payload, dict):
        return None
    return section_payload.get(field_id)


def collect_condition_field_refs(expression: dict[str, Any]) -> set[str]:
    if "all_of" in expression:
        return {
            ref
            for clause in expression["all_of"]
            for ref in collect_condition_field_refs(clause)
        }
    if "any_of" in expression:
        return {
            ref
            for clause in expression["any_of"]
            for ref in collect_condition_field_refs(clause)
        }
    reference = expression.get("field")
    return {reference} if isinstance(reference, str) else set()


def evaluate_condition(expression: dict[str, Any], requirements: dict[str, Any]) -> bool:
    if "all_of" in expression:
        return all(evaluate_condition(clause, requirements) for clause in expression["all_of"])
    if "any_of" in expression:
        return any(evaluate_condition(clause, requirements) for clause in expression["any_of"])

    reference = expression.get("field")
    op = expression.get("op")
    if not isinstance(reference, str) or not isinstance(op, str):
        raise InferenceRuleCatalogError(
            f"Condition leaf must define string 'field' and 'op', got: {expression!r}"
        )

    actual = get_field_value(requirements, reference)
    if op == "eq":
        return actual == expression.get("value")
    if op == "in":
        values = expression.get("values", [])
        return actual in values
    if op == "not_in":
        values = expression.get("values", [])
        return actual not in values
    if op == "is_yes":
        return is_yes(actual)
    if op == "is_no":
        return is_no(actual)

    raise InferenceRuleCatalogError(f"Unsupported inference operator: {op!r}")


def apply_cross_field_inferences(
    requirements: dict[str, dict[str, Any]],
    *,
    rules: list[dict[str, Any]] | None = None,
    max_passes: int = 4,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    if max_passes < 1:
        raise ValueError("max_passes must be >= 1")

    loaded_rules = rules if rules is not None else load_cross_field_rules()
    inference_rules = [rule for rule in loaded_rules if rule.get("mode") == "infer_if_tbd"]
    normalized = {
        section_name: dict(section)
        for section_name, section in requirements.items()
    }
    inferred_by_target: dict[str, dict[str, Any]] = {}
    inferences: list[dict[str, Any]] = []

    for pass_index in range(1, max_passes + 1):
        fired_this_pass = 0
        for rule in inference_rules:
            if not evaluate_condition(rule["when"], normalized):
                continue

            target_section = rule["target_section"]
            target_field = rule["target_field"]
            target_reference = field_ref(target_section, target_field)
            section_payload = normalized.setdefault(target_section, {})
            present = target_field in section_payload
            current_value = section_payload.get(target_field)

            existing_inference = inferred_by_target.get(target_reference)
            if existing_inference is not None:
                if existing_inference["assumed_value"] != rule["inferred_value"]:
                    raise InferenceRuleConflictError(
                        "Conflicting cross-field inference rules derived different values "
                        f"for {target_reference}: {existing_inference['rule_id']} -> "
                        f"{existing_inference['assumed_value']!r}, {rule['rule_id']} -> "
                        f"{rule['inferred_value']!r}"
                    )
                continue

            if present and not is_tbd(current_value):
                continue

            section_payload[target_field] = rule["inferred_value"]
            inference = {
                "kind": "inference",
                "field_id": target_field,
                "section": target_section,
                "original_value": "__missing__" if not present else current_value,
                "assumed_value": rule["inferred_value"],
                "source": f"inference:{rule['rule_id']}",
                "rule_id": rule["rule_id"],
                "source_fields": list(rule.get("source_fields", [])),
                "reason": rule["reason"],
                "pass_index": pass_index,
                "review_required": True,
            }
            inferences.append(inference)
            inferred_by_target[target_reference] = inference
            fired_this_pass += 1

        if fired_this_pass == 0:
            break

    return normalized, inferences
