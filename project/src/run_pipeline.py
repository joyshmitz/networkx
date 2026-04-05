"""Legacy compatibility wrapper for the canonical run_pipeline module."""

from network_methodology_sandbox.run_pipeline import *  # type: ignore[F403]
from network_methodology_sandbox.run_pipeline import _manifest_path, main


if __name__ == "__main__":
    main()
