#!/usr/bin/env python3
"""Compile intake workspace, run pipeline, and summarize baseline readiness."""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from network_methodology_sandbox.intake.workspace_snapshot import build_workspace_snapshot
from network_methodology_sandbox.intake.workspace_manifest import refresh_workspace_manifest
from network_methodology_sandbox.model_utils import write_yaml
from network_methodology_sandbox.intake.workspace_validation import IntakeCommandError


def _parse_cli_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Expected YYYY-MM-DD date, got: {raw!r}"
        ) from exc


def _write_preview_status_md(path: Path, payload: dict[str, Any]) -> None:
    compile_totals = payload["compile"]
    pipeline = payload["pipeline"]
    lines = [
        f"# Preview Status — {payload['object_id']}",
        "",
        f"- Preview date: {payload['preview_at']}",
        f"- Workspace: {payload['workspace']}",
        f"- Questionnaire: {payload['questionnaire_path']}",
        "",
        "## Compile Totals",
        "",
        "| Answered | TBD | Unanswered | N/A | Total |",
        "|----------|-----|------------|-----|-------|",
        (
            f"| {compile_totals['answered']} | {compile_totals['tbd']} "
            f"| {compile_totals['unanswered']} | {compile_totals['not_applicable']} "
            f"| {compile_totals['total']} |"
        ),
        "",
        "## Pipeline Status",
        "",
        f"- Status: {pipeline['status']}",
        f"- Errors: {pipeline['error_count']}",
        f"- Warnings: {pipeline['warning_count']}",
        f"- Confidence level: {pipeline['confidence_level']}",
        f"- Assumed fields: {pipeline['assumed_count']}",
        f"- Archetype defaults: {pipeline.get('archetype_default_count', 0)}",
        f"- Cross-field inferences: {pipeline.get('inference_count', 0)}",
        "",
        "## Baseline Ready",
        "",
        f"- baseline_ready: {'true' if payload['baseline_ready'] else 'false'}",
        "",
        "## Blockers",
        "",
    ]

    blockers = payload["blockers"]
    if blockers:
        for blocker in blockers:
            if blocker["kind"] == "pipeline_error":
                lines.append(
                    f"- pipeline_error [{blocker['validator']}]: {blocker['message']}"
                )
            else:
                lines.append(
                    f"- unresolved_s4 [{blocker['field_id']}]: status={blocker['status']}"
                )
    else:
        lines.append("- none")
    lines.append("")

    lines.extend(
        [
            "## Unresolved S4 Fields",
            "",
        ]
    )
    unresolved_s4_fields = payload["unresolved_s4_fields"]
    if unresolved_s4_fields:
        lines.append("| Field | Section | Status | Owner Role |")
        lines.append("|-------|---------|--------|------------|")
        for field in unresolved_s4_fields:
            lines.append(
                f"| {field['field_id']} | {field['section']} | {field['status']} | "
                f"{field['owner_role'] or ''} |"
            )
    else:
        lines.append("- none")
    lines.append("")

    unresolved_non_s4_fields = payload.get("unresolved_non_s4_fields", [])
    if unresolved_non_s4_fields:
        lines.extend(
            [
                "## Unresolved Non-S4 Fields",
                "",
                "| Field | Section | Strictness | Status | Owner Role |",
                "|-------|---------|------------|--------|------------|",
            ]
        )
        for field in unresolved_non_s4_fields:
            lines.append(
                f"| {field['field_id']} | {field['section']} | {field['strictness'] or ''} "
                f"| {field['status']} | {field['owner_role'] or ''} |"
            )
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def preview_workspace(
    workspace_path: Path,
    *,
    project_root: Path | None = None,
    preview_on: date | None = None,
) -> dict[str, Any]:
    snapshot = build_workspace_snapshot(
        workspace_path,
        project_root=project_root,
        snapshot_on=preview_on,
        write_pipeline_outputs=True,
        command_name="preview",
    )
    unresolved_s4_fields = snapshot["fields"]["unresolved_by_strictness"].get("S4", [])
    unresolved_non_s4_fields = [
        field
        for field in snapshot["fields"]["unresolved"]
        if field["strictness"] != "S4"
    ]
    payload: dict[str, Any] = {
        "schema_version": snapshot["schema_version"],
        "object_id": snapshot["object_id"],
        "preview_at": snapshot["snapshot_at"],
        "date_used": snapshot["date_used"],
        "workspace": snapshot["workspace"],
        "questionnaire_path": snapshot["questionnaire_path"],
        "compile": snapshot["compile"]["totals"],
        "pipeline": {
            "status": snapshot["pipeline"]["status"],
            "error_count": snapshot["pipeline"]["error_count"],
            "warning_count": snapshot["pipeline"]["warning_count"],
            "confidence_level": snapshot["pipeline"]["confidence_level"],
            "assumed_count": snapshot["pipeline"]["assumed_count"],
            "archetype_default_count": snapshot["pipeline"].get("archetype_default_count", 0),
            "inference_count": snapshot["pipeline"].get("inference_count", 0),
            "errors": snapshot["pipeline"]["errors"],
        },
        "baseline_ready": snapshot["baseline_ready"],
        "unresolved_s4_fields": unresolved_s4_fields,
        "blockers": snapshot["blockers"],
    }
    if unresolved_non_s4_fields:
        payload["unresolved_non_s4_fields"] = unresolved_non_s4_fields

    reports_dir = Path(snapshot["workspace"]) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_yaml(reports_dir / "preview_status.yaml", payload)
    _write_preview_status_md(reports_dir / "preview_status.md", payload)
    refresh_workspace_manifest(
        Path(snapshot["workspace"]),
        object_id=snapshot["object_id"],
        date_used=snapshot["date_used"],
        artifacts=[
            {
                "producer": "preview",
                "artifact_type": "preview_status",
                "format": "yaml",
                "path": reports_dir / "preview_status.yaml",
            },
            {
                "producer": "preview",
                "artifact_type": "preview_status",
                "format": "markdown",
                "path": reports_dir / "preview_status.md",
            },
        ],
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preview whether an intake workspace is baseline_ready.",
    )
    parser.add_argument("workspace_path", help="Workspace directory to preview.")
    parser.add_argument(
        "--date",
        dest="preview_on",
        type=_parse_cli_date,
        help="Fixed preview date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()

    try:
        result = preview_workspace(
            Path(args.workspace_path),
            preview_on=args.preview_on,
        )
    except IntakeCommandError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    print(
        yaml.safe_dump(
            {
                "object_id": result["object_id"],
                "baseline_ready": result["baseline_ready"],
                "error_count": result["pipeline"]["error_count"],
                "warning_count": result["pipeline"]["warning_count"],
                "unresolved_s4_count": len(result["unresolved_s4_fields"]),
                "reports": {
                    "yaml": "reports/preview_status.yaml",
                    "markdown": "reports/preview_status.md",
                },
            },
            sort_keys=False,
            allow_unicode=True,
        )
    )


if __name__ == "__main__":
    main()
