"""Application core wiring agents, plugins, and infrastructure together."""

from __future__ import annotations

import logging
from typing import Iterable

from agents.hotkey_agent import HotkeyAgent
from agents.logger_agent import LoggerAgent
from agents.plugin_agent import PluginAgent
from agents.tray_agent import TrayAgent
from agents.ui_agent import UIAgent
from agents.null_agents import NullHotkeyAgent, NullTrayAgent
from core.plugin_manifest import PluginManifest
from core.task_manager import TaskManager

logger = logging.getLogger(__name__)


class AppCore:
    """Central coordinator that wires individual agents together."""

    def __init__(
        self,
        *,
        headless: bool = False,
        enable_hotkeys: bool = True,
        enable_tray: bool = True,
        worker_count: int | None = None,
        load_plugins: bool = True,
    ) -> None:
        self.logger_agent = LoggerAgent()
        self.logger = logging.getLogger("app")
        self.tasks = TaskManager(max_workers=worker_count)
        self.headless = headless
        self.threads: list = []

        self.ui = UIAgent(self, headless=headless)
        self.root = self.ui.root
        self.notebook = self.ui.notebook  # Expose notebook for legacy plugins
        self.plugins = PluginAgent(self, autoload=load_plugins)
        self.hotkeys = (
            HotkeyAgent(self) if enable_hotkeys and not headless else NullHotkeyAgent(self)
        )
        self.tray = (
            TrayAgent(self) if enable_tray and not headless else NullTrayAgent(self)
        )
        self.ui.attach()
        logger.info("App core initialized")

    def register_thread(self, thread) -> None:
        self.threads.append(thread)

    def shutdown(self) -> None:
        """Gracefully stop all background resources."""

        logger.info("Shutting down AppCore")
        self.tasks.shutdown(wait=True)
        if hasattr(self.tray, "icon") and hasattr(self.tray.icon, "stop"):
            try:
                self.tray.icon.stop()
            except Exception:  # pragma: no cover - best effort cleanup
                logger.debug("Tray stop failed", exc_info=True)
        for thread in list(self.threads):
            if thread.is_alive():
                thread.join(timeout=1.0)

    # Delegate tab addition for plugins
    def add_plugin_tab(
        self,
        title: str,
        frame,
        *,
        manifest: PluginManifest | None = None,
        description: str | None = None,
        category: str = "General",
        keywords: Iterable[str] | None = None,
        version: str = "1.0.0",
        author: str = "Community",
    ) -> PluginManifest:
        manifest = manifest or PluginManifest(
            plugin_id=title,
            name=title,
            description=description or f"{title} tools",
            category=category,
            keywords=tuple(keywords or ()),
            version=version,
            author=author,
        )
        self.ui.add_plugin_tab(manifest, frame)
        self.plugins.register_manifest(manifest)
        return manifest
