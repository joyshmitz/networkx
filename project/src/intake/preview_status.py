"""Legacy compatibility wrapper for the canonical preview_status module."""

from network_methodology_sandbox.intake.preview_status import *  # type: ignore[F403]
from network_methodology_sandbox.intake.preview_status import main


if __name__ == "__main__":
    main()
