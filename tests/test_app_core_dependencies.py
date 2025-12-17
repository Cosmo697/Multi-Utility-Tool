from __future__ import annotations

from queue import Queue

import pytest

from core import app_core as app_core_module
from core.app_core import AppCore
from utils.health_checks import DependencyStatus


class DummyRoot:
    def after(self, *_args, **_kwargs):
        return None


class DummyUI:
    def __init__(self, app, headless: bool = False):
        self.app = app
        self.headless = headless
        self.queue: Queue = Queue()
        self.root = DummyRoot()
        self.notebook = None

    def attach(self) -> None:
        return None


class DummyTray:
    def __init__(self, app):
        self.app = app
        self.notifications: list[str] = []

    def notify(self, message: str) -> None:
        self.notifications.append(message)


@pytest.fixture(autouse=True)
def patch_ui_and_tray(monkeypatch):
    monkeypatch.setattr(app_core_module, "UIAgent", DummyUI)
    monkeypatch.setattr(app_core_module, "TrayAgent", DummyTray)


def test_dependency_check_healthy(monkeypatch):
    statuses = [
        DependencyStatus("dep_a", True, True, "1.0.0", "OK"),
        DependencyStatus("dep_b", False, True, "2.0.0", "OK"),
    ]
    monkeypatch.setattr(app_core_module, "check_dependencies", lambda deps: statuses)

    app = AppCore(
        headless=True,
        enable_hotkeys=False,
        enable_tray=False,
        load_plugins=False,
    )

    assert app.dependency_statuses == statuses
    assert app.dependency_failures == []


def test_dependency_check_missing_required(monkeypatch):
    statuses = [
        DependencyStatus("critical", True, False, None, "Not installed"),
        DependencyStatus("optional", False, True, "1.0.0", "OK"),
    ]
    monkeypatch.setattr(app_core_module, "check_dependencies", lambda deps: statuses)

    app = AppCore(
        headless=False,
        enable_hotkeys=False,
        enable_tray=True,
        load_plugins=False,
    )

    assert app.dependency_failures == ["Missing required dependency: critical"]
    queued = list(app.ui.queue.queue)
    assert queued and queued[0][1] == "toast"
    assert app.tray.notifications == ["Missing required dependency: critical"]


def test_dependency_check_missing_optional(monkeypatch):
    statuses = [
        DependencyStatus("dep_a", True, True, "1.0.0", "OK"),
        DependencyStatus("opt", False, False, None, "Not installed"),
    ]
    monkeypatch.setattr(app_core_module, "check_dependencies", lambda deps: statuses)

    app = AppCore(
        headless=True,
        enable_hotkeys=False,
        enable_tray=False,
        load_plugins=False,
    )

    assert app.dependency_failures == []
    assert any(not status.required and not status.installed for status in app.dependency_statuses)
