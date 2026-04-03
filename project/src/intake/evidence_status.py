#!/usr/bin/env python3
"""Generate advisory evidence status from the shared workspace snapshot."""
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

from intake.workspace_snapshot import build_workspace_snapshot
from model_utils import load_yaml, resolve_project_root, write_yaml

EVIDENCE_SCHEMA_VERSION = "0.1.0"
EVIDENCE_STRENGTH_ORDER = {
    "none": 0,
    "reference_only": 1,
    "structured_ref": 2,
    "workspace_artifact": 3,
}
STRUCTURED_SOURCE_REF_PATTERN = re.compile(
    r"^\s*([a-z_][a-z0-9_]*)\s*[:=]\s*(.+?)\s*$",
    re.IGNORECASE,
)
ARTIFACT_SOURCE_KEYS = {"path", "artifact", "workspace_path", "file"}


def _parse_cli_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Expected YYYY-MM-DD date, got: {raw!r}"
        ) from exc


def _field_sort_key(field: dict[str, Any]) -> tuple[str, str]:
    return field.get("section") or "", field["field_id"]


def _load_evidence_policy(project_root: Path) -> dict[str, Any]:
    return load_yaml(project_root / "specs" / "evidence" / "evidence_policy.yaml")


def _strength_rank(strength: str) -> int:
    return EVIDENCE_STRENGTH_ORDER[strength]


def _split_source_ref(source_ref: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"[;\n]+", source_ref) if segment.strip()]


def _parse_structured_source_ref(source_ref: str) -> dict[str, str]:
    structured: dict[str, str] = {}
    for segment in _split_source_ref(source_ref):
        match = STRUCTURED_SOURCE_REF_PATTERN.match(segment)
        if not match:
            continue
        key, value = match.groups()
        structured[key.lower()] = value.strip()
    return structured


def _safe_resolve_in_workspace(workspace: Path, raw_path: str) -> str | None:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (workspace / candidate).resolve()

    try:
        resolved.relative_to(workspace.resolve())
    except ValueError:
        return None

    if not resolved.exists():
        return None

    return str(resolved.relative_to(workspace.resolve()))


def analyze_source_ref(source_ref: str | None, workspace: Path) -> dict[str, Any]:
    normalized = (source_ref or "").strip()
    if not normalized:
        return {
            "source_ref": None,
            "structured_ref": {},
            "workspace_artifacts": [],
            "evidence_strength": "none",
        }

    structured_ref = _parse_structured_source_ref(normalized)
    workspace_artifacts: list[str] = []
    for key, value in structured_ref.items():
        if key not in ARTIFACT_SOURCE_KEYS:
            continue
        artifact_path = _safe_resolve_in_workspace(workspace, value)
        if artifact_path is not None:
            workspace_artifacts.append(artifact_path)

    if workspace_artifacts:
        evidence_strength = "workspace_artifact"
    elif structured_ref:
        evidence_strength = "structured_ref"
    else:
        evidence_strength = "reference_only"

    return {
        "source_ref": normalized,
        "structured_ref": structured_ref,
        "workspace_artifacts": sorted(set(workspace_artifacts)),
        "evidence_strength": evidence_strength,
    }


def _merge_field_policy(
    field_id: str,
    *,
    defaults: dict[str, Any],
    field_overrides: dict[str, Any],
) -> dict[str, Any]:
    # Overrides replace default values, including list-valued keys.
    merged = dict(defaults)
    merged.update(field_overrides.get(field_id, {}))
    return merged


def _is_monitored_field(
    field_record: dict[str, Any],
    *,
    defaults: dict[str, Any],
    field_overrides: dict[str, Any],
) -> bool:
    field_id = field_record["field_id"]
    if not field_record.get("evidence_required"):
        return False
    if field_id in set(defaults.get("exclude_fields", [])):
        return False
    if field_id in field_overrides:
        return True
    if field_id in set(defaults.get("include_fields", [])):
        return True
    return field_record.get("strictness") in set(defaults.get("monitored_strictness", []))


def build_evidence_status_from_snapshot(
    snapshot: dict[str, Any],
    *,
    project_root: Path | None = None,
) -> dict[str, Any]:
    project_root = project_root or resolve_project_root()
    workspace = Path(snapshot["workspace"])
    policy = _load_evidence_policy(project_root)
    defaults = policy.get("defaults", {})
    field_overrides = policy.get("field_overrides", {})
    project_stage = snapshot.get("metadata", {}).get("project_stage")

    fields: list[dict[str, Any]] = []
    for field_record in sorted(snapshot["fields"]["records"].values(), key=_field_sort_key):
        if not _is_monitored_field(
            field_record,
            defaults=defaults,
            field_overrides=field_overrides,
        ):
            continue

        field_policy = _merge_field_policy(
            field_record["field_id"],
            defaults=defaults,
            field_overrides=field_overrides,
        )
        signal = analyze_source_ref(field_record.get("source_ref"), workspace)
        advisory_minimum_strength = field_policy["advisory_minimum_strength"]
        advisory_gap = (
            _strength_rank(signal["evidence_strength"])
            < _strength_rank(advisory_minimum_strength)
        )
        blocking_eligible = project_stage in set(field_policy.get("blocking_allowed_stages", []))
        review_routing_required = advisory_gap and (
            field_policy.get("review_route_always", False)
            or field_record["status"] in set(field_policy.get("review_route_statuses", []))
        )

        if not advisory_gap:
            gap_reason = None
        elif signal["evidence_strength"] == "none":
            gap_reason = "missing evidence"
        else:
            gap_reason = (
                f"weak evidence: {signal['evidence_strength']} < {advisory_minimum_strength}"
            )

        fields.append(
            {
                "field_id": field_record["field_id"],
                "section": field_record["section"],
                "label_uk": field_record.get("label_uk"),
                "strictness": field_record.get("strictness"),
                "status": field_record.get("status"),
                "value": field_record.get("value"),
                "evidence_required": field_record.get("evidence_required"),
                "evidence_strength": signal["evidence_strength"],
                "advisory_minimum_strength": advisory_minimum_strength,
                "blocking_eligible": blocking_eligible,
                "review_routing_required": review_routing_required,
                "advisory_gap": advisory_gap,
                "gap_reason": gap_reason,
                "source_ref": signal["source_ref"],
                "structured_ref": signal["structured_ref"],
                "workspace_artifacts": signal["workspace_artifacts"],
                "owner_role": field_record.get("owner_role"),
                "reviewer_roles": list(field_record.get("reviewer_roles", [])),
                "owner_persons": list(field_record.get("owner_persons", [])),
                "reviewer_persons": list(field_record.get("reviewer_persons", [])),
            }
        )

    by_strength: dict[str, int] = {}
    for field in fields:
        by_strength[field["evidence_strength"]] = by_strength.get(field["evidence_strength"], 0) + 1

    advisory_gap_count = sum(1 for field in fields if field["advisory_gap"])
    review_routing_count = sum(1 for field in fields if field["review_routing_required"])
    blocking_eligible_count = sum(1 for field in fields if field["blocking_eligible"])

    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "evidence_at": snapshot["snapshot_at"],
        "date_used": snapshot["date_used"],
        "object_id": snapshot["object_id"],
        "workspace": snapshot["workspace"],
        "questionnaire_path": snapshot["questionnaire_path"],
        "metadata": snapshot.get("metadata", {}),
        "summary": {
            "selected_field_count": len(fields),
            "advisory_gap_count": advisory_gap_count,
            "review_routing_required_count": review_routing_count,
            "blocking_eligible_count": blocking_eligible_count,
            "by_strength": by_strength,
        },
        "fields": fields,
    }


def _write_evidence_status_md(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        f"# Evidence Status — {payload['object_id']}",
        "",
        f"- Evidence date: {payload['evidence_at']}",
        f"- Workspace: {payload['workspace']}",
        f"- Questionnaire: {payload['questionnaire_path']}",
        f"- Project stage: {payload['metadata'].get('project_stage') or 'unknown'}",
        f"- Selected fields: {summary['selected_field_count']}",
        f"- Advisory gaps: {summary['advisory_gap_count']}",
        f"- Review-routing gaps: {summary['review_routing_required_count']}",
        f"- Blocking-eligible fields: {summary['blocking_eligible_count']}",
        "",
        "## Evidence Strength",
        "",
    ]

    for strength in ["none", "reference_only", "structured_ref", "workspace_artifact"]:
        lines.append(f"- `{strength}`: {summary['by_strength'].get(strength, 0)}")
    lines.append("")

    lines.extend(
        [
            "## Field Status",
            "",
            "| Field | Status | Strength | Advisory Min | Gap | Review Route | Blocking Eligible |",
            "|-------|--------|----------|--------------|-----|--------------|-------------------|",
        ]
    )
    for field in payload["fields"]:
        lines.append(
            f"| `{field['field_id']}` | `{field['status']}` | `{field['evidence_strength']}` | "
            f"`{field['advisory_minimum_strength']}` | "
            f"{'yes' if field['advisory_gap'] else 'no'} | "
            f"{'yes' if field['review_routing_required'] else 'no'} | "
            f"{'yes' if field['blocking_eligible'] else 'no'} |"
        )

    lines.extend(
        [
            "",
            "## Advisory Gap Details",
            "",
        ]
    )

    advisory_gap_fields = [field for field in payload["fields"] if field["advisory_gap"]]
    if advisory_gap_fields:
        for field in advisory_gap_fields:
            lines.extend(
                [
                    f"### `{field['field_id']}`",
                    "",
                    f"- Evidence required: `{field['evidence_required']}`",
                    f"- Evidence strength: `{field['evidence_strength']}`",
                    f"- Advisory minimum: `{field['advisory_minimum_strength']}`",
                    f"- Gap reason: {field['gap_reason']}",
                    f"- Source ref: `{field['source_ref']}`" if field.get("source_ref") else "- Source ref: none",
                    (
                        f"- Workspace artifacts: {', '.join(f'`{artifact}`' for artifact in field['workspace_artifacts'])}"
                        if field["workspace_artifacts"]
                        else "- Workspace artifacts: none"
                    ),
                    f"- Review routing required: {'yes' if field['review_routing_required'] else 'no'}",
                    "",
                ]
            )
    else:
        lines.append("- none")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def evidence_workspace(
    workspace_path: Path,
    *,
    project_root: Path | None = None,
    evidence_on: date | None = None,
) -> dict[str, Any]:
    project_root = project_root or resolve_project_root()
    snapshot = build_workspace_snapshot(
        workspace_path,
        project_root=project_root,
        snapshot_on=evidence_on,
        write_pipeline_outputs=False,
    )
    payload = build_evidence_status_from_snapshot(snapshot, project_root=project_root)

    reports_dir = Path(snapshot["workspace"]) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(reports_dir / "evidence_status.yaml", payload)
    _write_evidence_status_md(reports_dir / "evidence_status.md", payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate advisory evidence status for an intake workspace.",
    )
    parser.add_argument("workspace_path", help="Workspace directory to evaluate.")
    parser.add_argument(
        "--date",
        dest="evidence_on",
        type=_parse_cli_date,
        help="Fixed evidence date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()

    result = evidence_workspace(
        Path(args.workspace_path),
        evidence_on=args.evidence_on,
    )
    print(
        yaml.safe_dump(
            {
                "object_id": result["object_id"],
                "evidence_at": result["evidence_at"],
                "selected_field_count": result["summary"]["selected_field_count"],
                "advisory_gap_count": result["summary"]["advisory_gap_count"],
                "review_routing_required_count": result["summary"]["review_routing_required_count"],
                "reports": {
                    "yaml": "reports/evidence_status.yaml",
                    "markdown": "reports/evidence_status.md",
                },
            },
            sort_keys=False,
            allow_unicode=True,
        )
    )


if __name__ == "__main__":
    main()
