"""Plugin metadata structures used for registration and navigation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from ..utils import normalize_keywords, slugify


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Describe a plugin so the UI and analytics can reason about it."""

    plugin_id: str
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "Community"
    category: str = "General"
    keywords: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:  # pragma: no cover - dataclass hook
        normalized_id = slugify(self.plugin_id)
        if normalized_id != self.plugin_id:
            object.__setattr__(self, "plugin_id", normalized_id)
        keywords = normalize_keywords(self.keywords)
        object.__setattr__(self, "keywords", keywords)

    @property
    def search_blob(self) -> str:
        """Return a lower-case search blob for quick filtering. O(k)."""

        parts = [
            self.plugin_id,
            self.name.lower(),
            self.description.lower(),
            self.category.lower(),
            " ".join(self.keywords),
        ]
        return " ".join(parts)
