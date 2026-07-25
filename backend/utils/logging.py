"""Logging configuration for the CodeAtlas backend."""

import logging
import sys

LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging with a consistent format.

    Safe to call more than once; ``force=True`` replaces any handlers
    installed by earlier calls or by libraries.
    """
    logging.basicConfig(
        level=level.upper(),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )
