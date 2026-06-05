from __future__ import annotations

import argparse
import json
from pathlib import Path
import threading
from typing import Any

try:
    from scripts.companion_client import CompanionClient, CompanionClientError
    from scripts.companion_server import DEFAULT_HOST, make_server
    from scripts.run_runtime_translation_memory import RuntimeTranslationMemoryError
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover
    from companion_client import CompanionClient, CompanionClientError
    from companion_server import DEFAULT_HOST, make_server
    from run_runtime_translation_memory import RuntimeTranslationMemoryError
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "runtime-current-line-smoke-summary.v1"
OUTPUT_ROOT = "workspace/local-private/runtime-smoke/"


class RuntimeCurrentLineSmokeError(RuntimeError):
    """Raised when runtime current-line smoke evidence is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a local synthetic runtime current-line transport smoke."
    )
    parser.add_argument("--output", type=Path, help=f"Optional summary under {OUTPUT_ROOT}.")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        summary = run_smoke(root=ROOT)
        if args.output:
            write_summary(summary, resolve_output_path(args.output, root=ROOT))
        if args.quiet:
            print("Runtime current-line smoke passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (
        CompanionClientError,
        RuntimeCurrentLineSmokeError,
        RuntimeTranslationMemoryError,
    ) as exc:
        parser.error(str(exc))
    return 0


def run_smoke(*, root: Path = ROOT) -> dict[str, Any]:
    server = make_server(DEFAULT_HOST, 0)
    host, port = server.server_address[:2]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = CompanionClient(f"http://{host}:{port}")
        event = _synthetic_runtime_event()
        receipt = client.post_runtime_current_line(event)
        latest = client.latest_runtime_current_line()
        if latest is None:
            raise RuntimeCurrentLineSmokeError("Latest runtime current-line state was missing.")
        tm = receipt.get("translation_memory")
        if not isinstance(tm, dict):
            raise RuntimeCurrentLineSmokeError(
                "Runtime receipt did not include translation memory."
            )
        summary = {
            "schema_version": SUMMARY_SCHEMA_VERSION,
            "runtime_current_line_endpoint_available": True,
            "event_received": receipt.get("event_received") is True,
            "latest_runtime_current_line_available": latest is not None,
            "translation_memory_checked": True,
            "cache_hit": bool(tm.get("cache_hit")),
            "provider_call_required": bool(tm.get("provider_call_required")),
            "provider_called": receipt.get("provider_called") is True,
            "source_text_included": False,
            "translated_text_included": False,
            "private_paths_included": False,
            "provider_payloads_included": False,
            "raw_logs_included": False,
            "screenshots_included": False,
            "game_file_reads": False,
            "bepinex_log_reads": False,
            "ocr_used": False,
            "unity_scanning_used": False,
            "hooks_used": False,
            "recommended_next_step": "runtime_targeted_hook_candidate_research_review_gate",
        }
        rendered = json.dumps(summary, sort_keys=True)
        for forbidden in (
            event["source_text"],
            event["line_id"],
            "Synthetic Speaker",
            str(root),
        ):
            if forbidden in rendered:
                raise RuntimeCurrentLineSmokeError("Smoke summary leaked private runtime data.")
        return summary
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def resolve_output_path(path: Path, *, root: Path = ROOT) -> Path:
    if path.is_absolute() or ".." in path.parts:
        raise RuntimeCurrentLineSmokeError("Use repo-relative output paths without traversal.")
    resolved = (root / path).resolve(strict=False)
    allowed = (root / OUTPUT_ROOT).resolve(strict=False)
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise RuntimeCurrentLineSmokeError(f"Unsafe output path. Use {OUTPUT_ROOT}.") from exc
    if resolved.suffix.lower() != ".json":
        raise RuntimeCurrentLineSmokeError("Smoke output path must use .json.")
    return resolved


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _synthetic_runtime_event() -> dict[str, str]:
    return {
        "schema_version": "runtime-current-line-event.v1",
        "event_kind": "current_line",
        "line_id": "synthetic.runtime.smoke.001",
        "source_text": "Invented runtime smoke line.",
        "speaker": "Synthetic Speaker",
        "conversation_id": "synthetic.runtime.conversation",
        "source": "synthetic_runtime",
    }


if __name__ == "__main__":
    raise SystemExit(main())
