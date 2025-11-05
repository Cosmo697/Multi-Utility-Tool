"""Test fixtures and helpers for Multi-Utility-Tool."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure repository root is on sys.path for absolute imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def pytest_configure(config):  # pragma: no cover - pytest hook
    os.environ.setdefault("MUT_TESTING", "1")
