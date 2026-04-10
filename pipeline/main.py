"""Backward-compatible re-exports from the split modules.

Before the refactor, all functions lived here. External callers and
``__main__.py`` can still import from ``pipeline.main`` without changes.
"""

from __future__ import annotations

from pipeline.cli import cli
from pipeline.modes.digest import run as run_digest
from pipeline.modes.generate import run as run_generate
from pipeline.modes.publish import run as run_publish

__all__ = ["cli", "run_generate", "run_publish", "run_digest"]
