#!/usr/bin/env python3
"""Generate derived review packets from the shared workspace snapshot."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from intake.evidence_status import build_evidence_status_from_snapshot
from intake.workspace_snapshot import build_workspace_snapshot
from model_utils import load_yaml, resolve_project_root, write_yaml

REVIEW_SCHEMA_VERSION = "0.2.0"
PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SOURCE_KIND_ORDER = {"field": 0, "validator_issue": 1, "evidence_gap": 2}
SKIPPED_VALIDATORS = {"role_assignments"}
FIELD_CONTEXT_DEFAULTS = {
    "field_id": None,
    "related_field_ids": [],
    "section": "",
    "field_label_uk": None,
    "current_value": None,
    "status": None,
    "strictness": None,
    "owner_role": None,
    "reviewer_roles": [],
    "owner_persons": [],
    "reviewer_persons": [],
    "comment": None,
    "source_ref": None,
}
REQUIRED_ROUTING_KEYS = {
    "target_role",
    "primary_role",
    "primary_person",
    "secondary_roles",
    "secondary_persons",
    "routing_state",
    "escalation_reason",
}
ALLOWED_ITEM_OVERRIDE_KEYS = {
    "evidence_strength",
    "advisory_minimum_strength",
    "blocking_stage_allowed",
    "blocking_allowlisted",
    "blocking_minimum_strength",
    "blocking_eligible",
    "blocking_gap",
    "blocking_reason",
}


def _parse_cli_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Expected YYYY-MM-DD date, got: {raw!r}"
        ) from exc


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "item"


def _list_or_none(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "none"


def _load_validator_routing(project_root: Path) -> dict[str, Any]:
    return load_yaml(project_root / "specs" / "review" / "validator_routing.yaml")


def _stable_item_id(
    object_id: str,
    source_kind: str,
    source_key: str,
    target_role: str,
) -> str:
    return ".".join(
        [
            _slugify(object_id),
            _slugify(source_kind),
            _slugify(source_key),
            _slugify(target_role),
        ]
    )


def _priority_from_strictness(strictness: str | None) -> str:
    mapping = {
        "S4": "critical",
        "S3": "high",
        "S2": "medium",
        "S1": "low",
    }
    return mapping.get(strictness or "", "medium")


def _derive_priority(
    *,
    source_kind: str,
    routing_state: str,
    strictness: str | None = None,
    severity: str | None = None,
    blocking_gap: bool = False,
) -> str:
    if source_kind == "validator_issue":
        priority = "critical" if severity in {"error", "critical"} else "high"
    elif source_kind == "evidence_gap":
        priority = "critical" if blocking_gap else "medium"
    else:
        priority = _priority_from_strictness(strictness)

    if routing_state in {"unassigned_owner", "second_reviewer_required", "coordinator_escalation"}:
        if PRIORITY_ORDER[priority] > PRIORITY_ORDER["high"]:
            return "high"
    return priority


def _derive_next_action(
    source_kind: str,
    routing_state: str,
    *,
    blocking_gap: bool = False,
) -> str:
    if routing_state == "unassigned_owner":
        return "Assign the owner role in role_assignments.yaml before review can proceed."
    if routing_state == "second_reviewer_required":
        return "Coordinator must assign an independent second reviewer before this item can be accepted."
    if routing_state == "coordinator_escalation":
        return "Coordinator must resolve routing ambiguity and pick the accountable reviewer."
    if source_kind == "validator_issue":
        return "Review the validator finding and update the implicated field or design assumption."
    if source_kind == "evidence_gap":
        if blocking_gap:
            return "Attach the required workspace artifact evidence before the stage gate can pass."
        return "Attach or reference supporting evidence in the workspace sources."
    return "Answer the field in intake inputs and regenerate the derived workspace outputs."


def _item_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        PRIORITY_ORDER[item["priority"]],
        SOURCE_KIND_ORDER.get(item["source_kind"], 99),
        item.get("section") or "",
        item.get("field_id") or "",
        item["review_item_id"],
    )


def _field_context_from_record(field_record: dict[str, Any] | None) -> dict[str, Any]:
    if field_record is None:
        return {
            **FIELD_CONTEXT_DEFAULTS,
            "related_field_ids": [],
            "reviewer_roles": [],
            "owner_persons": [],
            "reviewer_persons": [],
        }

    field_id = field_record.get("field_id")
    return {
        "field_id": field_id,
        "related_field_ids": [field_id] if field_id else [],
        "section": field_record.get("section", ""),
        "field_label_uk": field_record.get("label_uk"),
        "current_value": field_record.get("value"),
        "status": field_record.get("status"),
        "strictness": field_record.get("strictness"),
        "owner_role": field_record.get("owner_role"),
        "reviewer_roles": list(field_record.get("reviewer_roles", [])),
        "owner_persons": list(field_record.get("owner_persons", [])),
        "reviewer_persons": list(field_record.get("reviewer_persons", [])),
        "comment": field_record.get("comment"),
        "source_ref": field_record.get("source_ref"),
    }


def _make_review_item(
    *,
    object_id: str,
    source_kind: str,
    source_key: str,
    target_role: str,
    routing: dict[str, Any],
    review_reasons: list[str],
    field_record: dict[str, Any] | None = None,
    related_field_ids: list[str] | None = None,
    field_context_overrides: dict[str, Any] | None = None,
    severity: str | None = None,
    validator: str | None = None,
    message: str | None = None,
    item_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    missing_routing_keys = REQUIRED_ROUTING_KEYS - set(routing)
    if missing_routing_keys:
        missing = ", ".join(sorted(missing_routing_keys))
        raise KeyError(f"Routing payload is missing required keys: {missing}")

    field_context = _field_context_from_record(field_record)
    if related_field_ids is not None:
        field_context["related_field_ids"] = list(related_field_ids)
    if field_context_overrides:
        field_context.update(field_context_overrides)
    blocking_gap = bool(item_overrides and item_overrides.get("blocking_gap"))
    if item_overrides:
        unexpected_keys = set(item_overrides) - ALLOWED_ITEM_OVERRIDE_KEYS
        if unexpected_keys:
            unexpected = ", ".join(sorted(unexpected_keys))
            raise KeyError(f"Unexpected review item override keys: {unexpected}")

    item = {
        "review_item_id": _stable_item_id(
            object_id,
            source_kind,
            source_key,
            target_role,
        ),
        "source_kind": source_kind,
        "source_key": source_key,
        "object_id": object_id,
        **field_context,
        "priority": _derive_priority(
            source_kind=source_kind,
            routing_state=routing["routing_state"],
            strictness=field_context.get("strictness"),
            severity=severity,
            blocking_gap=blocking_gap,
        ),
        "next_action": _derive_next_action(
            source_kind,
            routing["routing_state"],
            blocking_gap=blocking_gap,
        ),
        "primary_role": routing["primary_role"],
        "primary_person": routing["primary_person"],
        "secondary_roles": routing["secondary_roles"],
        "secondary_persons": routing["secondary_persons"],
        "routing_state": routing["routing_state"],
        "escalation_reason": routing["escalation_reason"],
        "review_reasons": review_reasons,
        "validator": validator,
        "severity": severity,
        "message": message,
    }
    if item_overrides:
        for key in sorted(item_overrides):
            item[key] = item_overrides[key]
    return item


def _routing_from_field_record(field_record: dict[str, Any]) -> dict[str, Any]:
    owner_role = field_record.get("owner_role")
    owner_persons = list(field_record.get("owner_persons", []))
    reviewer_roles = list(field_record.get("reviewer_roles", []))

    if not owner_role:
        return {
            "target_role": "coordinator",
            "primary_role": "coordinator",
            "primary_person": None,
            "secondary_roles": reviewer_roles,
            "secondary_persons": list(field_record.get("reviewer_persons", [])),
            "routing_state": "coordinator_escalation",
            "escalation_reason": "Field dictionary does not define an owner role.",
        }

    if not owner_persons:
        return {
            "target_role": "coordinator",
            "primary_role": owner_role,
            "primary_person": None,
            "secondary_roles": reviewer_roles,
            "secondary_persons": list(field_record.get("reviewer_persons", [])),
            "routing_state": "unassigned_owner",
            "escalation_reason": f"Owner role '{owner_role}' is not assigned to any person.",
        }

    if len(owner_persons) > 1:
        return {
            "target_role": "coordinator",
            "primary_role": "coordinator",
            "primary_person": None,
            "secondary_roles": [owner_role, *reviewer_roles],
            "secondary_persons": sorted(
                set(owner_persons) | set(field_record.get("reviewer_persons", []))
            ),
            "routing_state": "coordinator_escalation",
            "escalation_reason": (
                f"Owner role '{owner_role}' resolves to multiple people: {owner_persons}."
            ),
        }

    primary_person = owner_persons[0]
    independent_reviewers = sorted(
        set(field_record.get("reviewer_persons", [])) - {primary_person}
    )

    if field_record.get("strictness") == "S4" and reviewer_roles and not independent_reviewers:
        return {
            "target_role": owner_role,
            "primary_role": owner_role,
            "primary_person": primary_person,
            "secondary_roles": reviewer_roles,
            "secondary_persons": [],
            "routing_state": "second_reviewer_required",
            "escalation_reason": (
                "All reviewer roles collapse to the owner; an independent reviewer is required."
            ),
        }

    return {
        "target_role": owner_role,
        "primary_role": owner_role,
        "primary_person": primary_person,
        "secondary_roles": reviewer_roles,
        "secondary_persons": independent_reviewers,
        "routing_state": "assigned",
        "escalation_reason": None,
    }


def _reason_list_for_field(field_record: dict[str, Any]) -> list[str]:
    reasons = ["unresolved field"]
    if field_record.get("strictness") == "S4":
        reasons.append("stage-gate critical field")
    return reasons


def _build_field_review_items(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for field_record in snapshot["fields"]["unresolved"]:
        routing = _routing_from_field_record(field_record)
        items.append(
            _make_review_item(
                object_id=snapshot["object_id"],
                source_kind="field",
                source_key=field_record["field_id"],
                target_role=routing["target_role"],
                routing=routing,
                review_reasons=_reason_list_for_field(field_record),
                field_record=field_record,
            )
        )
    return items


def _message_matches(rule: dict[str, Any], message: str) -> bool:
    message_contains = rule.get("message_contains")
    if message_contains is None:
        return True
    if isinstance(message_contains, str):
        return message_contains in message
    return all(fragment in message for fragment in message_contains)


def _match_validator_rule(
    issue: dict[str, Any],
    validator_spec: dict[str, Any],
) -> dict[str, Any] | None:
    matches = [
        rule
        for rule in validator_spec.get("rules", [])
        if _message_matches(rule, issue["message"])
    ]
    if len(matches) > 1:
        raise ValueError(
            f"Validator routing for '{issue['validator']}' is ambiguous: "
            f"multiple rules matched message {issue['message']!r}."
        )
    return matches[0] if matches else None


def _route_validator_issue(
    issue: dict[str, Any],
    *,
    snapshot: dict[str, Any],
    routing_spec: dict[str, Any],
) -> dict[str, Any]:
    field_records = snapshot["fields"]["records"]
    validator_name = issue["validator"]
    validator_spec = routing_spec.get("validators", {}).get(validator_name, {})
    rule = _match_validator_rule(issue, validator_spec) or {}
    issue_code = rule.get("issue_code") or _slugify(issue["message"])
    source_key = f"{validator_name}:{issue_code}"
    field_ids = list(rule.get("field_ids", []))
    related_field_ids = list(field_ids)

    if len(field_ids) == 1 and field_ids[0] in field_records:
        field_record = field_records[field_ids[0]]
        review_reasons = ["pipeline validator finding"]
        if field_record.get("strictness") == "S4":
            review_reasons.append("stage-gate critical field")
        return {
            "source_key": source_key,
            "routing": _routing_from_field_record(field_record),
            "field_record": field_record,
            "related_field_ids": related_field_ids,
            "review_reasons": review_reasons,
            "field_context_overrides": None,
        }

    if len(field_ids) > 1:
        primary_field = field_records.get(field_ids[0])
        owner_roles = sorted(
            {
                field_records[field_id]["owner_role"]
                for field_id in field_ids
                if field_id in field_records and field_records[field_id].get("owner_role")
            }
        )
        secondary_persons: set[str] = set()
        for field_id in field_ids:
            field_record = field_records.get(field_id)
            if not field_record:
                continue
            secondary_persons.update(field_record.get("owner_persons", []))
            secondary_persons.update(field_record.get("reviewer_persons", []))

        return {
            "source_key": source_key,
            "routing": {
                "target_role": "coordinator",
                "primary_role": "coordinator",
                "primary_person": None,
                "secondary_roles": owner_roles,
                "secondary_persons": sorted(secondary_persons),
                "routing_state": "coordinator_escalation",
                "escalation_reason": (
                    f"Validator finding implicates multiple fields: {related_field_ids}."
                ),
            },
            "field_record": primary_field,
            "related_field_ids": related_field_ids,
            "review_reasons": ["pipeline validator finding"],
            "field_context_overrides": {
                "comment": None,
                "source_ref": None,
            },
        }

    fallback_roles = list(rule.get("fallback_owner_roles", [])) or list(
        validator_spec.get("fallback_owner_roles", [])
    )
    resolved_persons: set[str] = set()
    for role in fallback_roles:
        resolved_persons.update(snapshot["roles"]["role_to_persons"].get(role, []))

    routing_state = "assigned"
    primary_role = fallback_roles[0] if len(fallback_roles) == 1 else "coordinator"
    primary_person = None
    target_role = primary_role
    escalation_reason = None

    if len(fallback_roles) != 1:
        routing_state = "coordinator_escalation"
        primary_role = "coordinator"
        target_role = "coordinator"
        escalation_reason = (
            f"Validator '{validator_name}' fallback roles are ambiguous: {fallback_roles}."
        )
    elif len(resolved_persons) != 1:
        routing_state = "coordinator_escalation"
        primary_role = "coordinator"
        target_role = "coordinator"
        if not resolved_persons:
            escalation_reason = (
                f"Fallback owner role '{fallback_roles[0]}' is not assigned to any person."
            )
        else:
            escalation_reason = (
                f"Fallback owner role '{fallback_roles[0]}' resolves to multiple people: "
                f"{sorted(resolved_persons)}."
            )
    else:
        primary_person = next(iter(resolved_persons))

    return {
        "source_key": source_key,
        "routing": {
            "target_role": target_role,
            "primary_role": primary_role,
            "primary_person": primary_person,
            "secondary_roles": fallback_roles,
            "secondary_persons": sorted(resolved_persons),
            "routing_state": routing_state,
            "escalation_reason": escalation_reason,
        },
        "field_record": None,
        "related_field_ids": related_field_ids,
        "review_reasons": ["pipeline validator finding"],
        "field_context_overrides": None,
    }


def _build_validator_review_items(
    snapshot: dict[str, Any],
    *,
    project_root: Path,
) -> list[dict[str, Any]]:
    routing_spec = _load_validator_routing(project_root)
    items: list[dict[str, Any]] = []
    for issue in snapshot["pipeline"]["issues"]:
        # Role-assignment collapse is already represented directly via field routing
        # states, so the raw validator issue would only duplicate the same operator action.
        if issue["validator"] in SKIPPED_VALIDATORS:
            continue
        routed_issue = _route_validator_issue(
            issue,
            snapshot=snapshot,
            routing_spec=routing_spec,
        )
        items.append(
            _make_review_item(
                object_id=snapshot["object_id"],
                source_kind="validator_issue",
                source_key=routed_issue["source_key"],
                target_role=routed_issue["routing"]["target_role"],
                routing=routed_issue["routing"],
                review_reasons=routed_issue["review_reasons"],
                field_record=routed_issue["field_record"],
                related_field_ids=routed_issue["related_field_ids"],
                field_context_overrides=routed_issue["field_context_overrides"],
                validator=issue["validator"],
                severity=issue["severity"],
                message=issue["message"],
            )
        )
    return items


def _build_evidence_gap_items(
    snapshot: dict[str, Any],
    *,
    project_root: Path,
) -> list[dict[str, Any]]:
    evidence_status = build_evidence_status_from_snapshot(snapshot, project_root=project_root)
    field_records = snapshot["fields"]["records"]
    items: list[dict[str, Any]] = []

    for evidence_field in evidence_status["fields"]:
        if not evidence_field["advisory_gap"]:
            continue
        if not evidence_field["review_routing_required"]:
            continue

        field_record = field_records[evidence_field["field_id"]]
        routing = _routing_from_field_record(field_record)
        review_reasons = [evidence_field["gap_reason"] or "missing evidence"]
        if evidence_field["blocking_gap"]:
            review_reasons.insert(0, "blocking evidence gap")
        if field_record.get("strictness") == "S4":
            review_reasons.append("stage-gate critical field")

        items.append(
            _make_review_item(
                object_id=snapshot["object_id"],
                source_kind="evidence_gap",
                source_key=evidence_field["field_id"],
                target_role=routing["target_role"],
                routing=routing,
                review_reasons=review_reasons,
                field_record=field_record,
                field_context_overrides={
                    "comment": field_record.get("comment"),
                    "source_ref": evidence_field.get("source_ref"),
                },
                item_overrides={
                    "evidence_strength": evidence_field["evidence_strength"],
                    "advisory_minimum_strength": evidence_field["advisory_minimum_strength"],
                    "blocking_stage_allowed": evidence_field["blocking_stage_allowed"],
                    "blocking_allowlisted": evidence_field["blocking_allowlisted"],
                    "blocking_minimum_strength": evidence_field["blocking_minimum_strength"],
                    "blocking_eligible": evidence_field["blocking_eligible"],
                    "blocking_gap": evidence_field["blocking_gap"],
                    "blocking_reason": evidence_field["blocking_reason"],
                },
            )
        )
    return items


def _group_items_by_person(
    items: list[dict[str, Any]],
    person_ids: list[str],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped = {
        person_id: {"primary_items": [], "secondary_items": []}
        for person_id in person_ids
    }
    for item in items:
        primary_person = item.get("primary_person")
        if primary_person in grouped:
            grouped[primary_person]["primary_items"].append(item)
        for secondary_person in item.get("secondary_persons", []):
            if secondary_person == primary_person:
                continue
            if secondary_person in grouped:
                grouped[secondary_person]["secondary_items"].append(item)
    return grouped


def _build_registry(
    snapshot: dict[str, Any],
    items: list[dict[str, Any]],
    grouped_items: dict[str, dict[str, list[dict[str, Any]]]],
    coordinator_items: list[dict[str, Any]],
) -> dict[str, Any]:
    reviewers: list[dict[str, Any]] = []
    for person_id, roles in snapshot["roles"]["person_to_roles"].items():
        primary_items = grouped_items[person_id]["primary_items"]
        secondary_items = grouped_items[person_id]["secondary_items"]
        packet_path = None
        if primary_items or secondary_items:
            packet_path = f"reports/review_packet.{person_id}.md"
        reviewers.append(
            {
                "person_id": person_id,
                "roles": list(roles),
                "packet_path": packet_path,
                "primary_item_ids": [item["review_item_id"] for item in primary_items],
                "secondary_item_ids": [item["review_item_id"] for item in secondary_items],
            }
        )

    by_routing_state: dict[str, int] = {}
    by_source_kind: dict[str, int] = {}
    for item in items:
        by_routing_state[item["routing_state"]] = by_routing_state.get(item["routing_state"], 0) + 1
        by_source_kind[item["source_kind"]] = by_source_kind.get(item["source_kind"], 0) + 1

    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "review_at": snapshot["snapshot_at"],
        "date_used": snapshot["date_used"],
        "object_id": snapshot["object_id"],
        "workspace": snapshot["workspace"],
        "questionnaire_path": snapshot["questionnaire_path"],
        "summary": {
            "total_review_items": len(items),
            "by_routing_state": by_routing_state,
            "by_source_kind": by_source_kind,
            "coordinator_packet": "reports/review_packet._coordinator.md",
        },
        "reviewers": reviewers,
        "coordinator": {
            "packet_path": "reports/review_packet._coordinator.md",
            "item_ids": [item["review_item_id"] for item in coordinator_items],
        },
        "review_items": items,
    }


def _render_item_block(item: dict[str, Any]) -> list[str]:
    reasons = ", ".join(item["review_reasons"])
    lines = [
        f"### `{item['review_item_id']}`",
        "",
        f"- Priority: `{item['priority']}`",
        f"- Routing state: `{item['routing_state']}`",
        f"- Review reason: {reasons}",
        f"- Source: `{item['source_kind']}` / `{item['source_key']}`",
    ]

    if item.get("field_id"):
        lines.extend(
            [
                f"- Field: `{item['field_id']}`",
                f"- Section: `{item['section']}`" if item.get("section") else "- Section: none",
                f"- Current status: `{item['status']}`" if item.get("status") else "- Current status: none",
                f"- Current value: `{item['current_value']}`" if item.get("current_value") is not None else "- Current value: none",
                f"- Strictness: `{item['strictness']}`" if item.get("strictness") else "- Strictness: none",
                f"- Owner role: `{item['owner_role']}`" if item.get("owner_role") else "- Owner role: none",
                f"- Reviewer roles: {_list_or_none(item['reviewer_roles'])}",
                f"- Owner persons: {_list_or_none(item['owner_persons'])}",
                f"- Reviewer persons: {_list_or_none(item['reviewer_persons'])}",
            ]
        )

    if item.get("related_field_ids") and len(item["related_field_ids"]) > 1:
        lines.append(f"- Related fields: {_list_or_none(item['related_field_ids'])}")

    lines.extend(
        [
            f"- Primary role: `{item['primary_role']}`" if item.get("primary_role") else "- Primary role: none",
            f"- Primary person: `{item['primary_person']}`" if item.get("primary_person") else "- Primary person: none",
            f"- Secondary roles: {_list_or_none(item['secondary_roles'])}",
            f"- Secondary persons: {_list_or_none(item['secondary_persons'])}",
        ]
    )

    if item.get("validator"):
        lines.append(
            f"- Validator: `{item['validator']}` / `{item['severity']}`"
        )
        lines.append(f"- Validator message: {item['message']}")

    if item["source_kind"] == "evidence_gap":
        lines.extend(
            [
                (
                    f"- Evidence strength: `{item['evidence_strength']}`"
                    if item.get("evidence_strength")
                    else "- Evidence strength: none"
                ),
                (
                    f"- Advisory minimum: `{item['advisory_minimum_strength']}`"
                    if item.get("advisory_minimum_strength")
                    else "- Advisory minimum: none"
                ),
                (
                    f"- Blocking minimum: `{item['blocking_minimum_strength']}`"
                    if item.get("blocking_minimum_strength")
                    else "- Blocking minimum: none"
                ),
                f"- Blocking stage allowed: {'yes' if item.get('blocking_stage_allowed') else 'no'}",
                f"- Blocking allowlisted: {'yes' if item.get('blocking_allowlisted') else 'no'}",
                f"- Blocking eligible: {'yes' if item.get('blocking_eligible') else 'no'}",
                f"- Blocking gap: {'yes' if item.get('blocking_gap') else 'no'}",
            ]
        )
        if item.get("blocking_reason"):
            lines.append(f"- Blocking reason: {item['blocking_reason']}")

    if item.get("source_ref"):
        lines.append(f"- Source ref: `{item['source_ref']}`")
    if item.get("comment"):
        lines.append(f"- Comment: {item['comment']}")
    if item.get("escalation_reason"):
        lines.append(f"- Escalation reason: {item['escalation_reason']}")

    lines.append(f"- Next action: {item['next_action']}")
    lines.append("")
    return lines


def _write_registry_markdown(path: Path, registry: dict[str, Any]) -> None:
    summary = registry["summary"]
    lines = [
        f"# Reviewer Registry — {registry['object_id']}",
        "",
        f"- Review date: {registry['review_at']}",
        f"- Workspace: {registry['workspace']}",
        f"- Questionnaire: {registry['questionnaire_path']}",
        f"- Total review items: {summary['total_review_items']}",
        f"- Coordinator packet: `{summary['coordinator_packet']}`",
        "",
        "## Reviewers",
        "",
        "| Person | Roles | Primary | Secondary | Packet |",
        "|--------|-------|---------|-----------|--------|",
    ]

    for reviewer in registry["reviewers"]:
        packet_path = reviewer["packet_path"] or "none"
        lines.append(
            f"| `{reviewer['person_id']}` | {', '.join(reviewer['roles'])} | "
            f"{len(reviewer['primary_item_ids'])} | {len(reviewer['secondary_item_ids'])} | "
            f"`{packet_path}` |"
        )

    lines.extend(
        [
            "",
            "## Routing Summary",
            "",
        ]
    )
    for state, count in summary["by_routing_state"].items():
        lines.append(f"- `{state}`: {count}")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _write_person_packet(
    path: Path,
    *,
    person_id: str,
    roles: list[str],
    primary_items: list[dict[str, Any]],
    secondary_items: list[dict[str, Any]],
    registry: dict[str, Any],
) -> None:
    lines = [
        f"# Review Packet — {person_id}",
        "",
        f"- Review date: {registry['review_at']}",
        f"- Roles: {_list_or_none(roles)}",
        f"- Primary items: {len(primary_items)}",
        f"- Secondary items: {len(secondary_items)}",
        "",
        "## Primary Actions",
        "",
    ]

    if primary_items:
        for item in primary_items:
            lines.extend(_render_item_block(item))
    else:
        lines.append("- none")
        lines.append("")

    lines.extend(
        [
            "## Secondary Review",
            "",
        ]
    )
    if secondary_items:
        for item in secondary_items:
            lines.extend(_render_item_block(item))
    else:
        lines.append("- none")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _write_coordinator_packet(
    path: Path,
    *,
    registry: dict[str, Any],
    coordinator_items: list[dict[str, Any]],
) -> None:
    lines = [
        f"# Coordinator Review Packet — {registry['object_id']}",
        "",
        f"- Review date: {registry['review_at']}",
        f"- Workspace: {registry['workspace']}",
        f"- Total review items: {registry['summary']['total_review_items']}",
        f"- Coordinator queue: {len(coordinator_items)}",
        "",
        "## Coordinator Queue",
        "",
    ]

    if coordinator_items:
        for item in coordinator_items:
            lines.extend(_render_item_block(item))
    else:
        lines.append("- none")
        lines.append("")

    lines.extend(
        [
            "## Reviewer Packets",
            "",
        ]
    )
    for reviewer in registry["reviewers"]:
        if reviewer["packet_path"]:
            lines.append(
                f"- `{reviewer['person_id']}`: `{reviewer['packet_path']}` "
                f"(primary={len(reviewer['primary_item_ids'])}, secondary={len(reviewer['secondary_item_ids'])})"
            )
    if not any(reviewer["packet_path"] for reviewer in registry["reviewers"]):
        lines.append("- none")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def review_workspace(
    workspace_path: Path,
    *,
    project_root: Path | None = None,
    review_on: date | None = None,
) -> dict[str, Any]:
    project_root = project_root or resolve_project_root()
    snapshot = build_workspace_snapshot(
        workspace_path,
        project_root=project_root,
        snapshot_on=review_on,
        write_pipeline_outputs=False,
    )

    review_items = [
        *_build_field_review_items(snapshot),
        *_build_validator_review_items(snapshot, project_root=project_root),
        *_build_evidence_gap_items(snapshot, project_root=project_root),
    ]
    review_items = sorted(review_items, key=_item_sort_key)
    coordinator_items = [
        item for item in review_items if item["routing_state"] != "assigned"
    ]
    grouped_items = _group_items_by_person(
        review_items,
        list(snapshot["roles"]["person_to_roles"]),
    )

    registry = _build_registry(
        snapshot,
        review_items,
        grouped_items,
        coordinator_items,
    )
    reports_dir = Path(snapshot["workspace"]) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    write_yaml(reports_dir / "reviewer_registry.yaml", registry)
    _write_registry_markdown(reports_dir / "reviewer_registry.md", registry)
    _write_coordinator_packet(
        reports_dir / "review_packet._coordinator.md",
        registry=registry,
        coordinator_items=coordinator_items,
    )

    for reviewer in registry["reviewers"]:
        if not reviewer["packet_path"]:
            continue
        _write_person_packet(
            reports_dir / f"review_packet.{reviewer['person_id']}.md",
            person_id=reviewer["person_id"],
            roles=reviewer["roles"],
            primary_items=grouped_items[reviewer["person_id"]]["primary_items"],
            secondary_items=grouped_items[reviewer["person_id"]]["secondary_items"],
            registry=registry,
        )

    return registry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate derived review packets from an intake workspace.",
    )
    parser.add_argument("workspace_path", help="Workspace directory to review.")
    parser.add_argument(
        "--date",
        dest="review_on",
        type=_parse_cli_date,
        help="Fixed review date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()

    result = review_workspace(
        Path(args.workspace_path),
        review_on=args.review_on,
    )
    print(
        yaml.safe_dump(
            {
                "object_id": result["object_id"],
                "review_at": result["review_at"],
                "total_review_items": result["summary"]["total_review_items"],
                "routing_states": result["summary"]["by_routing_state"],
                "reports": {
                    "registry_yaml": "reports/reviewer_registry.yaml",
                    "registry_markdown": "reports/reviewer_registry.md",
                    "coordinator_packet": "reports/review_packet._coordinator.md",
                },
            },
            sort_keys=False,
            allow_unicode=True,
        )
    )


if __name__ == "__main__":
    main()
