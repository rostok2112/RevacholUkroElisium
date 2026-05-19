from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

try:
    from scripts.overlay_actions import ACTION_BY_ID, MODES, build_visibility_state
    from scripts.overlay_viewmodel_validator import (
        FUTURE_PROVIDER_MARKERS,
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )
except ImportError:  # pragma: no cover - used when run as a script path.
    from overlay_actions import ACTION_BY_ID, MODES, build_visibility_state
    from overlay_viewmodel_validator import (
        FUTURE_PROVIDER_MARKERS,
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )


TRANSITION_SCHEMA_VERSION = "overlay-state-transition-preview.v1"
SIDE_EFFECT_TYPES = ("none", "copy_preview", "hide_preview")

FORBIDDEN_TRANSITION_MARKERS = (
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


class OverlayStateSimulatorError(ValueError):
    """Raised when an overlay transition preview cannot be built safely."""


def simulate_overlay_action(view_model: dict[str, Any], action_id: str) -> dict[str, Any]:
    """Return a side-effect-free preview for a declared overlay action."""

    _assert_valid_input_view_model(view_model)
    mode = view_model["mode"]
    payload = view_model[mode]
    visibility = deepcopy(payload["visibility"])

    action_definition = ACTION_BY_ID.get(action_id)
    if action_definition is None:
        preview = _blocked_preview(
            mode=mode,
            action_id=action_id,
            action_label_uk="",
            action_hint_uk="",
            visibility=visibility,
            blocked_reason="unknown_action",
        )
        assert_valid_overlay_transition(preview)
        return preview

    action_label = action_definition.label_uk
    action_hint = action_definition.hint_uk

    if action_definition.debug_only and mode in {"compact", "deep"}:
        preview = _blocked_preview(
            mode=mode,
            action_id=action_id,
            action_label_uk=action_label,
            action_hint_uk=action_hint,
            visibility=visibility,
            blocked_reason="debug_only_action_in_player_mode",
        )
        assert_valid_overlay_transition(preview)
        return preview

    declared_action = _find_declared_action(payload.get("actions"), action_id)
    if declared_action is None:
        preview = _blocked_preview(
            mode=mode,
            action_id=action_id,
            action_label_uk=action_label,
            action_hint_uk=action_hint,
            visibility=visibility,
            blocked_reason="action_not_present",
        )
        assert_valid_overlay_transition(preview)
        return preview

    if mode not in action_definition.allowed_modes:
        preview = _blocked_preview(
            mode=mode,
            action_id=action_id,
            action_label_uk=action_label,
            action_hint_uk=action_hint,
            visibility=visibility,
            blocked_reason="action_not_allowed_in_mode",
        )
        assert_valid_overlay_transition(preview)
        return preview

    preview = _allowed_preview(
        view_model=view_model,
        mode=mode,
        action_id=action_id,
        action_label_uk=str(declared_action["label_uk"]),
        action_hint_uk=str(declared_action["hint_uk"]),
        visibility=visibility,
    )
    assert_valid_overlay_transition(preview)
    return preview


def collect_overlay_transition_errors(preview: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(preview, dict):
        return ["$: transition preview must be an object"]

    _require_const(preview, "schema_version", TRANSITION_SCHEMA_VERSION, "$", errors)
    for key in ("from_mode", "action_id", "action_label_uk", "action_hint_uk", "next_mode"):
        _require_type(preview, key, str, "$", errors)
    _require_type(preview, "allowed", bool, "$", errors)
    _require_type(preview, "next_visibility", dict, "$", errors)
    _require_type(preview, "summary_uk", str, "$", errors)
    if "blocked_reason" not in preview:
        errors.append("$: missing required property 'blocked_reason'")
    if "side_effect_type" not in preview:
        errors.append("$: missing required property 'side_effect_type'")
    if "copy_preview_text" not in preview:
        errors.append("$: missing required property 'copy_preview_text'")
    for key in (
        "no_side_effects",
        "clipboard_written",
        "keyboard_hook_used",
        "calls_companion_server",
        "calls_provider",
        "mutates_input_view_model",
    ):
        _require_type(preview, key, bool, "$", errors)

    if preview.get("from_mode") not in MODES:
        errors.append(f"$.from_mode: expected one of {MODES!r}")
    if preview.get("next_mode") not in MODES:
        errors.append(f"$.next_mode: expected one of {MODES!r}")
    if preview.get("side_effect_type") not in SIDE_EFFECT_TYPES:
        errors.append(f"$.side_effect_type: expected one of {SIDE_EFFECT_TYPES!r}")
    if preview.get("allowed") is True and preview.get("blocked_reason") is not None:
        errors.append("$.blocked_reason: allowed previews must use null")
    if preview.get("allowed") is False and not isinstance(preview.get("blocked_reason"), str):
        errors.append("$.blocked_reason: blocked previews require a string reason")
    if preview.get("copy_preview_text") is not None and not isinstance(
        preview.get("copy_preview_text"), str
    ):
        errors.append("$.copy_preview_text: expected string or null")

    if preview.get("no_side_effects") is not True:
        errors.append("$.no_side_effects: transition previews must be side-effect free")
    for key in (
        "clipboard_written",
        "keyboard_hook_used",
        "calls_companion_server",
        "calls_provider",
        "mutates_input_view_model",
    ):
        if preview.get(key) is not False:
            errors.append(f"$.{key}: must be false")

    visibility = preview.get("next_visibility")
    if isinstance(visibility, dict):
        _validate_preview_visibility(visibility, str(preview.get("next_mode")), errors)

    rendered = json.dumps(preview, ensure_ascii=False, sort_keys=True)
    _assert_markers_absent(rendered, FORBIDDEN_TRANSITION_MARKERS, "$", errors)
    if not _contains_ukrainian(str(preview.get("summary_uk", ""))):
        errors.append("$.summary_uk: expected Ukrainian human-facing summary")
    return errors


def assert_valid_overlay_transition(preview: dict[str, Any]) -> None:
    errors = collect_overlay_transition_errors(preview)
    if errors:
        raise OverlayStateSimulatorError("; ".join(errors))


def _allowed_preview(
    *,
    view_model: dict[str, Any],
    mode: str,
    action_id: str,
    action_label_uk: str,
    action_hint_uk: str,
    visibility: dict[str, Any],
) -> dict[str, Any]:
    next_mode = mode
    next_visibility = deepcopy(visibility)
    side_effect_type = "none"
    copy_preview_text: str | None = None
    summary_uk = "Дію перевірено: стан зміниться лише у попередньому перегляді."

    if action_id == "switch_compact":
        next_mode = "compact"
        next_visibility = build_visibility_state("compact")
        summary_uk = "Попередній перегляд: перейти до компактного режиму."
    elif action_id == "switch_deep":
        next_mode = "deep"
        next_visibility = build_visibility_state("deep")
        summary_uk = "Попередній перегляд: відкрити глибше пояснення."
    elif action_id == "switch_debug":
        next_mode = "debug"
        next_visibility = build_visibility_state("debug")
        summary_uk = "Попередній перегляд: залишитися у режимі розробника."
    elif action_id == "toggle_original":
        next_visibility["original_visible"] = not bool(next_visibility["original_visible"])
        summary_uk = "Попередній перегляд: перемкнути видимість англійського оригіналу."
    elif action_id == "toggle_translation":
        next_visibility["translation_visible"] = not bool(next_visibility["translation_visible"])
        summary_uk = "Попередній перегляд: перемкнути видимість українського варіанта."
    elif action_id == "toggle_annotations":
        next_visibility["annotations_visible"] = not bool(next_visibility["annotations_visible"])
        summary_uk = "Попередній перегляд: перемкнути видимість пояснень."
    elif action_id in {"next_annotation", "previous_annotation"}:
        direction = "наступної" if action_id == "next_annotation" else "попередньої"
        summary_uk = f"Попередній перегляд: перейти до {direction} нотатки без зміни індексу."
    elif action_id.startswith("copy_"):
        copy_preview_text = _copy_preview_text(view_model, action_id)
        if copy_preview_text is None:
            return _blocked_preview(
                mode=mode,
                action_id=action_id,
                action_label_uk=action_label_uk,
                action_hint_uk=action_hint_uk,
                visibility=visibility,
                blocked_reason="copy_source_unavailable",
            )
        side_effect_type = "copy_preview"
        summary_uk = "Попередній перегляд: текст підготовлено для копіювання без запису в буфер."
    elif action_id == "hide_overlay":
        next_visibility["hidden"] = True
        side_effect_type = "hide_preview"
        summary_uk = "Попередній перегляд: оверлей буде приховано без реальної дії."

    return _base_preview(
        mode=mode,
        action_id=action_id,
        action_label_uk=action_label_uk,
        action_hint_uk=action_hint_uk,
        allowed=True,
        blocked_reason=None,
        next_mode=next_mode,
        next_visibility=next_visibility,
        side_effect_type=side_effect_type,
        copy_preview_text=copy_preview_text,
        summary_uk=summary_uk,
    )


def _blocked_preview(
    *,
    mode: str,
    action_id: str,
    action_label_uk: str,
    action_hint_uk: str,
    visibility: dict[str, Any],
    blocked_reason: str,
) -> dict[str, Any]:
    return _base_preview(
        mode=mode,
        action_id=action_id,
        action_label_uk=action_label_uk,
        action_hint_uk=action_hint_uk,
        allowed=False,
        blocked_reason=blocked_reason,
        next_mode=mode,
        next_visibility=deepcopy(visibility),
        side_effect_type="none",
        copy_preview_text=None,
        summary_uk=f"Дію заблоковано: {blocked_reason}.",
    )


def _base_preview(
    *,
    mode: str,
    action_id: str,
    action_label_uk: str,
    action_hint_uk: str,
    allowed: bool,
    blocked_reason: str | None,
    next_mode: str,
    next_visibility: dict[str, Any],
    side_effect_type: str,
    copy_preview_text: str | None,
    summary_uk: str,
) -> dict[str, Any]:
    return {
        "schema_version": TRANSITION_SCHEMA_VERSION,
        "from_mode": mode,
        "action_id": action_id,
        "action_label_uk": action_label_uk,
        "action_hint_uk": action_hint_uk,
        "allowed": allowed,
        "blocked_reason": blocked_reason,
        "next_mode": next_mode,
        "next_visibility": next_visibility,
        "side_effect_type": side_effect_type,
        "copy_preview_text": copy_preview_text,
        "summary_uk": summary_uk,
        "no_side_effects": True,
        "clipboard_written": False,
        "keyboard_hook_used": False,
        "calls_companion_server": False,
        "calls_provider": False,
        "mutates_input_view_model": False,
    }


def _assert_valid_input_view_model(view_model: Any) -> None:
    if not isinstance(view_model, dict):
        raise OverlayStateSimulatorError("Overlay view model must be an object.")
    mode = view_model.get("mode")
    if mode not in MODES:
        raise OverlayStateSimulatorError(f"Unsupported overlay mode: {mode!r}")
    try:
        assert_valid_overlay_view_model(view_model, expected_mode=mode)
    except OverlayViewModelValidationError as exc:
        raise OverlayStateSimulatorError(f"Invalid overlay view model: {exc}") from exc


def _find_declared_action(actions: Any, action_id: str) -> dict[str, Any] | None:
    if not isinstance(actions, list):
        return None
    for action in actions:
        if isinstance(action, dict) and action.get("id") == action_id:
            return action
    return None


def _copy_preview_text(view_model: dict[str, Any], action_id: str) -> str | None:
    mode = view_model["mode"]
    if action_id == "copy_original":
        return _nonempty_string(view_model.get("source", {}).get("original_english"))

    payload = view_model[mode]
    if action_id == "copy_ukrainian_summary":
        if mode == "compact":
            return _nonempty_string(payload.get("concise_meaning_uk"))
        if mode == "deep":
            return _nonempty_string(payload.get("explanation_uk")) or _nonempty_string(
                payload.get("literary_rendering_uk")
            )
        return None

    if action_id == "copy_annotation_summary" and mode == "deep":
        parts = [
            _nonempty_string(payload.get("explanation_uk")),
            _first_note_text(payload.get("idiom_reference_subtext_notes")),
            _nonempty_string(payload.get("character_voice_note_uk")),
        ]
        rendered = "\n".join(part for part in parts if part)
        return rendered or None

    return None


def _first_note_text(notes: Any) -> str | None:
    if not isinstance(notes, list):
        return None
    for note in notes:
        if isinstance(note, dict):
            value = _nonempty_string(note.get("text"))
            if value:
                return value
    return None


def _nonempty_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _validate_preview_visibility(
    visibility: dict[str, Any],
    next_mode: str,
    errors: list[str],
) -> None:
    if next_mode not in MODES:
        return
    allowed_keys = set(build_visibility_state(next_mode)) | {"hidden"}
    actual_keys = set(visibility)
    unexpected = sorted(actual_keys - allowed_keys)
    if unexpected:
        errors.append(f"$.next_visibility: unexpected keys {unexpected!r}")

    for key in (
        "original_visible",
        "translation_visible",
        "annotations_visible",
        "debug_visible",
    ):
        if key not in visibility:
            errors.append(f"$.next_visibility: missing required property {key!r}")
        elif not isinstance(visibility[key], bool):
            errors.append(f"$.next_visibility.{key}: expected boolean")
    if visibility.get("current_mode") != next_mode:
        errors.append(
            f"$.next_visibility.current_mode: expected {next_mode!r}, "
            f"got {visibility.get('current_mode')!r}"
        )
    if not isinstance(visibility.get("available_modes"), list) or not all(
        isinstance(mode, str) for mode in visibility.get("available_modes", [])
    ):
        errors.append("$.next_visibility.available_modes: expected string array")
    if next_mode in {"compact", "deep"} and visibility.get("debug_visible") is True:
        errors.append("$.next_visibility.debug_visible: player modes must keep debug hidden")
    if next_mode == "debug" and visibility.get("debug_visible") is not True:
        errors.append("$.next_visibility.debug_visible: debug mode must expose debug")
    if "hidden" in visibility and visibility["hidden"] is not True:
        errors.append("$.next_visibility.hidden: expected true when present")


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


def _contains_ukrainian(value: str) -> bool:
    return any("\u0400" <= char <= "\u04ff" for char in value)


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
