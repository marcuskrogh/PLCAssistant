"""Process tag ↔ block pin wirings — one common testable format (SWD-224).

Inter-block ``Wire`` stays on the Program. External I/O (Soft-PLC image tags ↔
instance pins) uses ``TagPinWire`` so callers apply the same list in production
and tests — no per-tag bridge assertions required.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Iterable, Mapping, Sequence


class IoDir(str, Enum):
    """Direction relative to the block program."""

    IN = "IN"  # tag → pin (pre-tick)
    OUT = "OUT"  # pin → tag (post-tick)


@dataclass(frozen=True)
class TagPinWire:
    """One external tag ↔ instance pin link.

    Format (YAML / dict)::

        {tag: LT_TANK, instance: level_pi, pin: pv, dir: IN}
    """

    tag: str
    instance: str
    pin: str
    direction: IoDir

    @property
    def context_key(self) -> str:
        return f"{self.instance}.{self.pin}"

    def to_dict(self) -> dict[str, str]:
        return {
            "tag": self.tag,
            "instance": self.instance,
            "pin": self.pin,
            "dir": self.direction.value,
        }


def tag_pin_wire_from_dict(data: Mapping[str, Any], *, index: int = 0) -> TagPinWire:
    """Parse one wire dict; raises ``ValueError`` on bad shape."""
    if not isinstance(data, Mapping):
        raise ValueError(f"io_wires[{index}] must be a mapping")
    for key in ("tag", "instance", "pin"):
        if key not in data or data[key] is None or str(data[key]).strip() == "":
            raise ValueError(f"io_wires[{index}] missing required key {key!r}")
    raw_dir = data.get("dir", data.get("direction", "IN"))
    try:
        direction = IoDir(str(raw_dir).upper())
    except ValueError as exc:
        raise ValueError(
            f"io_wires[{index}] invalid dir {raw_dir!r} (expected IN|OUT)"
        ) from exc
    return TagPinWire(
        tag=str(data["tag"]).strip(),
        instance=str(data["instance"]).strip(),
        pin=str(data["pin"]).strip(),
        direction=direction,
    )


def tag_pin_wires_from_list(raw: Sequence[Mapping[str, Any]] | None) -> list[TagPinWire]:
    """Parse a list of wire dicts."""
    if raw is None:
        return []
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise ValueError("io_wires must be a list")
    return [tag_pin_wire_from_dict(item, index=i) for i, item in enumerate(raw)]


def validate_tag_pin_wires(wires: Iterable[TagPinWire]) -> None:
    """Reject duplicate drives of the same pin (IN) or tag (OUT)."""
    seen_in: set[tuple[str, str]] = set()
    seen_out: set[str] = set()
    for w in wires:
        if w.direction is IoDir.IN:
            key = (w.instance, w.pin)
            if key in seen_in:
                raise ValueError(
                    f"multiple IN wirings drive pin {w.pin!r} on {w.instance!r}"
                )
            seen_in.add(key)
        else:
            if w.tag in seen_out:
                raise ValueError(f"multiple OUT wirings drive tag {w.tag!r}")
            seen_out.add(w.tag)


def apply_io_wires_in(
    wires: Iterable[TagPinWire],
    *,
    get_tag: Callable[[str], Any],
    set_pin: Callable[[str, Any], None],
) -> int:
    """Copy tag values into context pins for every IN wire. Returns count applied."""
    n = 0
    for w in wires:
        if w.direction is not IoDir.IN:
            continue
        set_pin(w.context_key, get_tag(w.tag))
        n += 1
    return n


def apply_io_wires_out(
    wires: Iterable[TagPinWire],
    *,
    get_pin: Callable[[str], Any],
    set_tag: Callable[[str, Any], None],
) -> int:
    """Copy context pin values onto tags for every OUT wire. Returns count applied."""
    n = 0
    for w in wires:
        if w.direction is not IoDir.OUT:
            continue
        set_tag(w.tag, get_pin(w.context_key))
        n += 1
    return n


# Pseudo-tags resolved by the skid shell (not IoImage process tags).
SHELL_TAG_LEVEL_SP = "_SHELL.LEVEL_SP"
SHELL_TAG_RUNNING = "_SHELL.RUNNING"
SHELL_TAG_FLOW_SP_OVERRIDE = "_SHELL.FLOW_SP_OVERRIDE"


def wedge_cascade_io_wires() -> list[TagPinWire]:
    """Default Level→Flow cascade process ↔ pin map (demo tank).

    Shell-owned signals use ``_SHELL.*`` pseudo-tags so the same apply helpers
    work in unit tests with a plain dict of tag values.
    """
    return [
        TagPinWire("LT_TANK", "level_pi", "pv", IoDir.IN),
        TagPinWire(SHELL_TAG_LEVEL_SP, "level_pi", "sp", IoDir.IN),
        TagPinWire(SHELL_TAG_RUNNING, "level_pi", "running", IoDir.IN),
        TagPinWire("FT_INLET", "flow_pi", "pv", IoDir.IN),
        TagPinWire(SHELL_TAG_RUNNING, "flow_pi", "running", IoDir.IN),
        # Optional: when present, overrides cascade wire into flow_pi.sp.
        TagPinWire(SHELL_TAG_FLOW_SP_OVERRIDE, "flow_pi", "sp", IoDir.IN),
        TagPinWire("SP_FLOW_AUTO", "level_pi", "cv", IoDir.OUT),
        TagPinWire("CMD_SPEED", "flow_pi", "cv", IoDir.OUT),
    ]


__all__ = [
    "IoDir",
    "SHELL_TAG_FLOW_SP_OVERRIDE",
    "SHELL_TAG_LEVEL_SP",
    "SHELL_TAG_RUNNING",
    "TagPinWire",
    "apply_io_wires_in",
    "apply_io_wires_out",
    "tag_pin_wire_from_dict",
    "tag_pin_wires_from_list",
    "validate_tag_pin_wires",
    "wedge_cascade_io_wires",
]
