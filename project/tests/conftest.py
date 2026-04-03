import sys
from datetime import date, datetime, timezone
from pathlib import Path
import shutil
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Single source of truth for the fixed exemplar date used across all intake tests.
GOLDEN_DATE = date(2026, 4, 2)
GOLDEN_DATETIME_UTC = datetime(GOLDEN_DATE.year, GOLDEN_DATE.month, GOLDEN_DATE.day, tzinfo=timezone.utc)


def copy_workspace(tmp_path: Path, exemplar_workspace: Path) -> Path:
    workspace = tmp_path / exemplar_workspace.name
    shutil.copytree(exemplar_workspace, workspace)
    return workspace


def find_review_item(
    result: dict[str, Any],
    *,
    source_kind: str,
    source_key: str,
) -> dict[str, Any]:
    for item in result["review_items"]:
        if item["source_kind"] == source_kind and item["source_key"] == source_key:
            return item
    raise AssertionError(f"Missing review item for {source_kind=} {source_key=}")


def find_evidence_field(
    result: dict[str, Any],
    field_id: str,
) -> dict[str, Any]:
    for field in result["fields"]:
        if field["field_id"] == field_id:
            return field
    raise AssertionError(f"Missing evidence field {field_id!r}")
