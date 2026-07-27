"""Entry point: python -m plcassistant.app [--host HOST] [--port PORT]."""

from __future__ import annotations

import argparse

from plcassistant.app.server import run_app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PLC Assistant visual block editor (SWD-120)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host (default 127.0.0.1 — local only)",
    )
    parser.add_argument("--port", type=int, default=8099, help="Bind port (default 8099)")
    args = parser.parse_args()

    server = run_app(host=args.host, port=args.port)
    print(f"PLC Assistant App listening on http://{args.host}:{args.port}")
    print(f"Open your browser to: http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
