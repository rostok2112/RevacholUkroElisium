from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.check_overlay_review_accessibility import (
        collect_overlay_review_accessibility_errors,
    )
    from scripts.companion_client import CompanionClient, CompanionClientError
    from scripts.local_overlay_prototype import LocalOverlayPrototypeError, render_overlay_html
    from scripts.overlay_state_source import (
        OverlayStateSourceError,
        build_overlay_state_source,
        collect_overlay_state_source_errors,
    )
    from scripts.overlay_viewmodel_validator import collect_overlay_viewmodel_errors
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - direct script execution from scripts/
    from check_overlay_review_accessibility import collect_overlay_review_accessibility_errors
    from companion_client import CompanionClient, CompanionClientError
    from local_overlay_prototype import LocalOverlayPrototypeError, render_overlay_html
    from overlay_state_source import (
        OverlayStateSourceError,
        build_overlay_state_source,
        collect_overlay_state_source_errors,
    )
    from overlay_viewmodel_validator import collect_overlay_viewmodel_errors
    from schema_validator import load_json
    from synthetic_slice import ROOT


SCHEMA_VERSION = "overlay-refresh-readiness-summary.v1"
DEFAULT_SERVER_URL = "http://127.0.0.1:8765"
SUMMARY_ROOT = ROOT / "workspace/synthetic-slice/overlay-refresh-readiness"
DEFAULT_OUTPUT = SUMMARY_ROOT / "summary.json"
PROVIDER_SUCCESS_FIXTURE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"
MODES = ("compact", "deep", "debug")
READINESS_STATES = (
    "no_companion",
    "companion_available",
    "no_provider_state",
    "provider_state_ready",
    "overlay_state_ready",
    "overlay_view_ready",
    "overlay_html_review_ready",
    "stale",
    "error",
)


class OverlayRefreshReadinessError(RuntimeError):
    """Raised when refresh readiness cannot be summarized safely."""


class FixtureCompanionClient:
    """Synthetic in-memory companion facade used by --self-test and unit tests."""

    def __init__(
        self,
        context_packet: dict[str, Any] | None,
        annotation_card: dict[str, Any] | None,
    ) -> None:
        self.context_packet = context_packet
        self.annotation_card = annotation_card

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def latest_provider_context(self) -> dict[str, Any] | None:
        return self.context_packet

    def latest_provider_annotation(self) -> dict[str, Any] | None:
        return self.annotation_card


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            context_packet, annotation_card = load_synthetic_provider_payloads()
            client: Any = FixtureCompanionClient(context_packet, annotation_card)
            fixture_based = True
        else:
            client = CompanionClient(args.server_url)
            fixture_based = False
        summary = build_overlay_refresh_readiness_summary(
            client,
            mode=args.mode,
            fixture_based=fixture_based,
        )
        if args.write_report:
            write_summary(summary, args.output or DEFAULT_OUTPUT)
    except (OverlayRefreshReadinessError, OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.quiet:
        print(f"Overlay refresh readiness: {summary['readiness_state']}.")
    else:
        print(canonical_json(summary), end="")
    return 0 if summary["readiness_state"] != "error" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize metadata-only overlay refresh readiness from companion latest provider "
            "state and existing overlay validators. This does not poll, launch a shell, call real "
            "providers, or include raw payloads."
        )
    )
    parser.add_argument(
        "--server-url",
        default=DEFAULT_SERVER_URL,
        help="Companion server base URL. Default: http://127.0.0.1:8765",
    )
    parser.add_argument("--mode", choices=MODES, default="compact")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Use committed synthetic provider fixtures instead of a running companion server.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write a redacted JSON summary under workspace/synthetic-slice/overlay-refresh-readiness/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON summary path under workspace/synthetic-slice/overlay-refresh-readiness/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print one safe status line.")
    return parser


def build_overlay_refresh_readiness_summary(
    client: Any,
    *,
    mode: str = "compact",
    fixture_based: bool = False,
) -> dict[str, Any]:
    if mode not in MODES:
        raise OverlayRefreshReadinessError(f"Unsupported overlay mode: {mode!r}")

    summary = _base_summary(mode=mode, fixture_based=fixture_based)

    if not _set_health_status(summary, client):
        summary["readiness_state"] = "no_companion"
        return summary

    summary["readiness_state"] = "companion_available"

    latest_context, latest_annotation, provider_error = _latest_provider_state(client)
    summary["latest_provider_context_exists"] = latest_context is not None
    summary["latest_provider_annotation_exists"] = latest_annotation is not None

    if provider_error is not None:
        summary["readiness_state"] = "error"
        summary["error"] = provider_error
        summary["blockers"] = [provider_error]
        return summary

    if latest_context is None and latest_annotation is None:
        _summarize_state_source(summary, None, None, mode=mode)
        summary["readiness_state"] = "no_provider_state"
        return summary

    if latest_context is None or latest_annotation is None:
        _summarize_state_source(summary, latest_context, latest_annotation, mode=mode)
        summary["readiness_state"] = "error"
        summary["error"] = "partial_provider_state"
        summary["blockers"] = ["partial_provider_state"]
        return summary

    summary["readiness_state"] = "provider_state_ready"
    _summarize_state_source(summary, latest_context, latest_annotation, mode=mode)
    return summary


def load_synthetic_provider_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    envelope = load_json(PROVIDER_SUCCESS_FIXTURE)
    data = envelope.get("data", {}) if isinstance(envelope, dict) else {}
    context_packet = data.get("context_packet")
    annotation_card = data.get("annotation_card")
    if not isinstance(context_packet, dict) or not isinstance(annotation_card, dict):
        raise OverlayRefreshReadinessError("Synthetic provider fixture is malformed.")
    return deepcopy(context_packet), deepcopy(annotation_card)


def write_summary(summary: dict[str, Any], output: Path) -> Path:
    safe_output = ensure_safe_output_path(output)
    safe_output.parent.mkdir(parents=True, exist_ok=True)
    safe_output.write_text(canonical_json(summary), encoding="utf-8")
    return safe_output


def ensure_safe_output_path(path: Path) -> Path:
    raw = path.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    allowed_root = SUMMARY_ROOT.resolve(strict=False)
    try:
        resolved.relative_to(allowed_root)
    except ValueError as exc:
        raise OverlayRefreshReadinessError(
            "Unsafe output path. Use a path under "
            "workspace/synthetic-slice/overlay-refresh-readiness/."
        ) from exc
    if resolved.suffix.lower() != ".json":
        raise OverlayRefreshReadinessError("Unsafe output path. Expected a .json file.")
    return resolved


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _base_summary(*, mode: str, fixture_based: bool) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "fixture_based": fixture_based,
        "metadata_only": True,
        "companion_health_status": "not_checked",
        "latest_provider_context_exists": False,
        "latest_provider_annotation_exists": False,
        "overlay_state_source_status": "not_built",
        "overlay_state_source_ready": False,
        "overlay_state_source_valid": False,
        "overlay_view_model_valid": False,
        "overlay_html_review_ready": False,
        "accessibility_check_passed": False,
        "readiness_state": "no_companion",
        "stale": False,
        "error": None,
        "blockers": [],
        "raw_payloads_included": False,
        "raw_logs_included": False,
        "raw_html_included": False,
        "game_launched": False,
        "provider_called": False,
        "polling_loop_started": False,
        "timer_started": False,
        "background_worker_started": False,
        "production_overlay_shell_started": False,
        "current_line_capture_allowed": False,
        "real_text_capture_allowed": False,
        "ui_text_reading_allowed": False,
        "unity_scanning_allowed": False,
        "hooks_allowed": False,
        "ocr_allowed": False,
        "extraction_allowed": False,
        "companion_contract_change_allowed": False,
    }


def _set_health_status(summary: dict[str, Any], client: Any) -> bool:
    try:
        health = client.health()
    except (CompanionClientError, OSError, ValueError):
        summary["companion_health_status"] = "unavailable"
        summary["blockers"] = ["companion_unavailable"]
        return False
    if isinstance(health, dict) and health.get("status") == "ok":
        summary["companion_health_status"] = "ok"
        return True
    summary["companion_health_status"] = "invalid"
    summary["blockers"] = ["companion_health_invalid"]
    return False


def _latest_provider_state(
    client: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, str | None]:
    try:
        latest_context = client.latest_provider_context()
        latest_annotation = client.latest_provider_annotation()
    except (CompanionClientError, OSError, ValueError):
        return None, None, "latest_provider_state_unavailable"
    if latest_context is not None and not isinstance(latest_context, dict):
        return None, None, "latest_provider_context_invalid"
    if latest_annotation is not None and not isinstance(latest_annotation, dict):
        return None, None, "latest_provider_annotation_invalid"
    return latest_context, latest_annotation, None


def _summarize_state_source(
    summary: dict[str, Any],
    latest_context: dict[str, Any] | None,
    latest_annotation: dict[str, Any] | None,
    *,
    mode: str,
) -> None:
    try:
        state = build_overlay_state_source(latest_context, latest_annotation, mode=mode)
        state_errors = collect_overlay_state_source_errors(state)
    except (OverlayStateSourceError, LocalOverlayPrototypeError, ValueError):
        summary["readiness_state"] = "error"
        summary["error"] = "overlay_state_source_failed"
        summary["blockers"] = ["overlay_state_source_failed"]
        return

    state_status = state.get("source_status")
    summary["overlay_state_source_status"] = state_status
    summary["overlay_state_source_valid"] = not state_errors
    summary["overlay_state_source_ready"] = state_status in {"ready", "stale"} and not state_errors
    summary["stale"] = state_status == "stale"

    if state_errors:
        summary["readiness_state"] = "error"
        summary["error"] = "overlay_state_source_invalid"
        summary["blockers"] = ["overlay_state_source_invalid"]
        return

    if state_status == "no_provider_state":
        return
    if state_status == "stale":
        summary["readiness_state"] = "stale"
    elif state_status == "ready":
        summary["readiness_state"] = "overlay_state_ready"
    else:
        summary["readiness_state"] = "error"
        summary["error"] = f"overlay_state_source_{state_status}"
        summary["blockers"] = [str(summary["error"])]
        return

    view_model = state.get("view_model")
    if not isinstance(view_model, dict):
        summary["readiness_state"] = "error"
        summary["error"] = "overlay_view_model_missing"
        summary["blockers"] = ["overlay_view_model_missing"]
        return

    view_errors = collect_overlay_viewmodel_errors(view_model, expected_mode=mode)
    summary["overlay_view_model_valid"] = not view_errors
    if view_errors:
        summary["readiness_state"] = "error"
        summary["error"] = "overlay_view_model_invalid"
        summary["blockers"] = ["overlay_view_model_invalid"]
        return
    if summary["readiness_state"] != "stale":
        summary["readiness_state"] = "overlay_view_ready"

    try:
        html = render_overlay_html(view_model)
        accessibility_errors = collect_overlay_review_accessibility_errors(mode, html)
    except (LocalOverlayPrototypeError, ValueError):
        summary["readiness_state"] = "error"
        summary["error"] = "overlay_html_review_failed"
        summary["blockers"] = ["overlay_html_review_failed"]
        return

    summary["overlay_html_review_ready"] = not accessibility_errors
    summary["accessibility_check_passed"] = not accessibility_errors
    if accessibility_errors:
        summary["readiness_state"] = "error"
        summary["error"] = "overlay_accessibility_check_failed"
        summary["blockers"] = ["overlay_accessibility_check_failed"]
        return
    if summary["readiness_state"] != "stale":
        summary["readiness_state"] = "overlay_html_review_ready"


if __name__ == "__main__":
    sys.exit(main())
