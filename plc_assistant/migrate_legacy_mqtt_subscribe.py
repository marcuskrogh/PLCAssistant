#!/usr/bin/env python3
"""Rewrite pre-0.1.5 thin-integration MQTT subscribe off hass.components.

Used by the App entrypoint when a stale image or leftover /config copy still
contains ``await hass.components.mqtt.async_subscribe(...)``.
"""

from __future__ import annotations

import pathlib
import re
import sys

_SUBSCRIBE_CALL = re.compile(
    r"await\s+hass\.components\.mqtt\.async_subscribe\(\s*"
)


def migrate(path: pathlib.Path) -> bool:
    """Return True if the file was rewritten."""
    text = path.read_text(encoding="utf-8")
    if "hass.components" not in text:
        return False

    if "from homeassistant.components.mqtt import async_subscribe" not in text:
        needle = "from homeassistant.config_entries import ConfigEntry"
        insert = (
            "from homeassistant.components.mqtt import async_subscribe\n"
            "from homeassistant.config_entries import ConfigEntry"
        )
        if needle not in text:
            raise SystemExit(1)
        text = text.replace(needle, insert, 1)

    text, n = _SUBSCRIBE_CALL.subn("await async_subscribe(\n            hass, ", text)
    if n == 0 or "hass.components" in text:
        raise SystemExit(1)

    path.write_text(text, encoding="utf-8")
    # Drop stale bytecode so Core cannot reload the broken module from __pycache__.
    for pyc in path.parent.rglob("__pycache__"):
        if pyc.is_dir():
            for child in pyc.iterdir():
                child.unlink(missing_ok=True)
    return True


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <path-to-__init__.py>", file=sys.stderr)
        return 2
    path = pathlib.Path(argv[1])
    if not path.is_file():
        return 0
    if migrate(path):
        print(
            "PLCAssistant: migrated thin integration off hass.components mqtt subscribe"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
