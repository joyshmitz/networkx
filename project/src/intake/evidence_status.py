"""Legacy compatibility wrapper for the canonical evidence_status module."""

from network_methodology_sandbox.intake.evidence_status import *  # type: ignore[F403]
from network_methodology_sandbox.intake.evidence_status import _load_evidence_policy, main


if __name__ == "__main__":
    main()
