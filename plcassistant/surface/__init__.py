"""Block program surface: data model, YAML round-trip, runtime, and built-in library.

See docs/surface/ for the full contract.
No Home Assistant dependency.
"""

from plcassistant.surface.builtin import (
    register_builtins,
    wedge_cascade_program,
)
from plcassistant.surface.model import (
    BlockInstance,
    BlockTemplate,
    PinDirection,
    PinSpec,
    Program,
    TemplateLibrary,
    Wire,
)
from plcassistant.surface.runtime import (
    BlockCallable,
    BlockRuntime,
    DictContext,
    TagContext,
    make_runtime,
)
from plcassistant.surface.schema import (
    place_block,
    program_from_dict,
    program_to_dict,
    reset_instance,
    validate_program,
)
from plcassistant.surface.user_library import (
    add_user_template,
    get_user_template,
    list_user_templates,
    make_user_template,
    register_user_templates,
    remove_user_template,
)

__all__ = [
    # model
    "BlockInstance",
    "BlockTemplate",
    "PinDirection",
    "PinSpec",
    "Program",
    "TemplateLibrary",
    "Wire",
    # schema
    "place_block",
    "program_from_dict",
    "program_to_dict",
    "reset_instance",
    "validate_program",
    # runtime
    "BlockCallable",
    "BlockRuntime",
    "DictContext",
    "TagContext",
    "make_runtime",
    # built-in library
    "register_builtins",
    "wedge_cascade_program",
    # user library (SWD-114)
    "add_user_template",
    "get_user_template",
    "list_user_templates",
    "make_user_template",
    "register_user_templates",
    "remove_user_template",
]
