"""Fallback agents used when optional integrations are disabled."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class NullHotkeyAgent:
    """No-op hotkey agent for headless or disabled environments."""

    def __init__(self, app) -> None:
        self.app = app

    def add_hotkey(self, *_args, **_kwargs) -> None:
        logger.debug("Hotkeys disabled; add_hotkey ignored")

    def remove_hotkey(self, *_args, **_kwargs) -> None:
        logger.debug("Hotkeys disabled; remove_hotkey ignored")

    def open_manager(self) -> None:
        logger.info("Hotkey manager is unavailable in this mode")


class _NullIcon:
    def stop(self) -> None:  # pragma: no cover - trivial
        logger.debug("Tray icon stop ignored")


class NullTrayAgent:
    """No-op tray agent for environments without system tray access."""

    def __init__(self, app) -> None:
        self.app = app
        self.icon = _NullIcon()

    def show(self) -> None:
        logger.debug("Tray disabled; show ignored")

    def notify(self, message: str) -> None:
        logger.info("Tray notification suppressed: %s", message)
