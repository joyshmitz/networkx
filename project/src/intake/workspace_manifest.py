"""Maintain a workspace-local manifest for generated intake artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from model_utils import load_yaml, write_yaml

WORKSPACE_MANIFEST_SCHEMA_VERSION = "0.1.0"
REQUIRED_ARTIFACT_KEYS = {"producer", "artifact_type", "format", "path"}


def _relative_manifest_path(path: Path, workspace: Path) -> str:
    resolved_path = path.resolve()
    resolved_workspace = workspace.resolve()
    try:
        return str(resolved_path.relative_to(resolved_workspace))
    except ValueError as exc:
        raise ValueError(
            f"Workspace manifest artifacts must stay under workspace: {resolved_path}"
        ) from exc


def _artifact_path_exists(workspace: Path, path_str: str) -> bool:
    candidate = Path(path_str)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    return candidate.exists()


def _normalize_artifact(
    workspace: Path,
    artifact: dict[str, Any],
) -> dict[str, Any]:
    missing_keys = REQUIRED_ARTIFACT_KEYS - set(artifact)
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise KeyError(f"Workspace manifest artifact is missing required keys: {missing}")

    normalized = {
        "producer": artifact["producer"],
        "artifact_type": artifact["artifact_type"],
        "format": artifact["format"],
        "path": _relative_manifest_path(Path(artifact["path"]), workspace),
    }
    if normalized["path"] == "reports/workspace.manifest.yaml":
        raise ValueError("Workspace manifest artifacts must not register workspace.manifest.yaml")
    if not _artifact_path_exists(workspace, normalized["path"]):
        raise FileNotFoundError(
            f"Workspace manifest artifact path does not exist: {normalized['path']}"
        )

    for key in sorted(set(artifact) - {"path"}):
        if key in normalized:
            continue
        normalized[key] = artifact[key]
    return normalized


def _artifact_sort_key(artifact: dict[str, Any]) -> tuple[str, ...]:
    return (
        artifact["producer"],
        artifact["artifact_type"],
        artifact["path"],
        str(artifact.get("person_id") or ""),
    )


def _summary_counts(artifacts: list[dict[str, Any]]) -> dict[str, dict[str, int] | int]:
    by_producer: dict[str, int] = {}
    by_format: dict[str, int] = {}
    for artifact in artifacts:
        by_producer[artifact["producer"]] = by_producer.get(artifact["producer"], 0) + 1
        by_format[artifact["format"]] = by_format.get(artifact["format"], 0) + 1
    return {
        "artifact_count": len(artifacts),
        "by_producer": by_producer,
        "by_format": by_format,
    }


def refresh_workspace_manifest(
    workspace_path: Path,
    *,
    object_id: str,
    date_used: str,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    workspace = workspace_path.resolve()
    reports_dir = workspace / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = reports_dir / "workspace.manifest.yaml"

    existing_payload: dict[str, Any] = {}
    if manifest_path.exists():
        existing_payload = load_yaml(manifest_path)
        existing_object_id = existing_payload.get("object_id")
        if existing_object_id and existing_object_id != object_id:
            raise ValueError(
                f"Workspace manifest object_id mismatch: existing={existing_object_id!r} "
                f"new={object_id!r}"
            )

    normalized_artifacts = [
        _normalize_artifact(workspace, artifact)
        for artifact in artifacts
    ]
    producers_to_replace = {artifact["producer"] for artifact in normalized_artifacts}

    retained_artifacts: list[dict[str, Any]] = []
    for artifact in existing_payload.get("artifacts", []):
        if artifact.get("producer") in producers_to_replace:
            continue
        if not _artifact_path_exists(workspace, artifact["path"]):
            continue
        retained_artifacts.append(artifact)

    merged_artifacts = sorted(
        [*retained_artifacts, *normalized_artifacts],
        key=_artifact_sort_key,
    )

    payload = {
        "schema_version": WORKSPACE_MANIFEST_SCHEMA_VERSION,
        "manifest_at": date_used,
        "date_used": date_used,
        "object_id": object_id,
        "workspace": workspace.name,
        "artifacts": merged_artifacts,
        "summary": _summary_counts(merged_artifacts),
    }
    write_yaml(manifest_path, payload)
    return payload
