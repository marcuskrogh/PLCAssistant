"""Pure Program card status helpers for the App engineering surface."""

from __future__ import annotations

from typing import Mapping, Sequence

from plcassistant.surface.model import SoftPlcProject

ScheduleStatus = str
RunStatus = str
Health = str


def program_schedule_status(project: SoftPlcProject, program_id: str) -> ScheduleStatus:
    """Return ``scheduled`` when any Task calls *program_id*, else ``unscheduled``."""
    for task in project.tasks:
        if program_id in task.programs:
            return "scheduled"
    return "unscheduled"


def program_run_status(
    project: SoftPlcProject,
    program_id: str,
    softplc_running: bool,
) -> RunStatus:
    """Return the card run status for *program_id*."""
    if program_schedule_status(project, program_id) == "unscheduled":
        return "unscheduled"
    return "running" if softplc_running else "not running"


def health_from_log(entries: Sequence[Mapping[str, object]]) -> Health:
    """Summarise chronological log entries as ``ok``, ``warning``, or ``error``."""
    levels = {str(entry.get("level", "")).lower() for entry in entries}
    if "error" in levels:
        return "error"
    if "warning" in levels or "warn" in levels:
        return "warning"
    return "ok"


__all__ = [
    "health_from_log",
    "program_run_status",
    "program_schedule_status",
]
