"""Legacy compatibility wrapper for the canonical compile_intake module."""

from network_methodology_sandbox.intake.compile_intake import *  # type: ignore[F403]
from network_methodology_sandbox.intake.compile_intake import (
    _build_questionnaire,
    _check_conflicts,
    _count_statuses,
    _derive_status,
    _parse_value,
    _validate_values,
    main,
)


if __name__ == "__main__":
    main()
