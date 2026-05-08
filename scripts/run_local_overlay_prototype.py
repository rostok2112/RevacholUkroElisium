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
    from scripts.local_overlay_prototype import (
        LocalOverlayPrototypeError,
        build_overlay_view_model,
        render_overlay_html,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from companion_client import CompanionClient, CompanionClientError
    from companion_server import DEFAULT_HOST, make_server
    from local_overlay_prototype import (
        LocalOverlayPrototypeError,
        build_overlay_view_model,
        render_overlay_html,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


DEFAULT_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/overlay-prototype"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Render a local static overlay prototype from the synthetic companion provider "
            "contract. This is not a production overlay and never calls real providers."
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
        help="Overlay prototype mode to render.",
    )
    parser.add_argument(
        "--post-synthetic-event",
        action="store_true",
        help="Post the synthetic event fixture through /synthetic/provider-annotate first.",
    )
    parser.add_argument(
        "--event",
        type=Path,
        default=DEFAULT_EVENT,
        help="Synthetic fake game event JSON. Defaults to the public synthetic fixture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional HTML output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/overlay-prototype/; unsafe paths are rejected."
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help=(
            "Optional JSON view-model output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/overlay-prototype/; unsafe paths are rejected."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress rendered HTML on stdout and print only a short status line.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Start an in-process localhost server, post the fixture, render, and stop cleanly.",
    )
    args = parser.parse_args()

    try:
        output_path = resolve_output_path(args.output) if args.output else None
        json_output_path = resolve_output_path(args.json_output) if args.json_output else None
        if args.self_test:
            return run_self_test(
                mode=args.mode,
                event_path=args.event,
                output_path=output_path,
                json_output_path=json_output_path,
                quiet=args.quiet,
            )

        client = CompanionClient(args.server_url)
        if args.post_synthetic_event:
            provider_result = client.provider_annotate_fake_event(_load_event(args.event))
            context_packet = provider_result["context_packet"]
            annotation_card = provider_result["annotation_card"]
        else:
            context_packet = client.latest_provider_context()
            annotation_card = client.latest_provider_annotation()
            if context_packet is None or annotation_card is None:
                raise LocalOverlayPrototypeError(
                    "No latest provider annotation is available. "
                    "Use --post-synthetic-event or POST /synthetic/provider-annotate first."
                )

        view_model = build_overlay_view_model(context_packet, annotation_card, mode=args.mode)
        html = render_overlay_html(view_model)
        _write_outputs(view_model, html, output_path, json_output_path)
    except (
        CompanionClientError,
        LocalOverlayPrototypeError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        parser.error(str(exc))

    _print_result(
        html=html,
        output_path=output_path,
        json_output_path=json_output_path,
        quiet=args.quiet,
    )
    return 0


def run_self_test(
    *,
    mode: str = "compact",
    event_path: Path = DEFAULT_EVENT,
    output_path: Path | None = None,
    json_output_path: Path | None = None,
    quiet: bool = False,
) -> int:
    server = make_server(DEFAULT_HOST, 0)
    host, port = server.server_address[:2]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        client = CompanionClient(f"http://{host}:{port}")
        provider_result = client.provider_annotate_fake_event(_load_event(event_path))
        view_model = build_overlay_view_model(
            provider_result["context_packet"],
            provider_result["annotation_card"],
            mode=mode,
        )
        html = render_overlay_html(view_model)
        if "Local Overlay Prototype" not in html:
            print("Local overlay prototype self-test failed: HTML marker missing.")
            return 1
        _write_outputs(view_model, html, output_path, json_output_path)
        if quiet:
            print("Local overlay prototype self-test passed.")
        else:
            _print_result(
                html=html,
                output_path=output_path,
                json_output_path=json_output_path,
                quiet=False,
            )
        return 0
    except (CompanionClientError, LocalOverlayPrototypeError, OSError, ValueError) as exc:
        print(f"Local overlay prototype self-test failed: {exc}")
        return 1
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    output_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise ValueError(
            "Unsafe output path. Use a path under "
            "workspace/synthetic-slice/overlay-prototype/ for generated overlay artifacts."
        )
    return resolved


def _write_outputs(
    view_model: dict[str, Any],
    html: str,
    output_path: Path | None,
    json_output_path: Path | None,
) -> None:
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html + "\n", encoding="utf-8")
    if json_output_path:
        json_output_path.parent.mkdir(parents=True, exist_ok=True)
        json_output_path.write_text(
            json.dumps(view_model, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _print_result(
    *,
    html: str,
    output_path: Path | None,
    json_output_path: Path | None,
    quiet: bool,
) -> None:
    if quiet:
        print("Local overlay prototype rendered.")
        return
    if output_path or json_output_path:
        if output_path:
            print(f"Wrote {output_path.relative_to(ROOT)}")
        if json_output_path:
            print(f"Wrote {json_output_path.relative_to(ROOT)}")
        return
    print(html)


def _load_event(path: Path) -> dict[str, Any]:
    event = load_json(path)
    if not isinstance(event, dict):
        raise LocalOverlayPrototypeError("Synthetic event JSON must be an object.")
    return event


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
