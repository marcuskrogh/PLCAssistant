"""Lab / hobby wedge: gravity-drained tank skid mock (SWD-83).

First-class simulated process path — no Home Assistant dependency.
See docs/wedge/ for the tag contract, control, safety, and acceptance specs.
"""

from plcassistant.wedge.control import CascadeConfig, CascadeController, CascadeOutputs
from plcassistant.wedge.process import MockProcess, ProcessConfig, ProcessState
from plcassistant.wedge.safety import Mode, SafetyConfig, SafetyLayer, SafetyState, TripCode
from plcassistant.wedge.skid import OperatorCommand, Skid, SkidConfig, SkidSnapshot

# Back-compat
TripReason = TripCode

__all__ = [
    "CascadeConfig",
    "CascadeController",
    "CascadeOutputs",
    "MockProcess",
    "ProcessConfig",
    "ProcessState",
    "Mode",
    "SafetyConfig",
    "SafetyLayer",
    "SafetyState",
    "TripCode",
    "TripReason",
    "OperatorCommand",
    "Skid",
    "SkidConfig",
    "SkidSnapshot",
]
