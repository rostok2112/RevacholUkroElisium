from __future__ import annotations

import argparse
import json
import sys
import threading
from urllib.request import urlopen

try:
    from scripts.companion_server import DEFAULT_HOST, DEFAULT_PORT, make_server
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from companion_server import DEFAULT_HOST, DEFAULT_PORT, make_server


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the local synthetic Revachol companion server. "
            "Defaults bind to 127.0.0.1 and use only offline deterministic mocks."
        )
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=(
            "Host to bind. Defaults to 127.0.0.1; passing another host is an explicit "
            "choice to bind beyond localhost."
        ),
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind. Default: 8765.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Start an ephemeral localhost server, call /health, then shut it down cleanly.",
    )
    args = parser.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    server = make_server(args.host, args.port)
    host, port = server.server_address[:2]
    print(f"Revachol synthetic companion server listening on http://{host}:{port}")
    print("Mode: offline/mock/synthetic-only. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()
    return 0


def run_smoke_test() -> int:
    server = make_server(DEFAULT_HOST, 0)
    host, port = server.server_address[:2]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with urlopen(f"http://{host}:{port}/health", timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not payload.get("ok"):
            print("Companion server smoke test failed: /health did not return ok=true")
            return 1
        data = payload.get("data", {})
        if not data.get("mode", {}).get("offline") or not data.get("mode", {}).get("mock"):
            print("Companion server smoke test failed: server is not reporting offline/mock mode")
            return 1
        print(f"Companion server smoke test passed on http://{host}:{port}")
        return 0
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    sys.exit(main())
