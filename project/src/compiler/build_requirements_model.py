"""Legacy compatibility wrapper for the canonical build_requirements_model module."""

from network_methodology_sandbox.compiler.build_requirements_model import *  # type: ignore[F403]
from network_methodology_sandbox.compiler.build_requirements_model import main


if __name__ == "__main__":
    main()
