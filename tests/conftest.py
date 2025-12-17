"""Test fixtures and helpers for Multi-Utility-Tool."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure repository root and source tree are on sys.path for absolute imports
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for path in (SRC_ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def pytest_configure(config):  # pragma: no cover - pytest hook
    os.environ.setdefault("MUT_TESTING", "1")
