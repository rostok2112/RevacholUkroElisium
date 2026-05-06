from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import threading

try:
    from scripts.companion_client import CompanionClient, CompanionClientError
    from scripts.companion_server import DEFAULT_HOST, make_server
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT, build_context_packet
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from companion_client import CompanionClient, CompanionClientError
    from companion_server import DEFAULT_HOST, make_server
    from schema_validator import load_json
    from synthetic_slice import ROOT, build_context_packet


DEFAULT_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tiny local client for the synthetic companion server contract."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8765",
        help="Companion server base URL. Default: http://127.0.0.1:8765",
    )
    parser.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout in seconds.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in (
        "health",
        "latest-context",
        "latest-annotation",
        "latest-overlay-demo",
        "latest-eval-summary",
        "latest-provider-context",
        "latest-provider-annotation",
        "latest-review-html",
        "run-synthetic-eval",
        "smoke-test",
    ):
        subparsers.add_parser(name)

    post_parser = subparsers.add_parser("post-synthetic-event")
    post_parser.add_argument(
        "--event",
        type=Path,
        default=DEFAULT_EVENT,
        help="Synthetic fake game event JSON. Defaults to the public synthetic fixture.",
    )
    provider_event_parser = subparsers.add_parser("provider-annotate-event")
    provider_event_parser.add_argument(
        "--event",
        type=Path,
        default=DEFAULT_EVENT,
        help="Synthetic fake game event JSON. Defaults to the public synthetic fixture.",
    )
    provider_context_parser = subparsers.add_parser("provider-annotate-context")
    provider_context_parser.add_argument(
        "--context-packet",
        type=Path,
        required=True,
        help="Synthetic context packet JSON to annotate with the deterministic mock provider.",
    )

    args = parser.parse_args()

    try:
        if args.command == "smoke-test":
            return run_smoke_test()

        client = CompanionClient(args.base_url, args.timeout)
        result = _run_command(client, args)
    except CompanionClientError as exc:
        print(f"Companion client error: {exc}", file=sys.stderr)
        return 1

    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _run_command(client: CompanionClient, args: argparse.Namespace) -> object:
    if args.command == "health":
        return client.health()
    if args.command == "latest-context":
        return client.latest_context()
    if args.command == "latest-annotation":
        return client.latest_annotation()
    if args.command == "latest-overlay-demo":
        return client.latest_overlay_demo()
    if args.command == "latest-eval-summary":
        return client.latest_eval_summary()
    if args.command == "latest-provider-context":
        return client.latest_provider_context()
    if args.command == "latest-provider-annotation":
        return client.latest_provider_annotation()
    if args.command == "latest-review-html":
        return client.latest_review_html()
    if args.command == "run-synthetic-eval":
        return client.run_synthetic_eval()
    if args.command == "post-synthetic-event":
        return client.post_synthetic_event(load_json(args.event))
    if args.command == "provider-annotate-event":
        return client.provider_annotate_fake_event(load_json(args.event))
    if args.command == "provider-annotate-context":
        return client.provider_annotate_context_packet(load_json(args.context_packet))
    raise CompanionClientError(f"Unknown command: {args.command}")


def run_smoke_test() -> int:
    server = make_server(DEFAULT_HOST, 0)
    host, port = server.server_address[:2]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        client = CompanionClient(f"http://{host}:{port}")
        health = client.health()
        if not health["mode"]["offline"] or not health["mode"]["mock"]:
            print("Companion client smoke test failed: server is not offline/mock.")
            return 1
        event_result = client.post_synthetic_event(load_json(DEFAULT_EVENT))
        if not event_result["context_packet"]["current_line"]["source_text"]:
            print("Companion client smoke test failed: event did not produce context.")
            return 1
        if client.latest_context() is None or client.latest_overlay_demo() is None:
            print("Companion client smoke test failed: latest state is empty after event.")
            return 1
        provider_result = client.provider_annotate_fake_event(load_json(DEFAULT_EVENT))
        if "prompt_pack_guided" not in provider_result["annotation_card"].get("risk_flags", []):
            print(
                "Companion client smoke test failed: provider annotation missed prompt pack flag."
            )
            return 1
        if client.latest_provider_context() is None or client.latest_provider_annotation() is None:
            print("Companion client smoke test failed: latest provider state is empty.")
            return 1
        context_packet = build_context_packet(load_json(DEFAULT_EVENT))
        provider_context_result = client.provider_annotate_context_packet(context_packet)
        if provider_context_result["context_packet"]["packet_id"] != context_packet["packet_id"]:
            print(
                "Companion client smoke test failed: context packet provider annotation mismatch."
            )
            return 1
        if "Revachol Synthetic Review" not in client.latest_review_html():
            print("Companion client smoke test failed: latest review HTML is missing.")
            return 1
        eval_summary = client.run_synthetic_eval()
        if not eval_summary["passed"]:
            print("Companion client smoke test failed: synthetic eval did not pass.")
            return 1
        print(f"Companion client smoke test passed on http://{host}:{port}")
        return 0
    except CompanionClientError as exc:
        print(f"Companion client smoke test failed: {exc}")
        return 1
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    sys.exit(main())
