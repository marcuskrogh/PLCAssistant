"""Entry point: python -m plcassistant.app [--host HOST] [--port PORT].

When ``PLCASSISTANT_OPTIONS_PATH`` or MQTT env is set (HA App), starts the
editor plus optional MQTT scan loop via ``runtime.run_ha_runtime``.
"""

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
        default=os.environ.get("PLCASSISTANT_HOST", "127.0.0.1"),
        help="Bind host (default 127.0.0.1; App uses 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PLCASSISTANT_PORT", "8099")),
        help="Bind port (default 8099)",
    )
    parser.add_argument(
        "--program-path",
        default=os.environ.get("PLCASSISTANT_PROGRAM_PATH"),
        help="Program-of-record JSON path (App /data/program.json)",
    )
    parser.add_argument(
        "--options-path",
        default=os.environ.get("PLCASSISTANT_OPTIONS_PATH"),
        help="Supervisor options.json path (enables HA App MQTT runtime)",
    )
    parser.add_argument(
        "--ha-runtime",
        action="store_true",
        default=os.environ.get("PLCASSISTANT_HA_RUNTIME", "") == "1",
        help="Force HA App runtime (editor + MQTT scan loop)",
    )
    args = parser.parse_args()

    use_runtime = bool(args.ha_runtime or args.options_path)
    if use_runtime:
        from plcassistant.app.runtime import run_ha_runtime

        print(f"PLC Assistant HA runtime on http://{args.host}:{args.port}")
        if args.program_path:
            print(f"Program-of-record: {args.program_path}")
        if args.options_path:
            print(f"Options: {args.options_path}")
        print("Press Ctrl+C to stop.")
        try:
            run_ha_runtime(
                host=args.host,
                port=args.port,
                program_path=args.program_path,
                options_path=args.options_path,
                serve_forever=True,
            )
        except KeyboardInterrupt:
            print("\nShutting down.")
        return

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
