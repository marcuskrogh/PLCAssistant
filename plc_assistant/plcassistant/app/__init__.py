"""PLC Assistant App — visual block editor and HTTP API (SWD-120).

Entry points
------------
``python -m plcassistant.app``       Start the server (default port 8099)
``python -m plcassistant.app --port 8080``

See docs/surface/05-app-editor.md for the full contract.
"""

from plcassistant.app.server import AppState, make_handler, run_app

__all__ = [
    "AppState",
    "make_handler",
    "run_app",
]
