"""Lightweight integration tests covering headless registration flows."""

from __future__ import annotations

from core.app_core import AppCore
from core.plugin_manifest import PluginManifest


def test_headless_plugin_registration():
    app = AppCore(headless=True, enable_hotkeys=False, enable_tray=False, load_plugins=False)
    manifest = PluginManifest(
        plugin_id="stub",
        name="Stub Plugin",
        description="Synthetic plugin for integration testing.",
        category="Testing",
        keywords=("test",),
        version="0.1.0",
        author="QA",
    )
    app.add_plugin_tab(manifest.name, object(), manifest=manifest)
    assert "stub" in app.plugins.manifests
    app.shutdown()
