"""Legacy compatibility wrapper for the canonical generate_intake_sheets module."""

from network_methodology_sandbox.intake.generate_intake_sheets import *  # type: ignore[F403]
from network_methodology_sandbox.intake.generate_intake_sheets import _load_yaml, main


if __name__ == "__main__":
    main()
