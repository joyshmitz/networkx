"""Legacy compatibility wrapper for the canonical generate_network_volume_summary module."""

from network_methodology_sandbox.reports.generate_network_volume_summary import *  # type: ignore[F403]
from network_methodology_sandbox.reports.generate_network_volume_summary import main


if __name__ == "__main__":
    main()
