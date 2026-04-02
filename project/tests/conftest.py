import sys
from datetime import date, datetime, timezone
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Single source of truth for the fixed exemplar date used across all intake tests.
GOLDEN_DATE = date(2026, 4, 2)
GOLDEN_DATETIME_UTC = datetime(GOLDEN_DATE.year, GOLDEN_DATE.month, GOLDEN_DATE.day, tzinfo=timezone.utc)


def copy_workspace(tmp_path: Path, exemplar_workspace: Path) -> Path:
    workspace = tmp_path / exemplar_workspace.name
    shutil.copytree(exemplar_workspace, workspace)
    return workspace
