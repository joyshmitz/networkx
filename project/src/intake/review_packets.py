"""Legacy compatibility wrapper for the canonical review_packets module."""

from network_methodology_sandbox.intake.review_packets import *  # type: ignore[F403]
from network_methodology_sandbox.intake.review_packets import main


if __name__ == "__main__":
    main()
