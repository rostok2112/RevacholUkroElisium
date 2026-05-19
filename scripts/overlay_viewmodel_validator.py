from __future__ import annotations

import json
from typing import Any

try:
    from scripts.overlay_actions import (
        ACTION_BY_ID,
        ACTION_IDS,
        DEBUG_ONLY_ACTION_IDS,
        build_overlay_actions,
        build_visibility_state,
    )
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path dependency.
    from overlay_actions import (
        ACTION_BY_ID,
        ACTION_IDS,
        DEBUG_ONLY_ACTION_IDS,
        build_overlay_actions,
        build_visibility_state,
    )


OVERLAY_SCHEMA_VERSION = "local-overlay-prototype.v1"
MODES = ("compact", "deep", "debug")
EXPECTED_ACTION_IDS_BY_MODE = {
    mode: tuple(action["id"] for action in build_overlay_actions(mode)) for mode in MODES
}

RAW_INTERNAL_FLAGS = (
    "synthetic_fixture",
    "mock_provider",
    "deterministic_mock_provider",
    "deterministic_mock_pipeline",
    "prompt_pack_guided",
)
FUTURE_PROVIDER_MARKERS = (
    "openai_compatible",
    "deepl_glossary",
    "local_model",
    "ensemble_reviewer",
)
COMMON_FORBIDDEN_MARKERS = (
    "Disco Elysium: The Final Cut",
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
    "key_binding",
    "hotkey",
    "shortcut",
    "Ctrl+",
) + FUTURE_PROVIDER_MARKERS

PLAYER_FORBIDDEN_MARKERS = RAW_INTERNAL_FLAGS + (
    "provider_debug",
    "raw_risk_flags",
    "raw_deep_notes",
    "raw_provider",
    "Prompt-pack policy keeps",
    "Raw risk flags",
    "Raw Deep Notes",
    "provider-cache-v1.",
)

DEBUG_REQUIRED_FLAGS = ("synthetic_fixture", "mock_provider", "prompt_pack_guided")
DISALLOWED_ACTION_FIELDS = ("key_binding", "hotkey", "shortcut", "shortcut_key")


class OverlayViewModelValidationError(ValueError):
    """Raised when an overlay view model violates the stable local contract."""


def assert_valid_overlay_view_model(
    view_model: dict[str, Any],
    expected_mode: str | None = None,
) -> None:
    errors = collect_overlay_viewmodel_errors(view_model, expected_mode=expected_mode)
    if errors:
        raise OverlayViewModelValidationError("; ".join(errors))


def collect_overlay_viewmodel_errors(
    view_model: Any,
    expected_mode: str | None = None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(view_model, dict):
        return ["$: view model must be an object"]

    mode = view_model.get("mode")
    if expected_mode is not None and mode != expected_mode:
        errors.append(f"$.mode: expected {expected_mode!r}, got {mode!r}")
    if mode not in MODES:
        errors.append(f"$.mode: expected one of {MODES!r}, got {mode!r}")
        return errors

    expected_keys = {"schema_version", "mode", "source", mode}
    actual_keys = set(view_model)
    if actual_keys != expected_keys:
        errors.append(
            f"$: expected top-level keys {sorted(expected_keys)}, got {sorted(actual_keys)}"
        )

    _require_const(view_model, "schema_version", OVERLAY_SCHEMA_VERSION, "$", errors)
    _validate_source(view_model.get("source"), errors)

    rendered = _canonical(view_model)
    _assert_markers_absent(rendered, COMMON_FORBIDDEN_MARKERS, "$", errors)

    if mode in {"compact", "deep"}:
        _assert_markers_absent(rendered, PLAYER_FORBIDDEN_MARKERS, f"$.{mode}", errors)
        if mode == "compact":
            _validate_compact(view_model.get("compact"), view_model.get("source"), errors)
        else:
            _validate_deep(view_model.get("deep"), view_model.get("source"), errors)
    else:
        _validate_debug(view_model.get("debug"), errors)

    return errors


def _validate_source(source: Any, errors: list[str]) -> None:
    if not isinstance(source, dict):
        errors.append("$.source: expected object")
        return
    for key in ("original_english", "speaker", "scene_id", "conversation_id"):
        _require_type(source, key, str, "$.source", errors)
    if "line_id" in source:
        _require_type(source, "line_id", str, "$.source", errors)


def _validate_compact(compact: Any, source: Any, errors: list[str]) -> None:
    if not isinstance(compact, dict):
        errors.append("$.compact: expected object")
        return
    _require_const(compact, "mode", "compact", "$.compact", errors)
    labels = compact.get("labels_uk")
    if not isinstance(labels, dict):
        errors.append("$.compact.labels_uk: expected object")
    else:
        for key in ("original", "concise_meaning", "confidence", "risk_summary"):
            _require_type(labels, key, str, "$.compact.labels_uk", errors)
    for key in (
        "original_english",
        "speaker",
        "concise_meaning_uk",
        "confidence_summary_uk",
        "risk_summary_uk",
        "deep_notes_label_uk",
    ):
        _require_type(compact, key, str, "$.compact", errors)
    _require_number(compact, "confidence", "$.compact", errors)
    _require_type(compact, "has_deep_notes", bool, "$.compact", errors)
    _require_type(compact, "deep_note_count", int, "$.compact", errors)
    _validate_visibility(compact.get("visibility"), "compact", "$.compact.visibility", errors)
    _validate_actions(compact.get("actions"), "compact", "$.compact.actions", errors)
    _check_source_mirror(compact, source, "$.compact", errors)


def _validate_deep(deep: Any, source: Any, errors: list[str]) -> None:
    if not isinstance(deep, dict):
        errors.append("$.deep: expected object")
        return
    _require_const(deep, "mode", "deep", "$.deep", errors)
    for key in (
        "original_english",
        "speaker",
        "literary_rendering_uk",
        "explanation_uk",
        "character_voice_note_uk",
        "confidence_summary_uk",
        "risk_summary_uk",
        "spoiler_budget",
        "spoiler_budget_summary_uk",
    ):
        _require_type(deep, key, str, "$.deep", errors)
    _require_number(deep, "confidence", "$.deep", errors)
    _require_string_array(deep, "section_order_uk", "$.deep", errors, exact_length=7)
    _require_string_array(deep, "glossary_terms", "$.deep", errors)
    _require_note_array(deep, "idiom_reference_subtext_notes", "$.deep", errors)
    _require_note_array(deep, "character_tone_notes", "$.deep", errors)
    _validate_visibility(deep.get("visibility"), "deep", "$.deep.visibility", errors)
    _validate_actions(deep.get("actions"), "deep", "$.deep.actions", errors)
    _check_source_mirror(deep, source, "$.deep", errors)


def _validate_debug(debug: Any, errors: list[str]) -> None:
    if not isinstance(debug, dict):
        errors.append("$.debug: expected object")
        return
    for key in ("packet_id", "line_id", "retrieval_strategy"):
        _require_type(debug, key, str, "$.debug", errors)
    _require_number(debug, "confidence_raw", "$.debug", errors)
    _require_string_array(debug, "raw_risk_flags", "$.debug", errors)
    _require_note_array(debug, "raw_deep_notes", "$.debug", errors)
    for key in ("provider", "provider_debug", "prompt_pack", "privacy"):
        _require_type(debug, key, dict, "$.debug", errors)
    _validate_visibility(debug.get("visibility"), "debug", "$.debug.visibility", errors)
    _validate_actions(debug.get("actions"), "debug", "$.debug.actions", errors)

    raw_flags = debug.get("raw_risk_flags")
    if isinstance(raw_flags, list):
        for flag in DEBUG_REQUIRED_FLAGS:
            if flag not in raw_flags:
                errors.append(f"$.debug.raw_risk_flags: missing required raw flag {flag!r}")

    _validate_provider(debug.get("provider"), errors)
    _validate_provider_debug(debug.get("provider_debug"), errors)
    _validate_prompt_pack(debug.get("prompt_pack"), errors)
    _validate_privacy(debug.get("privacy"), errors)


def _validate_visibility(
    visibility: Any,
    mode: str,
    path: str,
    errors: list[str],
) -> None:
    if not isinstance(visibility, dict):
        errors.append(f"{path}: expected object")
        return

    expected = build_visibility_state(mode)
    expected_keys = set(expected)
    actual_keys = set(visibility)
    if actual_keys != expected_keys:
        errors.append(f"{path}: expected keys {sorted(expected_keys)}, got {sorted(actual_keys)}")

    for key in (
        "original_visible",
        "translation_visible",
        "annotations_visible",
        "debug_visible",
    ):
        _require_type(visibility, key, bool, path, errors)
    _require_type(visibility, "current_mode", str, path, errors)
    _require_string_array(visibility, "available_modes", path, errors)

    for key, expected_value in expected.items():
        if key in visibility and visibility[key] != expected_value:
            errors.append(f"{path}.{key}: expected {expected_value!r}, got {visibility[key]!r}")

    if mode in {"compact", "deep"} and visibility.get("debug_visible") is True:
        errors.append(f"{path}.debug_visible: compact/deep must keep debug hidden")
    if mode == "debug" and visibility.get("debug_visible") is not True:
        errors.append(f"{path}.debug_visible: debug mode must expose debug visibility")


def _validate_actions(actions: Any, mode: str, path: str, errors: list[str]) -> None:
    if not isinstance(actions, list):
        errors.append(f"{path}: expected array")
        return

    seen: list[str] = []
    for index, action in enumerate(actions):
        action_path = f"{path}[{index}]"
        if not isinstance(action, dict):
            errors.append(f"{action_path}: expected object")
            continue
        for field in DISALLOWED_ACTION_FIELDS:
            if field in action:
                errors.append(f"{action_path}: field {field!r} is not allowed")

        for key in ("id", "label_uk", "hint_uk"):
            _require_type(action, key, str, action_path, errors)
        _require_string_array(action, "allowed_modes", action_path, errors)
        _require_type(action, "player_facing", bool, action_path, errors)
        _require_type(action, "debug_only", bool, action_path, errors)

        action_id = action.get("id")
        if not isinstance(action_id, str):
            continue
        if action_id in seen:
            errors.append(f"{action_path}.id: duplicate action id {action_id!r}")
        seen.append(action_id)

        expected = ACTION_BY_ID.get(action_id)
        if expected is None:
            errors.append(f"{action_path}.id: unknown action id {action_id!r}")
            continue

        if mode not in expected.allowed_modes:
            errors.append(f"{action_path}.id: action {action_id!r} is not allowed in {mode!r}")
        if list(expected.allowed_modes) != action.get("allowed_modes"):
            errors.append(
                f"{action_path}.allowed_modes: expected {list(expected.allowed_modes)!r}, "
                f"got {action.get('allowed_modes')!r}"
            )
        if action.get("player_facing") != expected.player_facing:
            errors.append(
                f"{action_path}.player_facing: expected {expected.player_facing!r}, "
                f"got {action.get('player_facing')!r}"
            )
        if action.get("debug_only") != expected.debug_only:
            errors.append(
                f"{action_path}.debug_only: expected {expected.debug_only!r}, "
                f"got {action.get('debug_only')!r}"
            )
        if action.get("label_uk") != expected.label_uk:
            errors.append(f"{action_path}.label_uk: does not match canonical Ukrainian label")
        if action.get("hint_uk") != expected.hint_uk:
            errors.append(f"{action_path}.hint_uk: does not match canonical Ukrainian hint")
        if not str(action.get("label_uk", "")).strip():
            errors.append(f"{action_path}.label_uk: must not be empty")
        if not str(action.get("hint_uk", "")).strip():
            errors.append(f"{action_path}.hint_uk: must not be empty")
        if action.get("player_facing") and not _contains_ukrainian(
            f"{action.get('label_uk', '')} {action.get('hint_uk', '')}"
        ):
            errors.append(f"{action_path}: player-facing label and hint must be Ukrainian")
        if mode in {"compact", "deep"} and (
            action_id in DEBUG_ONLY_ACTION_IDS or action.get("debug_only")
        ):
            errors.append(f"{action_path}.id: debug-only action is not allowed in player modes")
        if mode in {"compact", "deep"} and action.get("player_facing") is not True:
            errors.append(
                f"{action_path}.player_facing: player modes may expose only player actions"
            )

    expected_ids = EXPECTED_ACTION_IDS_BY_MODE[mode]
    if tuple(seen) != expected_ids:
        errors.append(f"{path}: expected action ids {expected_ids!r}, got {tuple(seen)!r}")
    for action_id in seen:
        if action_id not in ACTION_IDS:
            errors.append(f"{path}: unknown action id {action_id!r}")


def _validate_provider(provider: Any, errors: list[str]) -> None:
    if not isinstance(provider, dict):
        return
    for key in ("provider_name", "provider_kind", "version"):
        _require_type(provider, key, str, "$.debug.provider", errors)
    for key in ("offline", "deterministic"):
        _require_type(provider, key, bool, "$.debug.provider", errors)


def _validate_provider_debug(provider_debug: Any, errors: list[str]) -> None:
    if not isinstance(provider_debug, dict):
        return
    for key in (
        "provider_name",
        "provider_role",
        "provider_version",
        "prompt_pack_id",
        "prompt_pack_version",
        "player_facing_language_default",
        "internal_guidance_language",
    ):
        _require_type(provider_debug, key, str, "$.debug.provider_debug", errors)
    for key in (
        "policy_note_keys",
        "policy_refs_seen",
        "quality_priorities_seen",
        "required_output_fields_seen",
    ):
        _require_string_array(provider_debug, key, "$.debug.provider_debug", errors)


def _validate_prompt_pack(prompt_pack: Any, errors: list[str]) -> None:
    if not isinstance(prompt_pack, dict):
        return
    for key in (
        "pack_id",
        "version",
        "player_facing_language_default",
        "internal_guidance_language",
    ):
        _require_type(prompt_pack, key, str, "$.debug.prompt_pack", errors)
    for key in ("policy_note_keys", "policy_refs", "quality_priorities", "required_output_fields"):
        _require_string_array(prompt_pack, key, "$.debug.prompt_pack", errors)


def _validate_privacy(privacy: Any, errors: list[str]) -> None:
    if not isinstance(privacy, dict):
        return
    for key in (
        "schema_version",
        "provider_id",
        "provider_mode",
        "prompt_pack_id",
        "prompt_pack_version",
        "context_packet_id",
        "line_id",
        "cache_key",
        "cache_root",
    ):
        _require_type(privacy, key, str, "$.debug.privacy", errors)
    for key in (
        "available",
        "dry_run",
        "calls_external_services",
        "raw_provider_payload_persisted",
    ):
        _require_type(privacy, key, bool, "$.debug.privacy", errors)
    for key in ("cache_write_plan", "request_summary", "text_metadata"):
        _require_type(privacy, key, dict, "$.debug.privacy", errors)

    cache_plan = privacy.get("cache_write_plan")
    if isinstance(cache_plan, dict):
        _validate_cache_plan(cache_plan, errors)


def _validate_cache_plan(cache_plan: dict[str, Any], errors: list[str]) -> None:
    _require_type(
        cache_plan,
        "planned_relative_path",
        str,
        "$.debug.privacy.cache_write_plan",
        errors,
    )
    for key in (
        "dry_run",
        "would_write",
        "writes_raw_payload",
        "cache_root_is_private",
        "cache_root_is_repo_ignored",
    ):
        _require_type(cache_plan, key, bool, "$.debug.privacy.cache_write_plan", errors)
    _require_string_array(
        cache_plan,
        "blocked_reasons",
        "$.debug.privacy.cache_write_plan",
        errors,
    )


def _check_source_mirror(
    payload: dict[str, Any],
    source: Any,
    path: str,
    errors: list[str],
) -> None:
    if not isinstance(source, dict):
        return
    if payload.get("original_english") != source.get("original_english"):
        errors.append(f"{path}.original_english: must mirror $.source.original_english")
    if payload.get("speaker") != source.get("speaker"):
        errors.append(f"{path}.speaker: must mirror $.source.speaker")


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
        errors.append(
            f"{path}.{key}: expected {_type_name(expected_type)}, got {type(value[key]).__name__}"
        )


def _require_number(
    value: dict[str, Any],
    key: str,
    path: str,
    errors: list[str],
) -> None:
    if key not in value:
        errors.append(f"{path}: missing required property {key!r}")
        return
    if not isinstance(value[key], (int, float)) or isinstance(value[key], bool):
        errors.append(f"{path}.{key}: expected number, got {type(value[key]).__name__}")


def _require_string_array(
    value: dict[str, Any],
    key: str,
    path: str,
    errors: list[str],
    *,
    exact_length: int | None = None,
) -> None:
    if key not in value:
        errors.append(f"{path}: missing required property {key!r}")
        return
    items = value[key]
    if not isinstance(items, list):
        errors.append(f"{path}.{key}: expected array")
        return
    if exact_length is not None and len(items) != exact_length:
        errors.append(f"{path}.{key}: expected {exact_length} items, got {len(items)}")
    for index, item in enumerate(items):
        if not isinstance(item, str):
            errors.append(f"{path}.{key}[{index}]: expected string")


def _require_note_array(
    value: dict[str, Any],
    key: str,
    path: str,
    errors: list[str],
) -> None:
    if key not in value:
        errors.append(f"{path}: missing required property {key!r}")
        return
    notes = value[key]
    if not isinstance(notes, list):
        errors.append(f"{path}.{key}: expected array")
        return
    for index, note in enumerate(notes):
        note_path = f"{path}.{key}[{index}]"
        if not isinstance(note, dict):
            errors.append(f"{note_path}: expected object")
            continue
        for note_key in ("kind", "title", "text"):
            _require_type(note, note_key, str, note_path, errors)


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


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _type_name(expected_type: type) -> str:
    if expected_type is str:
        return "string"
    if expected_type is dict:
        return "object"
    if expected_type is list:
        return "array"
    if expected_type is bool:
        return "boolean"
    if expected_type is int:
        return "integer"
    return expected_type.__name__
