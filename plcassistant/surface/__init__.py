"""Block program surface: data model, YAML round-trip, runtime, and built-in library.

See docs/surface/ for the full contract.
No Home Assistant dependency.
"""

from plcassistant.surface.apply import ProgramLoader, ProjectLoader
from plcassistant.surface.builtin import (
    register_builtins,
    wedge_cascade_program,
    wedge_softplc_project,
)
from plcassistant.surface.model import (
    BlockInstance,
    BlockTemplate,
    DEFAULT_LEGACY_PROGRAM_ID,
    DEFAULT_WEDGE_PROGRAM_ID,
    MAIN_TASK_ID,
    PinDirection,
    PinSpec,
    Program,
    SoftPlcProject,
    Task,
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
    classify_project_apply,
    is_legacy_program_dict,
    main_program,
    migrate_legacy_program_dict,
    place_block,
    program_from_dict,
    program_to_dict,
    project_from_dict,
    project_structure_signature,
    project_to_dict,
    reset_instance,
    scheduled_programs,
    validate_program,
    validate_project,
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
    "DEFAULT_LEGACY_PROGRAM_ID",
    "DEFAULT_WEDGE_PROGRAM_ID",
    "MAIN_TASK_ID",
    "PinDirection",
    "PinSpec",
    "Program",
    "SoftPlcProject",
    "Task",
    "TemplateLibrary",
    "Wire",
    # schema
    "classify_project_apply",
    "is_legacy_program_dict",
    "main_program",
    "migrate_legacy_program_dict",
    "place_block",
    "program_from_dict",
    "program_to_dict",
    "project_from_dict",
    "project_structure_signature",
    "project_to_dict",
    "reset_instance",
    "scheduled_programs",
    "validate_program",
    "validate_project",
    # runtime
    "BlockCallable",
    "BlockRuntime",
    "DictContext",
    "TagContext",
    "make_runtime",
    # built-in library
    "register_builtins",
    "wedge_cascade_program",
    "wedge_softplc_project",
    # apply policy (SWD-117 / SWD-182)
    "ProgramLoader",
    "ProjectLoader",
    # user library (SWD-114)
    "add_user_template",
    "get_user_template",
    "list_user_templates",
    "make_user_template",
    "register_user_templates",
    "remove_user_template",
]
