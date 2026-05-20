from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import threading
from typing import Any

try:
    from scripts.companion_client import CompanionClient, CompanionClientError
    from scripts.companion_server import DEFAULT_HOST, make_server
    from scripts.overlay_state_source import (
        OverlayStateSourceError,
        build_overlay_state_from_client,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ImportError:  # pragma: no cover - used when run as a script path.
    from companion_client import CompanionClient, CompanionClientError
    from companion_server import DEFAULT_HOST, make_server
    from overlay_state_source import OverlayStateSourceError, build_overlay_state_from_client
    from schema_validator import load_json
    from synthetic_slice import ROOT


DEFAULT_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/overlay-prototype/state"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a side-effect-free overlay state-source result from latest companion provider "
            "state. This is not a polling loop, timer, UI shell, or provider runner."
        )
    )
    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:8765",
        help="Companion server base URL. Default: http://127.0.0.1:8765",
    )
    parser.add_argument(
        "--mode",
        choices=("compact", "deep", "debug"),
        default="compact",
        help="Overlay mode to build.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Start an in-process localhost server, post the synthetic fixture, read state, stop.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON output path. Must be under "
            "workspace/synthetic-slice/overlay-prototype/state/."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short status line.")
    args = parser.parse_args()

    try:
        output_path = resolve_output_path(args.output) if args.output else None
        if args.self_test:
            state = run_self_test(mode=args.mode)
        else:
            client = CompanionClient(args.server_url)
            state = build_overlay_state_from_client(client, mode=args.mode)
        if output_path:
            _write_state(output_path, state)
    except (CompanionClientError, OverlayStateSourceError, OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.quiet:
        if args.self_test and state["source_status"] == "ready":
            print("Overlay state source self-test passed.")
        else:
            print(f"Overlay state source: {state['source_status']}.")
    else:
        print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if state["source_status"] != "error" else 1


def run_self_test(*, mode: str = "compact") -> dict[str, Any]:
    server = make_server(DEFAULT_HOST, 0)
    host, port = server.server_address[:2]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        client = CompanionClient(f"http://{host}:{port}")
        client.provider_annotate_fake_event(load_json(DEFAULT_EVENT))
        state = build_overlay_state_from_client(client, mode=mode)
        if state["source_status"] != "ready":
            raise OverlayStateSourceError(
                f"Self-test expected ready state, got {state['source_status']!r}."
            )
        return state
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    allowed_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, allowed_root):
        raise ValueError(
            "Unsafe output path. Use a path under "
            "workspace/synthetic-slice/overlay-prototype/state/ for generated state-source "
            "summaries."
        )
    return resolved


def _write_state(output_path: Path, state: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
