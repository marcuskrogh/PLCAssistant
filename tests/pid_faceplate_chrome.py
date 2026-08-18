"""Shared source for PID faceplate chrome (card + isolated elements)."""

from __future__ import annotations

from pathlib import Path

WWW = Path("custom_components/plcassistant/www")
CARD = WWW / "pid-loop-card.js"
ELEMENTS = WWW / "pid-faceplate-elements.js"


def faceplate_chrome_source() -> str:
    return CARD.read_text(encoding="utf-8") + "\n" + ELEMENTS.read_text(encoding="utf-8")
