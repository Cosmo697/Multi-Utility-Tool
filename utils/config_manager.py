"""YAML-backed configuration storage with validation and atomic writes.

Hot path complexity: O(n) over configuration keys during validation to ensure
all keys are strings and values are serializable.
"""

from __future__ import annotations

import logging
import os
import tempfile
from typing import Any, Mapping

import yaml

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "MultiUtilityTool")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")

logger = logging.getLogger(__name__)


def _validate_config(cfg: Any) -> dict:
    """Ensure configs are mappings with string keys.

    Returns a copy of the configuration to avoid mutating caller data. Raises a
    ``TypeError`` when the payload is not a mapping or contains non-string
    keys. Values are accepted as-is to allow flexible schemas.
    """

    if cfg is None:
        return {}
    if not isinstance(cfg, Mapping):
        raise TypeError("Config must be a mapping")
    validated: dict = {}
    for key, value in cfg.items():
        if not isinstance(key, str):
            raise TypeError("Config keys must be strings")
        if not key.strip() or key[0] in {":", "-", "!", "?"}:
            raise TypeError("Config keys must be non-empty and not start with YAML control characters")
        validated[key] = value
    return validated


def _merge_defaults(cfg: dict, defaults: Mapping[str, Any] | None) -> dict:
    """Merge default values without overwriting user-provided settings."""

    if not defaults:
        return cfg
    merged = dict(defaults)
    merged.update(cfg)
    return merged


def load_config(*, defaults: Mapping[str, Any] | None = None) -> dict:
    """Load the YAML configuration safely.

    - Returns defaults (or ``{}``) when the file is absent or malformed.
    - Logs parse errors for diagnostics while favoring availability over
      strictness.
    """

    if not os.path.exists(CONFIG_FILE):
        return dict(defaults or {})
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        validated = _validate_config(raw)
        return _merge_defaults(validated, defaults)
    except (yaml.YAMLError, TypeError):
        logger.warning("Failed to parse config; using defaults", exc_info=True)
        return dict(defaults or {})
    except OSError:
        logger.exception("Unable to read config file; using defaults")
        return dict(defaults or {})


def _atomic_write(path: str, payload: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix="config-", suffix=".yaml")
    with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
        tmp_file.write(payload)
        tmp_file.flush()
        os.fsync(tmp_file.fileno())
    os.replace(tmp_path, path)


def save_config(cfg: Mapping[str, Any]) -> str:
    """Persist validated configuration to disk atomically.

    Returns the file path for observability and testing. Raises ``TypeError``
    when the provided configuration is invalid.
    """

    validated = _validate_config(cfg)
    serialized = yaml.safe_dump(validated, allow_unicode=True, sort_keys=True)
    _atomic_write(CONFIG_FILE, serialized)
    return CONFIG_FILE


def update_config(updates: Mapping[str, Any]) -> dict:
    """Merge updates into the stored config and persist the result."""

    current = load_config()
    current.update(_validate_config(updates))
    save_config(current)
    return current
