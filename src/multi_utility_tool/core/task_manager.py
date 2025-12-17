"""Threaded task execution with retries, cancellation, and progress hooks."""

from __future__ import annotations

import inspect
import logging
import os
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Optional

from ..utils.diagnostics import increment_usage

logger = logging.getLogger(__name__)


class TaskCancelledError(RuntimeError):
    """Raised when a task is cancelled before completion."""


class TaskTimeoutError(RuntimeError):
    """Raised when a task exceeds its allotted timeout."""


@dataclass(slots=True)
class TaskSpec:
    """Internal description of a submitted task."""

    task_id: str
    name: str
    func: Callable[..., Any]
    args: tuple[Any, ...]
    kwargs: Dict[str, Any]
    retries: int
    retry_backoff: float
    timeout: Optional[float]
    metadata: Dict[str, Any]

@dataclass(slots=True)
class TaskHandle:
    """Expose control over a running task."""

    spec: TaskSpec
    future: Future
    cancel_event: threading.Event

    def cancel(self) -> None:
        """Request cancellation and cancel the future if pending."""

        self.cancel_event.set()
        if not self.future.done():
            self.future.cancel()

    def done(self) -> bool:
        return self.future.done()

    def result(self, timeout: Optional[float] = None) -> Any:
        return self.future.result(timeout=timeout)


class TaskManager:
    """Coordinate execution of background tasks.

    Complexity: submission is O(1); cancellation and lookups are O(1).
    """

    def __init__(self, max_workers: Optional[int] = None) -> None:
        cpu_bound = os.cpu_count() or 4
        workers = max_workers or max(4, cpu_bound * 2)
        self._executor = ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="mut-task"
        )
        self._lock = threading.RLock()
        self._handles: Dict[str, TaskHandle] = {}
        self._shutdown = False

    def submit(
        self,
        name: str,
        func: Callable[..., Any],
        *,
        args: Iterable[Any] | None = None,
        kwargs: Optional[Dict[str, Any]] = None,
        retries: int = 0,
        retry_backoff: float = 0.5,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> TaskHandle:
        """Submit a task for execution.

        Parameters are validated for safety. The callable can optionally accept
        ``cancel_event`` and ``progress_callback`` keyword arguments, which will
        be injected automatically. The task is retried with exponential backoff.
        """

        if self._shutdown:
            raise RuntimeError("TaskManager is shut down")
        if not callable(func):
            raise TypeError("func must be callable")
        task_id = uuid.uuid4().hex
        args_tuple = tuple(args or ())
        kwargs_dict = dict(kwargs or {})
        metadata_dict = dict(metadata or {})
        spec = TaskSpec(
            task_id=task_id,
            name=name,
            func=func,
            args=args_tuple,
            kwargs=kwargs_dict,
            retries=max(0, int(retries)),
            retry_backoff=max(0.1, float(retry_backoff)),
            timeout=timeout,
            metadata=metadata_dict,
        )
        cancel_event = threading.Event()
        future = self._executor.submit(
            self._run_task,
            spec,
            cancel_event,
            progress_callback,
            on_error,
        )
        handle = TaskHandle(spec=spec, future=future, cancel_event=cancel_event)
        with self._lock:
            self._handles[task_id] = handle
        future.add_done_callback(lambda _: self._cleanup(task_id))
        logger.info("Task %s submitted", name)
        return handle

    def _cleanup(self, task_id: str) -> None:
        with self._lock:
            self._handles.pop(task_id, None)

    def _run_task(
        self,
        spec: TaskSpec,
        cancel_event: threading.Event,
        progress_callback: Optional[Callable[[float], None]],
        on_error: Optional[Callable[[Exception], None]],
    ) -> Any:
        increment_usage(f"task:{spec.name}")
        attempts = spec.retries + 1
        backoff = spec.retry_backoff
        func_signature = inspect.signature(spec.func)
        for attempt in range(1, attempts + 1):
            if cancel_event.is_set():
                logger.info("Task %s cancelled before start", spec.name)
                raise TaskCancelledError(spec.name)
            try:
                kwargs = dict(spec.kwargs)
                if "cancel_event" in func_signature.parameters:
                    kwargs.setdefault("cancel_event", cancel_event)
                if (
                    progress_callback
                    and "progress_callback" in func_signature.parameters
                ):
                    kwargs.setdefault("progress_callback", progress_callback)
                start = time.perf_counter()
                result = spec.func(*spec.args, **kwargs)
                duration = time.perf_counter() - start
                timeout = spec.timeout
                if timeout is not None and duration > timeout:
                    raise TaskTimeoutError(
                        f"Task {spec.name} exceeded timeout {timeout}s"
                    )
                logger.info(
                    "Task %s completed in %.2fs", spec.name, duration
                )
                return result
            except TaskCancelledError:
                cancel_event.set()
                logger.info("Task %s cancelled", spec.name)
                raise
            except Exception as exc:  # noqa: BLE001
                logger.exception("Task %s failed on attempt %s", spec.name, attempt)
                if cancel_event.is_set():
                    raise TaskCancelledError(spec.name) from exc
                if attempt >= attempts:
                    if on_error:
                        on_error(exc)
                    raise
                time.sleep(min(backoff, 8.0))
                backoff *= 2
        raise RuntimeError("Unreachable")

    def cancel(self, task_id: str) -> None:
        with self._lock:
            handle = self._handles.get(task_id)
        if handle:
            handle.cancel()

    def shutdown(self, wait: bool = True) -> None:
        self._shutdown = True
        with self._lock:
            handles = list(self._handles.values())
        for handle in handles:
            handle.cancel()
        self._executor.shutdown(wait=wait, cancel_futures=True)
        logger.info("TaskManager shut down")
