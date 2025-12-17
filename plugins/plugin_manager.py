from __future__ import annotations

import importlib.util
import logging
import os
import sys
import time
from dataclasses import dataclass
from types import ModuleType
from typing import Iterable, List, Tuple

from utils.diagnostics import increment_usage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PluginLoadResult:
    """Outcome of a plugin load attempt."""

    name: str
    path: str
    success: bool
    duration: float
    error: str | None = None


def get_plugins_dir(default_dir: str = "plugins") -> str:
    if getattr(sys, "frozen", False):
        # When running as an executable, use the folder alongside the exe.
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, default_dir)


def _iter_plugin_candidates(plugins_dir: str) -> Iterable[Tuple[str, str]]:
    """Yield safe plugin module names and paths, enforcing directory boundaries."""

    base_dir = os.path.realpath(plugins_dir)
    try:
        entries = sorted(os.listdir(plugins_dir))
    except FileNotFoundError:
        logger.info("No plugins directory found at '%s'.", plugins_dir)
        return []

    for filename in entries:
        if (
            not filename.endswith(".py")
            or filename.startswith("_")
            or filename == "plugin_manager.py"
        ):
            continue
        module_path = os.path.join(plugins_dir, filename)
        if not os.path.isfile(module_path):
            continue
        resolved_path = os.path.realpath(module_path)
        if os.path.commonpath([base_dir, resolved_path]) != base_dir:
            logger.warning(
                "Refusing to load plugin outside plugins_dir: %s", resolved_path
            )
            continue
        module_name = os.path.splitext(filename)[0]
        yield module_name, resolved_path


def _load_module(module_name: str, module_path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot create spec for plugin {module_name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_single_plugin(api, module_name: str, module_path: str) -> PluginLoadResult:
    start = time.perf_counter()
    success = False
    error_message: str | None = None
    try:
        module = _load_module(module_name, module_path)
        manifest = getattr(module, "PLUGIN_MANIFEST", None)
        if manifest:
            api.begin_registration(manifest)
        register = getattr(module, "register_plugin", None)
        if not callable(register):
            raise AttributeError(
                f"Plugin '{module_name}' must define a callable register_plugin(api)"
            )
        register(api)
        increment_usage(f"plugin_loaded:{module_name}")
        logger.info("Plugin '%s' loaded successfully.", module_name)
        success = True
    except Exception as exc:  # noqa: BLE001
        error_message = str(exc)
        logger.error("Error loading plugin '%s': %s", module_name, exc, exc_info=True)
    finally:
        try:
            api.end_registration()
        except Exception:  # pragma: no cover - defensive cleanup
            logger.debug("Plugin cleanup failed for %s", module_name, exc_info=True)

    duration = time.perf_counter() - start
    return PluginLoadResult(
        name=module_name,
        path=module_path,
        success=success,
        duration=duration,
        error=error_message,
    )


def load_plugins(agent, plugins_dir: str | None = None) -> List[PluginLoadResult]:
    if plugins_dir is None:
        plugins_dir = get_plugins_dir()
    api = agent.api
    results: List[PluginLoadResult] = []
    for module_name, module_path in _iter_plugin_candidates(plugins_dir):
        results.append(_load_single_plugin(api, module_name, module_path))
    if not results:
        logger.info("No plugins were loaded from %s", plugins_dir)
    return results
