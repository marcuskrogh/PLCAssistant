"""Entry point: python -m plcassistant.app [--host HOST] [--port PORT]."""

from __future__ import annotations

import argparse
import os

from plcassistant.app.server import run_app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PLC Assistant visual block editor (SWD-120 / SWD-84)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host (default 127.0.0.1 — local only; App uses 0.0.0.0)",
    )
    parser.add_argument("--port", type=int, default=8099, help="Bind port (default 8099)")
    parser.add_argument(
        "--program-path",
        default=os.environ.get("PLCASSISTANT_PROGRAM_PATH"),
        help="Program-of-record JSON path (App /data/program.json)",
    )
    args = parser.parse_args()

    server = run_app(host=args.host, port=args.port, program_path=args.program_path)
    print(f"PLC Assistant App listening on http://{args.host}:{args.port}")
    if args.program_path:
        print(f"Program-of-record: {args.program_path}")
    print(f"Open your browser to: http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
