"""Canonical namespace wrapper for intake.compile_intake."""

from intake.compile_intake import *  # type: ignore[F403]
from intake.compile_intake import _count_statuses, main


if __name__ == "__main__":
    main()
