"""Tests for the TaskManager concurrency helper."""

from __future__ import annotations

import time

import pytest

from multi_utility_tool.core.task_manager import (
    TaskCancelledError,
    TaskManager,
    TaskTimeoutError,
)


def test_task_manager_completes_simple_task():
    manager = TaskManager(max_workers=2)

    def work():
        return 21 * 2

    handle = manager.submit("simple", work)
    assert handle.result(timeout=1) == 42
    manager.shutdown()


def test_task_manager_retries(monkeypatch):
    manager = TaskManager(max_workers=1)
    attempts = {"count": 0}

    def flaky():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("boom")
        return "ok"

    handle = manager.submit("flaky", flaky, retries=2, retry_backoff=0.01)
    assert handle.result(timeout=2) == "ok"
    assert attempts["count"] == 2
    manager.shutdown()


def test_task_manager_timeout():
    manager = TaskManager(max_workers=1)

    def slow_task():
        time.sleep(0.05)
        return 1

    handle = manager.submit("slow", slow_task, timeout=0.01)
    with pytest.raises(TaskTimeoutError):
        handle.result(timeout=1)
    manager.shutdown()


def test_task_manager_cancellation():
    manager = TaskManager(max_workers=1)

    def blocking(cancel_event=None):
        while not cancel_event.is_set():
            time.sleep(0.01)
        raise TaskCancelledError("cancel requested")

    handle = manager.submit("block", blocking)
    time.sleep(0.03)
    manager.cancel(handle.spec.task_id)
    with pytest.raises(TaskCancelledError):
        handle.result(timeout=1)
    manager.shutdown()
