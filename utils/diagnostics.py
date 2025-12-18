"""Utilities for lightweight diagnostics, timing, and metrics emission.

Hot path complexity: usage increments are ``O(1)`` and metrics emission writes
single JSON lines to avoid buffering large payloads in memory.
"""

import logging
import json
from pathlib import Path
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Mapping

logger = logging.getLogger("diagnostics")

_usage_counts = {}


def increment_usage(name: str) -> None:
    """Increment usage count for the given operation."""
    _usage_counts[name] = _usage_counts.get(name, 0) + 1
    logger.debug("Usage %s -> %d", name, _usage_counts[name])


def get_usage_stats() -> dict:
    """Return a copy of the current usage statistics."""
    return dict(_usage_counts)


def emit_metrics_snapshot(
    *,
    path: str | Path = "logs/metrics.jsonl",
    extra: Mapping[str, Any] | None = None,
) -> dict:
    """Persist a metrics snapshot to a JSONL file.

    Metrics are appended to avoid rewriting the file and to keep I/O streaming
    friendly for production usage. The payload always includes an ISO8601 UTC
    timestamp and the current usage counters.
    """

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "usage": get_usage_stats(),
    }
    if extra:
        payload.update(dict(extra))

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False))
        handle.write("\n")
    logger.debug("Metrics snapshot written to %s", target)
    return payload


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
