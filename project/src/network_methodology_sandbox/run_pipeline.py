"""Canonical namespace wrapper for the top-level run_pipeline module."""

from run_pipeline import *  # type: ignore[F403]
from run_pipeline import _manifest_path, main


if __name__ == "__main__":
    main()
