"""Text utilities supporting consistent naming and validation."""

from __future__ import annotations

import re
from typing import Iterable, Tuple

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Return a lowercase, hyphen-delimited slug for *value*.

    The function keeps alphanumeric characters, replaces other sequences with
    single hyphens, and strips leading/trailing hyphens. Complexity: O(n).
    """

    if not isinstance(value, str):  # pragma: no cover - defensive programming
        raise TypeError("slugify expects a string input")
    normalized = value.strip().lower()
    normalized = _SLUG_PATTERN.sub("-", normalized)
    normalized = normalized.strip("-")
    return normalized or "plugin"


def normalize_keywords(values: Iterable[str] | None) -> Tuple[str, ...]:
    """Normalize keyword collection into a tuple of unique slugs."""

    if not values:
        return ()
    seen: set[str] = set()
    result: list[str] = []
    for raw in values:
        if not raw:
            continue
        slug = slugify(str(raw))
        if slug and slug not in seen:
            seen.add(slug)
            result.append(slug)
    return tuple(result)
