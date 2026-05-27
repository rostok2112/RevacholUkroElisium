from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.check_bepinex_metadata_probe_report import canonical_json
    from scripts.check_overlay_review_accessibility import (
        collect_overlay_review_accessibility_errors,
    )
    from scripts.companion_client import CompanionClient, CompanionClientError
    from scripts.local_overlay_prototype import (
        LocalOverlayPrototypeError,
        build_overlay_view_model,
        render_overlay_html,
    )
    from scripts.overlay_state_source import (
        OverlayStateSourceError,
        build_overlay_state_source,
        collect_overlay_state_source_errors,
    )
    from scripts.overlay_viewmodel_validator import (
        OverlayViewModelValidationError,
        collect_overlay_viewmodel_errors,
    )
    from scripts.run_bepinex_metadata_probe_local_smoke import (
        LocalSmokeError,
        check_metadata_probe_log_action,
        discover_local_smoke_paths,
        discovery_summary,
        enable_probe_flow,
        set_probe_config_action,
        set_synthetic_send_config_action,
        write_metadata_probe_report,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - direct script execution from scripts/
    from check_bepinex_metadata_probe_report import canonical_json
    from check_overlay_review_accessibility import collect_overlay_review_accessibility_errors
    from companion_client import CompanionClient, CompanionClientError
    from local_overlay_prototype import (
        LocalOverlayPrototypeError,
        build_overlay_view_model,
        render_overlay_html,
    )
    from overlay_state_source import (
        OverlayStateSourceError,
        build_overlay_state_source,
        collect_overlay_state_source_errors,
    )
    from overlay_viewmodel_validator import (
        OverlayViewModelValidationError,
        collect_overlay_viewmodel_errors,
    )
    from run_bepinex_metadata_probe_local_smoke import (
        LocalSmokeError,
        check_metadata_probe_log_action,
        discover_local_smoke_paths,
        discovery_summary,
        enable_probe_flow,
        set_probe_config_action,
        set_synthetic_send_config_action,
        write_metadata_probe_report,
    )
    from synthetic_slice import ROOT


SUMMARY_ROOT = ROOT / "workspace/synthetic-slice/bepinex-bridge/bridge-to-overlay-smoke"
DEFAULT_SUMMARY_OUTPUT = SUMMARY_ROOT / "summary.json"
OVERLAY_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/overlay-prototype/bridge-to-overlay-smoke"
DEFAULT_OVERLAY_OUTPUT = OVERLAY_OUTPUT_ROOT / "overlay.html"
SCHEMA_VERSION = "bridge-to-overlay-synthetic-smoke.v1"
DEFAULT_SERVER_URL = "http://127.0.0.1:8765"


class BridgeToOverlaySmokeError(RuntimeError):
    """Raised when the synthetic bridge-to-overlay smoke cannot continue safely."""


@dataclass(frozen=True)
class SmokeOptions:
    server_url: str = DEFAULT_SERVER_URL
    game_dir: str | None = None
    core_dll: str | None = None
    il2cpp_dll: str | None = None
    configuration: str = "Debug"
    skip_build: bool = False
    skip_install: bool = False
    mode: str = "compact"
    write_report: bool = False
    output: Path | None = None
    write_overlay_html: bool = False
    overlay_output: Path | None = None
    verbose: bool = False


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    options = SmokeOptions(
        server_url=args.server_url,
        game_dir=args.game_dir,
        core_dll=args.core_dll,
        il2cpp_dll=args.il2cpp_dll,
        configuration=args.configuration,
        skip_build=args.skip_build,
        skip_install=args.skip_install,
        mode=args.mode,
        write_report=args.write_report,
        output=args.output,
        write_overlay_html=args.write_overlay_html,
        overlay_output=args.overlay_output,
        verbose=args.verbose,
    )

    try:
        summary, exit_code = run_bridge_to_overlay_smoke(
            args.phase, options, client=CompanionClient(args.server_url)
        )
    except (BridgeToOverlaySmokeError, LocalSmokeError) as exc:
        summary = _base_summary(args.phase)
        summary["ok"] = False
        summary["blockers"] = [_safe_blocker(str(exc))]
        exit_code = 1

    if args.quiet:
        status = "ok" if exit_code == 0 else "not_ready"
        print(f"Bridge-to-overlay synthetic smoke {args.phase}: {status}.")
    else:
        print(canonical_json(summary), end="")
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare or review a synthetic bridge-to-overlay smoke without launching the game, "
            "printing raw logs, or dumping provider payloads."
        )
    )
    parser.add_argument(
        "--phase",
        choices=("prepare", "post", "cleanup"),
        default="post",
        help="Smoke phase to run. Default: post.",
    )
    parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    parser.add_argument("--auto-discover", action="store_true", help="Use bounded Steam discovery.")
    parser.add_argument("--game-dir", help="Explicit local game directory override.")
    parser.add_argument("--core-dll", help="Explicit BepInEx.Core.dll override.")
    parser.add_argument("--il2cpp-dll", help="Explicit BepInEx IL2CPP DLL override.")
    parser.add_argument("--configuration", choices=("Debug", "Release"), default="Debug")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--skip-install", action="store_true")
    parser.add_argument("--mode", choices=("compact", "deep", "debug"), default="compact")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write a redacted bridge-to-overlay summary under ignored workspace paths.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional JSON summary path under workspace/synthetic-slice/bepinex-bridge/bridge-to-overlay-smoke/.",
    )
    parser.add_argument(
        "--write-overlay-html",
        action="store_true",
        help="Write rendered overlay HTML under ignored overlay prototype workspace paths.",
    )
    parser.add_argument(
        "--overlay-output",
        type=Path,
        help="Optional HTML path under workspace/synthetic-slice/overlay-prototype/bridge-to-overlay-smoke/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print one safe status line.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include local discovery paths. Still never prints raw logs or provider payloads.",
    )
    return parser


def run_bridge_to_overlay_smoke(
    phase: str,
    options: SmokeOptions,
    *,
    client: Any | None = None,
) -> tuple[dict[str, object], int]:
    client = client or CompanionClient(options.server_url)
    if phase == "prepare":
        return run_prepare(options, client=client)
    if phase == "post":
        return run_post(options, client=client)
    if phase == "cleanup":
        return run_cleanup(options)
    raise BridgeToOverlaySmokeError(f"Unsupported smoke phase: {phase}")


def run_prepare(options: SmokeOptions, *, client: Any) -> tuple[dict[str, object], int]:
    summary = _base_summary("prepare")
    health_available = _health_available(client)
    summary["companion_health_available"] = health_available
    if not health_available:
        summary["ok"] = False
        summary["blockers"] = ["companion_health_unavailable"]
        return _maybe_write_summary(summary, options), 1

    discovery = _discover(options)
    summary["discovery"] = discovery_summary(discovery, verbose=options.verbose)
    actions = enable_probe_flow(
        discovery,
        configuration=options.configuration,
        skip_build=options.skip_build,
        skip_install=options.skip_install,
    )
    synthetic_action = set_synthetic_send_config_action(discovery, enabled=True)
    summary["prepare"] = {
        "bridge_build_attempted": _nested_bool(actions, "build", "attempted"),
        "bridge_build_succeeded": _nested_bool(actions, "build", "succeeded"),
        "bridge_dll_installed": _nested_bool(actions, "install", "installed"),
        "metadata_probe_enabled": _nested_bool(actions, "config", "metadata_probe_enabled"),
        "metadata_probe_log_on_start": _nested_bool(
            actions, "config", "metadata_probe_log_on_start"
        ),
        "send_synthetic_event_on_start": bool(
            synthetic_action.get("send_synthetic_event_on_start")
        ),
    }
    summary["ok"] = True
    return _maybe_write_summary(summary, options), 0


def run_post(options: SmokeOptions, *, client: Any) -> tuple[dict[str, object], int]:
    summary = _base_summary("post")
    discovery = _discover(options)
    summary["discovery"] = discovery_summary(discovery, verbose=options.verbose)

    log_check = check_metadata_probe_log_action(discovery)
    log_summary = log_check.redacted_summary()
    summary["bridge_log"] = {
        "plugin_loaded_observed": log_summary["plugin_loaded_observed"],
        "metadata_snapshot_observed": log_summary["metadata_snapshot_observed"],
        "companion_health_available_observed": log_summary["companion_health_available_observed"],
        "synthetic_send_observed": log_summary["synthetic_provider_event_sent_observed"],
        "metadata_snapshot_created_count_observed": log_summary[
            "metadata_snapshot_created_count_observed"
        ],
        "health_check_observed_count_observed": log_summary["health_check_observed_count_observed"],
        "synthetic_send_configured_count_observed": log_summary[
            "synthetic_send_configured_count_observed"
        ],
        "real_text_captured_false_observed": log_summary["real_text_captured_false_observed"],
        "current_line_capture_enabled_false_observed": log_summary[
            "current_line_capture_enabled_false_observed"
        ],
        "ui_probe_attempted_false_observed": log_summary["ui_probe_attempted_false_observed"],
        "scene_probe_attempted_false_observed": log_summary["scene_probe_attempted_false_observed"],
        "forbidden_marker_detected": log_summary["forbidden_marker_detected"],
        "raw_log_included": False,
    }

    blockers: list[str] = []
    if log_check.forbidden_marker_detected:
        blockers.append("forbidden_bridge_log_marker_detected")
    else:
        report_result = write_metadata_probe_report(log_check)
        summary["metadata_probe_report"] = {
            "written": report_result["written"],
            "probe_status": report_result["probe_status"],
            "raw_report_included": False,
        }

    latest_context, latest_annotation, companion_blockers = _latest_provider_state(client)
    blockers.extend(companion_blockers)
    summary["companion_provider_state"] = {
        "latest_provider_context_available": latest_context is not None,
        "latest_provider_annotation_available": latest_annotation is not None,
        "raw_provider_payload_included": False,
    }

    overlay_summary = _build_overlay_summary(
        latest_context,
        latest_annotation,
        mode=options.mode,
        write_html=options.write_overlay_html,
        overlay_output=options.overlay_output,
    )
    summary["overlay"] = overlay_summary
    blockers.extend(overlay_summary.get("blockers", []))
    summary["blockers"] = blockers
    summary["bridge_to_overlay_ready"] = not blockers
    summary["ok"] = not blockers
    return _maybe_write_summary(summary, options), 0 if not blockers else 1


def run_cleanup(options: SmokeOptions) -> tuple[dict[str, object], int]:
    summary = _base_summary("cleanup")
    discovery = _discover(options)
    summary["discovery"] = discovery_summary(discovery, verbose=options.verbose)
    probe_action = set_probe_config_action(discovery, enabled=False)
    synthetic_action = set_synthetic_send_config_action(discovery, enabled=False)
    summary["cleanup"] = {
        "metadata_probe_enabled": bool(probe_action.get("metadata_probe_enabled")),
        "metadata_probe_log_on_start": bool(probe_action.get("metadata_probe_log_on_start")),
        "send_synthetic_event_on_start": bool(
            synthetic_action.get("send_synthetic_event_on_start")
        ),
        "metadata_probe_disabled_restored": True,
        "synthetic_send_disabled_restored": True,
    }
    summary["ok"] = True
    return _maybe_write_summary(summary, options), 0


def _discover(options: SmokeOptions):
    return discover_local_smoke_paths(
        game_dir=options.game_dir,
        core_dll=options.core_dll,
        il2cpp_dll=options.il2cpp_dll,
        configuration=options.configuration,
    )


def _health_available(client: Any) -> bool:
    try:
        health = client.health()
    except (CompanionClientError, OSError, ValueError):
        return False
    return isinstance(health, dict) and health.get("status") == "ok"


def _latest_provider_state(
    client: Any,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    blockers: list[str] = []
    try:
        latest_context = client.latest_provider_context()
        latest_annotation = client.latest_provider_annotation()
    except (CompanionClientError, OSError, ValueError):
        return None, None, ["companion_latest_provider_state_unavailable"]
    if latest_context is None or latest_annotation is None:
        blockers.append("latest_provider_state_missing")
    return latest_context, latest_annotation, blockers


def _build_overlay_summary(
    latest_context: dict[str, Any] | None,
    latest_annotation: dict[str, Any] | None,
    *,
    mode: str,
    write_html: bool,
    overlay_output: Path | None,
) -> dict[str, object]:
    summary: dict[str, object] = {
        "mode": mode,
        "state_source_status": "not_built",
        "state_source_valid": False,
        "view_model_valid": False,
        "html_rendered": False,
        "html_accessibility_valid": False,
        "html_written": False,
        "raw_provider_payload_included": False,
        "raw_html_included": False,
        "blockers": [],
    }
    blockers: list[str] = []
    try:
        state = build_overlay_state_source(latest_context, latest_annotation, mode=mode)
        state_errors = collect_overlay_state_source_errors(state)
    except (OverlayStateSourceError, LocalOverlayPrototypeError, ValueError):
        summary["blockers"] = ["overlay_state_source_failed"]
        return summary

    status = state.get("source_status")
    summary["state_source_status"] = status
    summary["state_source_valid"] = not state_errors
    if state_errors:
        blockers.append("overlay_state_source_invalid")
    if status != "ready":
        blockers.append(f"overlay_state_source_{status}")

    view_model = state.get("view_model")
    if isinstance(view_model, dict):
        view_errors = collect_overlay_viewmodel_errors(view_model, expected_mode=mode)
        summary["view_model_valid"] = not view_errors
        if view_errors:
            blockers.append("overlay_view_model_invalid")
        try:
            build_overlay_view_model(latest_context or {}, latest_annotation or {}, mode=mode)
            html = render_overlay_html(view_model)
            summary["html_rendered"] = True
            accessibility_errors = collect_overlay_review_accessibility_errors(mode, html)
            summary["html_accessibility_valid"] = not accessibility_errors
            if accessibility_errors:
                blockers.append("overlay_html_accessibility_invalid")
            if write_html:
                output = ensure_safe_overlay_output_path(overlay_output or DEFAULT_OVERLAY_OUTPUT)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(html + "\n", encoding="utf-8")
                summary["html_written"] = True
                summary["html_output"] = _relative_path(output)
        except (
            LocalOverlayPrototypeError,
            OverlayViewModelValidationError,
            OSError,
            ValueError,
        ):
            blockers.append("overlay_html_render_failed")
    else:
        blockers.append("overlay_view_model_missing")

    summary["blockers"] = blockers
    return summary


def ensure_safe_summary_output_path(path: Path) -> Path:
    return _ensure_safe_output_path(path, SUMMARY_ROOT, ".json", "bridge-to-overlay summary")


def ensure_safe_overlay_output_path(path: Path) -> Path:
    return _ensure_safe_output_path(path, OVERLAY_OUTPUT_ROOT, ".html", "bridge-to-overlay HTML")


def _ensure_safe_output_path(path: Path, root: Path, suffix: str, label: str) -> Path:
    resolved_root = root.resolve(strict=False)
    resolved = (ROOT / path).resolve(strict=False) if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise BridgeToOverlaySmokeError(
            f"Unsafe {label} output path. Use a path under {root.relative_to(ROOT)}."
        ) from exc
    if resolved.suffix.lower() != suffix:
        raise BridgeToOverlaySmokeError(f"Unsafe {label} output path. Expected {suffix}.")
    return resolved


def _maybe_write_summary(summary: dict[str, object], options: SmokeOptions) -> dict[str, object]:
    if not options.write_report:
        return summary
    output = ensure_safe_summary_output_path(options.output or DEFAULT_SUMMARY_OUTPUT)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(summary), encoding="utf-8")
    summary["summary_report"] = {
        "written": True,
        "path": _relative_path(output),
        "raw_log_included": False,
        "raw_provider_payload_included": False,
    }
    output.write_text(canonical_json(summary), encoding="utf-8")
    return summary


def _base_summary(phase: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "phase": phase,
        "ok": False,
        "bridge_to_overlay_ready": False,
        "blockers": [],
        "no_game_launch_performed": True,
        "raw_log_included": False,
        "raw_report_included": False,
        "raw_provider_payload_included": False,
        "screenshots_read": False,
        "game_files_read": False,
        "provider_called": False,
        "companion_contract_changed": False,
        "current_line_capture_performed": False,
        "real_text_capture_performed": False,
    }


def _nested_bool(payload: dict[str, object], key: str, nested_key: str) -> bool:
    nested = payload.get(key)
    return bool(nested.get(nested_key)) if isinstance(nested, dict) else False


def _safe_blocker(message: str) -> str:
    lowered = message.lower()
    if "companion" in lowered:
        return "companion_unavailable_or_invalid"
    if "output path" in lowered or "unsafe" in lowered:
        return "unsafe_output_path"
    if "game directory" in lowered:
        return "game_directory_not_found"
    if "bepinex" in lowered:
        return "bepinex_path_unavailable"
    return "bridge_to_overlay_smoke_failed"


def _relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return f"<local:{path.name}>"


if __name__ == "__main__":
    sys.exit(main())
