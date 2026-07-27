"""Block program surface: data model, YAML round-trip, placement, and validation (SWD-119).

See docs/surface/01-block-model.md for the full contract.
No Home Assistant dependency.
"""

from plcassistant.surface.model import (
    BlockInstance,
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    TemplateLibrary,
    Wire,
)
from plcassistant.surface.schema import (
    place_block,
    program_from_dict,
    program_to_dict,
    reset_instance,
    validate_program,
)

__all__ = [
    "BlockInstance",
    "BlockTemplate",
    "PinDirection",
    "PinSpec",
    "Program",
    "TemplateLibrary",
    "Wire",
    "place_block",
    "program_from_dict",
    "program_to_dict",
    "reset_instance",
    "validate_program",
]
