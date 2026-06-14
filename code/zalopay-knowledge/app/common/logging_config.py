from __future__ import annotations

"""Central logging configuration."""

import logging
import sys

from app.config import get_settings


class _HealthPathFilter(logging.Filter):
    """Drop uvicorn access-log entries for health-check paths."""

    _PATHS = ("/health", "/health/live", "/health/ready")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(p in msg for p in self._PATHS)


def setup_logging() -> None:
    """Configure root logger from ``LOG_LEVEL`` in settings."""
    level_name = get_settings().log_level.upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        stream=sys.stdout,
        force=True,
    )
    # Suppress noisy health-probe access log lines from uvicorn.
    _health_filter = _HealthPathFilter()
    for _name in ("uvicorn.access", "uvicorn"):
        logging.getLogger(_name).addFilter(_health_filter)
