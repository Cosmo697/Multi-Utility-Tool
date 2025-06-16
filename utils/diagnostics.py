"""Utilities for lightweight diagnostics and timing."""

import logging
import time
from contextlib import contextmanager

logger = logging.getLogger("diagnostics")

_usage_counts = {}


def increment_usage(name: str) -> None:
    """Increment usage count for the given operation."""
    _usage_counts[name] = _usage_counts.get(name, 0) + 1
    logger.debug("Usage %s -> %d", name, _usage_counts[name])


def get_usage_stats() -> dict:
    """Return a copy of the current usage statistics."""
    return dict(_usage_counts)


@contextmanager
def time_block(label: str):
    """Context manager that measures execution time of a block."""
    start = time.perf_counter()
    try:
        yield
    except Exception as exc:
        logger.exception("Error in %s", label)
        raise exc
    finally:
        duration = time.perf_counter() - start
        logger.debug("%s took %.2fs", label, duration)
