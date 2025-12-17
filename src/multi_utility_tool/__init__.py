"""Multi-Utility Tool flat-package module."""

from .app import main
from .core.app_core import AppCore

__all__ = ["AppCore", "main"]
