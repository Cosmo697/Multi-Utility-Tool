"""Dependency health checks for runtime readiness.

The checks rely on ``importlib.metadata`` and ``importlib.util`` to avoid eager
imports and keep memory overhead low. Complexity: O(n) over declared
dependencies.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DependencyStatus:
    """Outcome of a dependency probe."""

    name: str
    required: bool
    installed: bool
    version: str | None
    message: str


def _probe_dependency(name: str, required: bool) -> DependencyStatus:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return DependencyStatus(
            name=name,
            required=required,
            installed=False,
            version=None,
            message="Not installed",
        )
    try:
        version = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        version = None
    return DependencyStatus(
        name=name,
        required=required,
        installed=True,
        version=version,
        message="OK" if version else "Installed (version unknown)",
    )


def check_dependencies(dependencies: Iterable[tuple[str, bool]]) -> list[DependencyStatus]:
    """Evaluate dependency availability.

    Args:
        dependencies: Iterable of ``(name, required)`` tuples.
    Returns:
        List of :class:`DependencyStatus` entries.
    """

    return [_probe_dependency(name, required) for name, required in dependencies]


def summarize_failures(statuses: Sequence[DependencyStatus]) -> list[str]:
    """Summarize missing required dependencies for logging/UI surfacing."""

    return [f"Missing required dependency: {status.name}" for status in statuses if status.required and not status.installed]
