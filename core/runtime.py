"""Runtime configuration helpers for production-safe launches.

All validation paths run in ``O(1)`` relative to the number of provided CLI
arguments. File-system interactions are limited to a single realpath call for
the plugin directory to avoid excess I/O overhead.
"""

from __future__ import annotations

import argparse
import logging
import os
import signal
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from core.app_core import AppCore

_LOG_LEVELS: Mapping[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def _validate_log_level(value: str | int) -> int:
    if isinstance(value, int):
        if value < 0:
            raise ValueError("Log level must be non-negative")
        return value
    normalized = value.strip().upper()
    if normalized not in _LOG_LEVELS:
        raise ValueError(f"Unsupported log level: {value}")
    return _LOG_LEVELS[normalized]


def _validate_plugin_dir(path_str: str | None) -> Path | None:
    if not path_str:
        return None
    candidate = Path(path_str).expanduser()
    if not candidate.exists():
        raise ValueError(f"Plugin directory does not exist: {candidate}")
    if not candidate.is_dir():
        raise ValueError(f"Plugin path is not a directory: {candidate}")
    resolved = candidate.resolve()
    return resolved


@dataclass(frozen=True)
class RuntimeConfig:
    """Validated runtime configuration derived from environment and CLI."""

    headless: bool = False
    enable_hotkeys: bool = True
    enable_tray: bool = True
    worker_count: int | None = None
    plugin_dir: Path | None = None
    log_level: int = logging.INFO

    @classmethod
    def from_env_and_args(cls, argv: Iterable[str] | None = None) -> "RuntimeConfig":
        parser = argparse.ArgumentParser(description="Launch the Multi-Utility Tool")
        parser.add_argument("--headless", action="store_true", help="Run without the GUI")
        parser.add_argument(
            "--no-hotkeys", action="store_true", help="Disable global hotkey registration"
        )
        parser.add_argument("--no-tray", action="store_true", help="Disable system tray icon")
        parser.add_argument(
            "--workers",
            type=int,
            default=None,
            help="Override the TaskManager worker pool size (positive int)",
        )
        parser.add_argument(
            "--plugin-dir",
            type=str,
            default=os.getenv("MUT_PLUGIN_DIR"),
            help="Custom plugin directory (defaults to bundled plugins)",
        )
        parser.add_argument(
            "--log-level",
            type=str,
            default=os.getenv("MUT_LOG_LEVEL", "INFO"),
            help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        )
        args = parser.parse_args(list(argv) if argv is not None else None)

        if args.workers is not None and args.workers <= 0:
            raise ValueError("workers must be a positive integer when provided")

        plugin_dir = _validate_plugin_dir(args.plugin_dir)
        log_level = _validate_log_level(args.log_level)

        return cls(
            headless=bool(args.headless),
            enable_hotkeys=not bool(args.no_hotkeys),
            enable_tray=not bool(args.no_tray),
            worker_count=args.workers,
            plugin_dir=plugin_dir,
            log_level=log_level,
        )

    def create_app(self) -> AppCore:
        """Instantiate :class:`AppCore` using the validated configuration."""

        return AppCore(
            headless=self.headless,
            enable_hotkeys=self.enable_hotkeys,
            enable_tray=self.enable_tray,
            worker_count=self.worker_count,
            load_plugins=True,
            log_level=self.log_level,
            plugin_dir=str(self.plugin_dir) if self.plugin_dir else None,
        )


def install_signal_handlers(app: AppCore) -> None:
    """Wire SIGINT/SIGTERM to a graceful shutdown path."""

    def _handle_signal(signum, _frame):  # pragma: no cover - exercised in runtime
        logging.getLogger(__name__).info("Received signal %s; shutting down", signum)
        app.shutdown()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

