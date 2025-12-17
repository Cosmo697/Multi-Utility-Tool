"""Public API exposed to plugins for UI and task orchestration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Optional

from tkinter import ttk

from .plugin_manifest import PluginManifest

logger = logging.getLogger(__name__)


class PluginAPI:
    def __init__(self, app):
        self.app = app
        self._current_manifest: PluginManifest | None = None

    # Registration helpers -------------------------------------------------
    def begin_registration(self, manifest: Any) -> None:
        self._current_manifest = self._coerce_manifest(manifest)

    def end_registration(self) -> None:
        self._current_manifest = None

    def add_tab(
        self,
        title: str,
        frame,
        *,
        manifest: PluginManifest | Dict[str, Any] | None = None,
        description: str | None = None,
        category: str = "General",
        keywords: Iterable[str] | None = None,
        version: str | None = None,
        author: str | None = None,
    ) -> PluginManifest:
        manifest_obj = self._merge_manifest(
            title,
            manifest or self._current_manifest,
            description,
            category,
            keywords,
            version,
            author,
        )
        self.app.add_plugin_tab(
            title,
            frame,
            manifest=manifest_obj,
            description=manifest_obj.description,
            category=manifest_obj.category,
            keywords=manifest_obj.keywords,
            version=manifest_obj.version,
            author=manifest_obj.author,
        )
        return manifest_obj

    def create_plugin_frame(
        self,
        manifest: PluginManifest | Dict[str, Any],
        *,
        container=None,
    ):
        manifest_obj = self._coerce_manifest(manifest)
        parent = container or self.app.notebook
        frame = ttk.Frame(parent)
        self.add_tab(manifest_obj.name, frame, manifest=manifest_obj)
        return frame

    def register_hook(self, hook_name, callback):
        self.app.hooks.register(hook_name, callback)

    def trigger_hook(self, hook_name, *args, **kwargs):
        self.app.hooks.trigger(hook_name, *args, **kwargs)

    def collect(self, hook_name, *args, **kwargs):
        return self.app.hooks.collect(hook_name, *args, **kwargs)

    # Task orchestration ---------------------------------------------------
    def submit_task(
        self,
        name: str,
        func,
        *,
        args: Iterable[Any] | None = None,
        kwargs: Optional[Dict[str, Any]] = None,
        retries: int = 1,
        retry_backoff: float = 0.5,
        timeout: float | None = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback=None,
    ):
        logger.info("Submitting background task %s", name)
        return self.app.tasks.submit(
            name,
            func,
            args=args,
            kwargs=kwargs,
            retries=retries,
            retry_backoff=retry_backoff,
            timeout=timeout,
            metadata=metadata,
            progress_callback=progress_callback,
            on_error=self.report_error,
        )

    def notify_status(self, message: str) -> None:
        logger.info("Plugin status: %s", message)
        self.app.ui.queue.put((None, "status", message))

    def notify_done(self, message: str) -> None:
        self.app.ui.queue.put((None, "done", message))

    def report_error(self, exc: Exception) -> None:
        logger.error("Plugin error: %s", exc, exc_info=True)
        self.app.ui.queue.put((None, "error", str(exc)))

    def get_main_window(self):
        return self.app.root

    # Internal helpers -----------------------------------------------------
    def _coerce_manifest(self, manifest: Any) -> PluginManifest:
        if isinstance(manifest, PluginManifest):
            return manifest
        if isinstance(manifest, dict):
            return PluginManifest(**manifest)
        raise TypeError("Manifest must be PluginManifest or dict")

    def _merge_manifest(
        self,
        title: str,
        manifest: PluginManifest | None,
        description: str | None,
        category: str,
        keywords: Iterable[str] | None,
        version: str | None,
        author: str | None,
    ) -> PluginManifest:
        if manifest is None:
            return PluginManifest(
                plugin_id=title,
                name=title,
                description=description or f"{title} tools",
                category=category,
                keywords=tuple(keywords or ()),
                version=version or "1.0.0",
                author=author or "Community",
            )
        return PluginManifest(
            plugin_id=manifest.plugin_id or title,
            name=manifest.name or title,
            description=description or manifest.description,
            category=manifest.category or category,
            keywords=manifest.keywords or tuple(keywords or ()),
            version=version or manifest.version,
            author=author or manifest.author,
        )
