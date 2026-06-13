from __future__ import annotations

"""PingPort — minimal liveness interface.

Used by the ``/health`` endpoint and AgentBase ``@app.ping`` handler to
confirm the application process is alive and its core dependencies are
reachable.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class PingPort(Protocol):
    """Simple liveness check interface."""

    def healthy(self) -> bool:
        """Return True when this component is alive and ready to serve.

        Must not raise.  Must return within ~1 second (called on every health
        check and should not block the event loop for long).
        """
        ...
