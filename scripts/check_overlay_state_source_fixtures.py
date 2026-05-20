from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.overlay_state_simulator import (
        OverlayStateSimulatorError,
        assert_valid_overlay_transition,
        simulate_overlay_action,
    )
    from scripts.overlay_state_source import (
        OverlayStateSourceError,
        assert_valid_overlay_state_source,
        build_overlay_state_source,
    )
    from scripts.overlay_viewmodel_validator import (
        FUTURE_PROVIDER_MARKERS,
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ImportError:  # pragma: no cover - used when run as a script path.
    from overlay_state_simulator import (
        OverlayStateSimulatorError,
        assert_valid_overlay_transition,
        simulate_overlay_action,
    )
    from overlay_state_source import (
        OverlayStateSourceError,
        assert_valid_overlay_state_source,
        build_overlay_state_source,
    )
    from overlay_viewmodel_validator import (
        FUTURE_PROVIDER_MARKERS,
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


FIXTURE_DIR = ROOT / "tests/fixtures"
PROVIDER_SUCCESS_FIXTURE = FIXTURE_DIR / "provider_annotate.success_response.synthetic.json"

STATE_SOURCE_CASES = (
    "ready.compact",
    "ready.deep",
    "ready.debug",
    "no_provider_state",
    "stale",
    "error",
)

FIXTURE_PATHS = {
    "ready.compact": FIXTURE_DIR / "overlay_state_source.ready.compact.synthetic.json",
    "ready.deep": FIXTURE_DIR / "overlay_state_source.ready.deep.synthetic.json",
    "ready.debug": FIXTURE_DIR / "overlay_state_source.ready.debug.synthetic.json",
    "no_provider_state": FIXTURE_DIR / "overlay_state_source.no_provider_state.synthetic.json",
    "stale": FIXTURE_DIR / "overlay_state_source.stale.synthetic.json",
    "error": FIXTURE_DIR / "overlay_state_source.error.synthetic.json",
}

READY_TRANSITION_ACTIONS = {
    "ready.compact": "switch_deep",
    "ready.deep": "switch_compact",
    "ready.debug": "switch_debug",
}

FORBIDDEN_FIXTURE_MARKERS = (
    "Disco Elysium: The Final Cut",
    "context_packet.game.title",
    "<!doctype html>",
    "<html",
    "prompt_pack_sections",
    "prompt_pack_focus_sections",
    "raw_provider_request",
    "api_key",
    "access_token",
    "bearer ",
    "sk-",
    "password",
    "credential",
    "secret",
    "C:\\",
    "D:\\",
    "/Users/",
    "/home/",
    "data/extracted",
    "data/local",
    "steamapps",
    "http://",
    "https://",
) + FUTURE_PROVIDER_MARKERS


class OverlayStateSourceFixtureError(ValueError):
    """Raised when state-source fixtures drift or violate the local contract."""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check or regenerate synthetic overlay state-source regression fixtures. "
            "This does not start a polling loop, server, provider, or UI shell."
        )
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Regenerate committed JSON fixtures intentionally.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short pass/fail line.")
    args = parser.parse_args()

    try:
        summary = check_overlay_state_source_fixtures(write=args.write)
    except (OverlayStateSourceFixtureError, OSError, ValueError) as exc:
        if args.quiet:
            print(f"Overlay state-source fixture check failed: {exc}")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        action = "updated" if args.write else "passed"
        print(f"Overlay state-source fixture check {action}.")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def check_overlay_state_source_fixtures(
    *,
    write: bool = False,
    fixture_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    fixture_paths = fixture_paths or FIXTURE_PATHS
    states = build_current_state_sources()
    errors: list[str] = []
    drift: dict[str, list[str]] = {}

    for case in STATE_SOURCE_CASES:
        state = states[case]
        try:
            validate_state_source_fixture(case, state)
        except OverlayStateSourceFixtureError as exc:
            errors.append(f"{case}: generated state is invalid: {exc}")
            continue

        path = fixture_paths[case]
        rendered = canonical_json(state)
        if write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered + "\n", encoding="utf-8")
            continue

        if not path.exists():
            errors.append(f"{case}: missing fixture {_display_path(path)}")
            continue

        try:
            existing_payload = json.loads(path.read_text(encoding="utf-8"))
            validate_state_source_fixture(case, existing_payload)
        except (json.JSONDecodeError, OverlayStateSourceFixtureError) as exc:
            errors.append(f"{case}: committed fixture is invalid: {exc}")
            continue

        existing_rendered = canonical_json(existing_payload)
        if existing_rendered != rendered:
            drift[case] = list(
                difflib.unified_diff(
                    existing_rendered.splitlines(),
                    rendered.splitlines(),
                    fromfile=_display_path(path),
                    tofile=f"current:{case}",
                    lineterm="",
                )
            )

    if drift:
        drift_chunks = []
        for case, lines in drift.items():
            drift_chunks.extend([f"{case} fixture drift:", *lines])
        errors.append("\n".join(drift_chunks))

    if errors:
        raise OverlayStateSourceFixtureError("\n".join(errors))

    return {
        "schema_version": "overlay-state-source-fixture-check.v1",
        "ok": True,
        "write": write,
        "fixtures": {
            case: str(fixture_paths[case].relative_to(ROOT)).replace("\\", "/")
            if _is_relative_to(fixture_paths[case], ROOT)
            else str(fixture_paths[case])
            for case in STATE_SOURCE_CASES
        },
    }


def build_current_state_sources() -> dict[str, dict[str, Any]]:
    context_packet, annotation_card = _provider_payloads()
    ready_compact = build_overlay_state_source(context_packet, annotation_card, mode="compact")
    ready_deep = build_overlay_state_source(context_packet, annotation_card, mode="deep")
    ready_debug = build_overlay_state_source(context_packet, annotation_card, mode="debug")
    return {
        "ready.compact": ready_compact,
        "ready.deep": ready_deep,
        "ready.debug": ready_debug,
        "no_provider_state": build_overlay_state_source(None, None, mode="compact"),
        "stale": build_overlay_state_source(
            None,
            None,
            mode="compact",
            previous_state=ready_compact,
        ),
        "error": build_overlay_state_source(context_packet, None, mode="compact"),
    }


def validate_state_source_fixture(case: str, state: dict[str, Any]) -> None:
    try:
        assert_valid_overlay_state_source(state)
    except OverlayStateSourceError as exc:
        raise OverlayStateSourceFixtureError(f"contract validation failed: {exc}") from exc

    _validate_case_shape(case, state)
    _assert_safe_fixture(case, state)

    if case.startswith("ready."):
        mode = case.split(".", 1)[1]
        view_model = state.get("view_model")
        try:
            assert_valid_overlay_view_model(view_model, expected_mode=mode)
            preview = simulate_overlay_action(view_model, READY_TRANSITION_ACTIONS[case])
            assert_valid_overlay_transition(preview)
        except (OverlayViewModelValidationError, OverlayStateSimulatorError) as exc:
            raise OverlayStateSourceFixtureError(f"transition compatibility failed: {exc}") from exc
        _assert_safe_fixture(f"{case} transition preview", preview)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _provider_payloads() -> tuple[dict[str, Any], dict[str, Any]]:
    envelope = load_json(PROVIDER_SUCCESS_FIXTURE)
    return envelope["data"]["context_packet"], envelope["data"]["annotation_card"]


def _validate_case_shape(case: str, state: dict[str, Any]) -> None:
    expected_status = "ready" if case.startswith("ready.") else case
    if state.get("source_status") != expected_status:
        raise OverlayStateSourceFixtureError(
            f"expected source_status {expected_status!r}, got {state.get('source_status')!r}"
        )

    if case.startswith("ready."):
        expected_mode = case.split(".", 1)[1]
        if state.get("current_mode") != expected_mode:
            raise OverlayStateSourceFixtureError(
                f"expected current_mode {expected_mode!r}, got {state.get('current_mode')!r}"
            )
        if not isinstance(state.get("view_model"), dict):
            raise OverlayStateSourceFixtureError("ready fixture must include a view_model")
        if state.get("error") is not None:
            raise OverlayStateSourceFixtureError("ready fixture error must be null")
    elif case == "no_provider_state":
        _expect_absent_view_state(state)
        _expect_error_code(state, "no_provider_state")
    elif case == "stale":
        if not isinstance(state.get("view_model"), dict):
            raise OverlayStateSourceFixtureError("stale fixture must include a stale view_model")
        _expect_error_code(state, "stale")
    elif case == "error":
        _expect_absent_view_state(state)
        if not isinstance(state.get("error"), dict):
            raise OverlayStateSourceFixtureError("error fixture must include safe error details")

    for key in (
        "polling_loop_started",
        "timer_started",
        "background_thread_started",
        "provider_call_performed",
        "calls_provider",
        "companion_contract_changed",
        "companion_http_contract_changed",
        "ui_side_effects",
        "clipboard_written",
    ):
        if state.get(key) is not False:
            raise OverlayStateSourceFixtureError(f"{key} must be false")


def _expect_absent_view_state(state: dict[str, Any]) -> None:
    if state.get("view_model") is not None:
        raise OverlayStateSourceFixtureError("view_model must be null")
    if state.get("visibility") is not None:
        raise OverlayStateSourceFixtureError("visibility must be null")
    if state.get("available_actions") != []:
        raise OverlayStateSourceFixtureError("available_actions must be empty")


def _expect_error_code(state: dict[str, Any], expected_code: str) -> None:
    error = state.get("error")
    if not isinstance(error, dict) or error.get("code") != expected_code:
        raise OverlayStateSourceFixtureError(
            f"expected error code {expected_code!r}, got {error!r}"
        )


def _assert_safe_fixture(case: str, value: Any) -> None:
    rendered = canonical_json(value)
    lowered = rendered.lower()
    for marker in FORBIDDEN_FIXTURE_MARKERS:
        if marker.lower() in lowered:
            raise OverlayStateSourceFixtureError(f"{case}: contains forbidden marker {marker!r}")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
