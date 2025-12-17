"""Application core wiring agents, plugins, and infrastructure together."""

from __future__ import annotations

import logging
from typing import Iterable, Sequence

from ..agents.hotkey_agent import HotkeyAgent
from ..agents.logger_agent import LoggerAgent
from ..agents.null_agents import NullHotkeyAgent, NullTrayAgent
from ..agents.plugin_agent import PluginAgent
from ..agents.tray_agent import TrayAgent
from ..agents.ui_agent import UIAgent
from ..utils.health_checks import DependencyStatus, check_dependencies, summarize_failures
from .plugin_manifest import PluginManifest
from .task_manager import TaskManager

logger = logging.getLogger(__name__)


class AppCore:
    """Central coordinator that wires individual agents together."""

    REQUIRED_DEPENDENCIES: Sequence[str] = ("yaml", "requests")
    OPTIONAL_DEPENDENCIES: Sequence[str] = ("keyboard", "pystray", "tkinterdnd2")

    def __init__(
        self,
        *,
        headless: bool = False,
        enable_hotkeys: bool = True,
        enable_tray: bool = True,
        worker_count: int | None = None,
        load_plugins: bool = True,
        dependencies: Sequence[tuple[str, bool]] | None = None,
    ) -> None:
        self.logger_agent = LoggerAgent()
        self.logger = logging.getLogger("app")
        self.tasks = TaskManager(max_workers=worker_count)
        self.headless = headless
        self.threads: list = []
        self.dependency_statuses: list[DependencyStatus] = []
        self.dependency_failures: list[str] = []

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
        self._run_dependency_checks(dependencies)
        logger.info("App core initialized")

    def register_thread(self, thread) -> None:
        self.threads.append(thread)

    def _run_dependency_checks(
        self, dependencies: Sequence[tuple[str, bool]] | None = None
    ) -> None:
        """Execute startup dependency checks and surface any critical issues."""

        dependency_plan = dependencies or [
            *[(dep, True) for dep in self.REQUIRED_DEPENDENCIES],
            *[(dep, False) for dep in self.OPTIONAL_DEPENDENCIES],
        ]
        self.dependency_statuses = check_dependencies(dependency_plan)
        self.dependency_failures = summarize_failures(self.dependency_statuses)

        for status in self.dependency_statuses:
            level = logger.info if status.installed else logger.warning
            level(
                "Dependency %s (%s): %s",
                status.name,
                "required" if status.required else "optional",
                status.message,
            )

        if self.dependency_failures:
            for message in self.dependency_failures:
                logger.error(message)
            self._notify_missing_dependencies(self.dependency_failures)

        missing_optional = [s.name for s in self.dependency_statuses if not s.required and not s.installed]
        if missing_optional:
            logger.info("Optional features downgraded; missing: %s", ", ".join(sorted(missing_optional)))

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

    def _notify_missing_dependencies(self, messages: Sequence[str]) -> None:
        """Surface dependency issues via UI/tray when available while staying resilient in headless/test modes."""

        combined = "; ".join(messages)
        if self.headless:
            logger.warning("Headless mode: %s", combined)
            return

        try:
            self.ui.queue.put((self, "toast", combined))
        except Exception:  # pragma: no cover - guard against UI failures
            logger.debug("Failed to enqueue UI notification", exc_info=True)

        try:
            if hasattr(self.tray, "notify"):
                self.tray.notify(combined)
        except Exception:  # pragma: no cover - guard against platform-specific tray issues
            logger.debug("Failed to send tray notification", exc_info=True)

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
