"""Legacy compatibility wrapper for the canonical init_workspace module."""

from network_methodology_sandbox.intake.init_workspace import *  # type: ignore[F403]
from network_methodology_sandbox.intake.init_workspace import main


if __name__ == "__main__":
    main()
