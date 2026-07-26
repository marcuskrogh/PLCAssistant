"""Ensure vendored ``plcassistant_contract`` is importable (HACS + monorepo)."""

from __future__ import annotations

import sys
from pathlib import Path

_bootstrapped = False


def ensure_contract() -> None:
    """Add the vendored contract directory to ``sys.path`` once."""
    global _bootstrapped
    if _bootstrapped:
        return
    vendor = Path(__file__).resolve().parent / "vendor"
    path = str(vendor)
    if path not in sys.path:
        sys.path.insert(0, path)
    _bootstrapped = True
