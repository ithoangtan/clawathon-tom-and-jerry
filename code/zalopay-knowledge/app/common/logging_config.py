from __future__ import annotations

"""Central logging configuration."""

import logging
import sys

from app.config import get_settings


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
