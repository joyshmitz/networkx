"""Canonical namespace wrapper for the top-level run_pipeline module."""

from run_pipeline import *  # type: ignore[F403]
from run_pipeline import main


if __name__ == "__main__":
    main()
