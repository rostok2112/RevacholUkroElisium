from __future__ import annotations

import json
from typing import Any

try:
    from scripts.companion_client import CompanionClientError
    from scripts.local_overlay_prototype import LocalOverlayPrototypeError, build_overlay_view_model
    from scripts.overlay_actions import MODES
    from scripts.overlay_viewmodel_validator import (
        FUTURE_PROVIDER_MARKERS,
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )
except ImportError:  # pragma: no cover - used when run as a script path.
    from companion_client import CompanionClientError
    from local_overlay_prototype import LocalOverlayPrototypeError, build_overlay_view_model
    from overlay_actions import MODES
    from overlay_viewmodel_validator import (
        FUTURE_PROVIDER_MARKERS,
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )


STATE_SOURCE_SCHEMA_VERSION = "overlay-state-source.v1"
SOURCE_STATUSES = ("ready", "no_provider_state", "stale", "error")
DEFAULT_STALE_AFTER_SECONDS = 30

FORBIDDEN_STATE_SOURCE_MARKERS = (
    "Disco Elysium: The Final Cut",
    "<!doctype html>",
    "<html",
    "<script",
    "</script",
    "javascript:",
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
    "key_binding",
    "hotkey",
    "shortcut",
    "Ctrl+",
) + FUTURE_PROVIDER_MARKERS


class OverlayStateSourceError(ValueError):
    """Raised when an overlay state-source result violates the local contract."""


def build_overlay_state_source(
    latest_provider_context: dict[str, Any] | None,
    latest_provider_annotation: dict[str, Any] | None,
    *,
    mode: str = "compact",
    previous_state: dict[str, Any] | None = None,
    stale: bool = False,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    if mode not in MODES:
        raise OverlayStateSourceError(f"Unsupported overlay mode: {mode!r}")
    if stale_after_seconds < 1:
        raise OverlayStateSourceError("stale_after_seconds must be positive.")

    if stale and previous_state is not None and previous_state.get("view_model") is not None:
        state = _state_from_view_model(
            previous_state["view_model"],
            source_status="stale",
            stale_after_seconds=stale_after_seconds,
            error=_error("stale", "Previous overlay state is being reused as a stale preview."),
        )
        assert_valid_overlay_state_source(state)
        return state

    if latest_provider_context is None and latest_provider_annotation is None:
        if previous_state is not None and previous_state.get("view_model") is not None:
            state = _state_from_view_model(
                previous_state["view_model"],
                source_status="stale",
                stale_after_seconds=stale_after_seconds,
                error=_error(
                    "stale",
                    "No latest provider state is available; previous overlay state is stale.",
                ),
            )
            assert_valid_overlay_state_source(state)
            return state
        state = _empty_state(
            source_status="no_provider_state",
            current_mode=mode,
            stale_after_seconds=stale_after_seconds,
            error=_error(
                "no_provider_state",
                "No latest provider context or annotation is available.",
            ),
        )
        assert_valid_overlay_state_source(state)
        return state

    if latest_provider_context is None or latest_provider_annotation is None:
        state = _empty_state(
            source_status="error",
            current_mode=mode,
            stale_after_seconds=stale_after_seconds,
            error=_error(
                "partial_provider_state",
                "Latest provider context and annotation must both be available.",
            ),
        )
        assert_valid_overlay_state_source(state)
        return state

    try:
        view_model = build_overlay_view_model(
            latest_provider_context,
            latest_provider_annotation,
            mode=mode,
        )
        assert_valid_overlay_view_model(view_model, expected_mode=mode)
    except (LocalOverlayPrototypeError, OverlayViewModelValidationError, ValueError) as exc:
        state = _empty_state(
            source_status="error",
            current_mode=mode,
            stale_after_seconds=stale_after_seconds,
            error=_error("invalid_provider_state", _safe_message(str(exc))),
        )
        assert_valid_overlay_state_source(state)
        return state

    state = _state_from_view_model(
        view_model,
        source_status="stale" if stale else "ready",
        stale_after_seconds=stale_after_seconds,
        error=(
            _error("stale", "Latest provider state was marked stale deterministically.")
            if stale
            else None
        ),
    )
    assert_valid_overlay_state_source(state)
    return state


def build_overlay_state_from_client(
    client: Any,
    *,
    mode: str = "compact",
    previous_state: dict[str, Any] | None = None,
    stale: bool = False,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
) -> dict[str, Any]:
    try:
        latest_context = client.latest_provider_context()
        latest_annotation = client.latest_provider_annotation()
    except (CompanionClientError, OSError, ValueError) as exc:
        state = _empty_state(
            source_status="error",
            current_mode=mode,
            stale_after_seconds=stale_after_seconds,
            error=_error("companion_client_error", _safe_message(str(exc))),
        )
        assert_valid_overlay_state_source(state)
        return state
    return build_overlay_state_source(
        latest_context,
        latest_annotation,
        mode=mode,
        previous_state=previous_state,
        stale=stale,
        stale_after_seconds=stale_after_seconds,
    )


def collect_overlay_state_source_errors(state: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(state, dict):
        return ["$: overlay state source result must be an object"]

    _require_const(state, "schema_version", STATE_SOURCE_SCHEMA_VERSION, "$", errors)
    _require_type(state, "source_status", str, "$", errors)
    _require_type(state, "current_mode", str, "$", errors)
    _require_type(state, "available_actions", list, "$", errors)
    _require_type(state, "stale_after_seconds", int, "$", errors)
    for key in ("last_update_id", "line_id", "view_model", "visibility", "error", "debug_summary"):
        if key not in state:
            errors.append(f"$: missing required property {key!r}")
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
        _require_type(state, key, bool, "$", errors)

    status = state.get("source_status")
    if status not in SOURCE_STATUSES:
        errors.append(f"$.source_status: expected one of {SOURCE_STATUSES!r}")
    if state.get("current_mode") not in MODES:
        errors.append(f"$.current_mode: expected one of {MODES!r}")
    if isinstance(state.get("stale_after_seconds"), int) and state["stale_after_seconds"] < 1:
        errors.append("$.stale_after_seconds: expected positive integer")

    if status in {"ready", "stale"}:
        _validate_ready_or_stale_state(state, errors)
    else:
        if state.get("view_model") is not None:
            errors.append("$.view_model: expected null unless source_status is ready or stale")
        if state.get("visibility") is not None:
            errors.append("$.visibility: expected null unless source_status is ready or stale")
        if state.get("available_actions") != []:
            errors.append("$.available_actions: expected empty list unless ready or stale")
        if not isinstance(state.get("error"), dict):
            errors.append("$.error: expected object for non-ready state")

    if status == "ready" and state.get("error") is not None:
        errors.append("$.error: ready states must use null")
    if status == "no_provider_state":
        _require_error_code(state.get("error"), "no_provider_state", errors)
    if status == "stale":
        _require_error_code(state.get("error"), "stale", errors)
    if status == "error" and not isinstance(state.get("error"), dict):
        errors.append("$.error: error states require error details")

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
            errors.append(f"$.{key}: must be false")

    rendered = json.dumps(state, ensure_ascii=False, sort_keys=True)
    _assert_markers_absent(rendered, FORBIDDEN_STATE_SOURCE_MARKERS, "$", errors)
    return errors


def assert_valid_overlay_state_source(state: dict[str, Any]) -> None:
    errors = collect_overlay_state_source_errors(state)
    if errors:
        raise OverlayStateSourceError("; ".join(errors))


def _state_from_view_model(
    view_model: dict[str, Any],
    *,
    source_status: str,
    stale_after_seconds: int,
    error: dict[str, str] | None,
) -> dict[str, Any]:
    mode = view_model["mode"]
    payload = view_model[mode]
    source = view_model.get("source", {})
    line_id = source.get("line_id")
    return _base_state(
        source_status=source_status,
        current_mode=mode,
        view_model=view_model,
        visibility=payload.get("visibility"),
        available_actions=payload.get("actions", []),
        stale_after_seconds=stale_after_seconds,
        last_update_id=line_id,
        line_id=line_id,
        error=error,
        debug_summary=_debug_summary(view_model) if mode == "debug" else None,
    )


def _empty_state(
    *,
    source_status: str,
    current_mode: str,
    stale_after_seconds: int,
    error: dict[str, str],
) -> dict[str, Any]:
    return _base_state(
        source_status=source_status,
        current_mode=current_mode,
        view_model=None,
        visibility=None,
        available_actions=[],
        stale_after_seconds=stale_after_seconds,
        last_update_id=None,
        line_id=None,
        error=error,
        debug_summary=None,
    )


def _base_state(
    *,
    source_status: str,
    current_mode: str,
    view_model: dict[str, Any] | None,
    visibility: dict[str, Any] | None,
    available_actions: list[Any],
    stale_after_seconds: int,
    last_update_id: str | None,
    line_id: str | None,
    error: dict[str, str] | None,
    debug_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "schema_version": STATE_SOURCE_SCHEMA_VERSION,
        "source_status": source_status,
        "current_mode": current_mode,
        "view_model": view_model,
        "visibility": visibility,
        "available_actions": available_actions,
        "stale_after_seconds": stale_after_seconds,
        "last_update_id": last_update_id,
        "line_id": line_id,
        "error": error,
        "debug_summary": debug_summary,
        "polling_loop_started": False,
        "timer_started": False,
        "background_thread_started": False,
        "provider_call_performed": False,
        "calls_provider": False,
        "companion_contract_changed": False,
        "companion_http_contract_changed": False,
        "ui_side_effects": False,
        "clipboard_written": False,
    }


def _debug_summary(view_model: dict[str, Any]) -> dict[str, Any]:
    debug = view_model.get("debug", {})
    provider_debug = debug.get("provider_debug", {}) if isinstance(debug, dict) else {}
    prompt_pack = debug.get("prompt_pack", {}) if isinstance(debug, dict) else {}
    privacy = debug.get("privacy", {}) if isinstance(debug, dict) else {}
    raw_flags = debug.get("raw_risk_flags", []) if isinstance(debug, dict) else []
    return {
        "provider_name": provider_debug.get("provider_name"),
        "prompt_pack_id": prompt_pack.get("pack_id") or provider_debug.get("prompt_pack_id"),
        "privacy_available": privacy.get("available"),
        "cache_key": privacy.get("cache_key"),
        "raw_risk_flag_count": len(raw_flags) if isinstance(raw_flags, list) else 0,
        "action_count": len(debug.get("actions", [])) if isinstance(debug, dict) else 0,
    }


def _validate_ready_or_stale_state(state: dict[str, Any], errors: list[str]) -> None:
    view_model = state.get("view_model")
    if not isinstance(view_model, dict):
        errors.append("$.view_model: expected object for ready/stale state")
        return
    mode = view_model.get("mode")
    try:
        assert_valid_overlay_view_model(
            view_model, expected_mode=mode if isinstance(mode, str) else None
        )
    except OverlayViewModelValidationError as exc:
        errors.append(f"$.view_model: invalid overlay view model: {exc}")
        return
    if state.get("current_mode") != mode:
        errors.append(f"$.current_mode: expected {mode!r}, got {state.get('current_mode')!r}")
    payload = view_model[mode]
    if state.get("visibility") != payload.get("visibility"):
        errors.append("$.visibility: must match active view-model visibility")
    if state.get("available_actions") != payload.get("actions"):
        errors.append("$.available_actions: must match active view-model actions")
    source = view_model.get("source", {})
    line_id = source.get("line_id") if isinstance(source, dict) else None
    if state.get("line_id") != line_id:
        errors.append("$.line_id: must match view-model source line_id")
    if state.get("last_update_id") != line_id:
        errors.append("$.last_update_id: must match view-model source line_id")
    if mode != "debug" and state.get("debug_summary") is not None:
        errors.append("$.debug_summary: expected null outside debug mode")
    if mode == "debug" and not isinstance(state.get("debug_summary"), dict):
        errors.append("$.debug_summary: expected object in debug mode")


def _require_error_code(error: Any, expected_code: str, errors: list[str]) -> None:
    if not isinstance(error, dict):
        return
    if error.get("code") != expected_code:
        errors.append(f"$.error.code: expected {expected_code!r}, got {error.get('code')!r}")


def _error(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": _safe_message(message)}


def _safe_message(message: str) -> str:
    rendered = str(message)
    for marker in FORBIDDEN_STATE_SOURCE_MARKERS:
        rendered = rendered.replace(marker, "[redacted]")
    return rendered


def _assert_markers_absent(
    text: str,
    markers: tuple[str, ...],
    path: str,
    errors: list[str],
) -> None:
    lowered = text.lower()
    for marker in markers:
        if marker.lower() in lowered:
            errors.append(f"{path}: contains forbidden marker {marker!r}")


def _require_const(
    value: dict[str, Any],
    key: str,
    expected: Any,
    path: str,
    errors: list[str],
) -> None:
    if key not in value:
        errors.append(f"{path}: missing required property {key!r}")
    elif value[key] != expected:
        errors.append(f"{path}.{key}: expected {expected!r}, got {value[key]!r}")


def _require_type(
    value: dict[str, Any],
    key: str,
    expected_type: type,
    path: str,
    errors: list[str],
) -> None:
    if key not in value:
        errors.append(f"{path}: missing required property {key!r}")
        return
    if not isinstance(value[key], expected_type) or (
        expected_type in {int, float} and isinstance(value[key], bool)
    ):
        errors.append(f"{path}.{key}: expected {expected_type.__name__}")
