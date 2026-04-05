"""Legacy compatibility wrapper for the canonical compile_graphs module."""

from network_methodology_sandbox.compiler.compile_graphs import *  # type: ignore[F403]
from network_methodology_sandbox.compiler.compile_graphs import (
    _service_source_zone,
    _service_transport_zone,
    main,
)


if __name__ == "__main__":
    main()
