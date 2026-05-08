from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

try:
    from scripts.provider_pipeline import ProviderPipelineError, build_provider_request
    from scripts.provider_privacy import ProviderPrivacyError, build_provider_privacy_envelope
    from scripts.provider_runtime_safety import (
        ProviderRuntimeSafetyError,
        build_provider_execution_plan,
    )
    from scripts.schema_validator import assert_valid, load_json
    from scripts.synthetic_slice import ANNOTATION_CARD_SCHEMA, CONTEXT_PACKET_SCHEMA, ROOT
    from scripts.validate_config import load_config
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path dependency.
    from provider_pipeline import ProviderPipelineError, build_provider_request
    from provider_privacy import ProviderPrivacyError, build_provider_privacy_envelope
    from provider_runtime_safety import ProviderRuntimeSafetyError, build_provider_execution_plan
    from schema_validator import assert_valid, load_json
    from synthetic_slice import ANNOTATION_CARD_SCHEMA, CONTEXT_PACKET_SCHEMA, ROOT
    from validate_config import load_config


OVERLAY_SCHEMA_VERSION = "local-overlay-prototype.v1"
DEFAULT_CONFIG = ROOT / "config/revachol.example.toml"
MODES = ("compact", "deep", "debug")

NOTE_TITLES = {
    "idiom": "Idiom",
    "reference": "Reference",
    "subtext": "Subtext",
    "skill_voice": "Character Voice",
    "tone": "Tone",
    "translation_choice": "Translation Choice",
}

IDIOM_REFERENCE_KINDS = {"idiom", "reference", "subtext", "translation_choice"}
TONE_VOICE_KINDS = {"skill_voice", "tone"}


class LocalOverlayPrototypeError(ValueError):
    """Raised when the local overlay prototype cannot build a safe view."""


def build_overlay_view_model(
    context_packet: dict[str, Any],
    annotation_card: dict[str, Any],
    *,
    mode: str = "compact",
    include_privacy_summary: bool = True,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    if mode not in MODES:
        raise LocalOverlayPrototypeError(f"Unsupported overlay mode: {mode}")

    assert_valid(context_packet, load_json(CONTEXT_PACKET_SCHEMA))
    assert_valid(annotation_card, load_json(ANNOTATION_CARD_SCHEMA))

    current_line = context_packet["current_line"]
    notes = _notes(annotation_card)
    source = {
        "original_english": current_line["source_text"],
        "speaker": current_line.get("speaker"),
        "scene_id": current_line.get("location"),
        "conversation_id": current_line.get("conversation_id"),
        "line_id": current_line.get("line_id"),
    }
    risk_flags = list(annotation_card.get("risk_flags", []))
    glossary_terms = list(annotation_card.get("glossary_terms", []))

    debug = {
        "packet_id": context_packet["packet_id"],
        "line_id": current_line["line_id"],
        "retrieval_strategy": context_packet["retrieval"]["strategy"],
        "provider": annotation_card.get("provider", {}),
        "provider_debug": annotation_card.get("provider_debug", {}),
        "prompt_pack": annotation_card.get("prompt_pack", {}),
        "privacy": (
            build_safe_privacy_summary(context_packet, config_path=config_path)
            if include_privacy_summary
            else {"available": False, "reason": "disabled"}
        ),
    }

    return {
        "schema_version": OVERLAY_SCHEMA_VERSION,
        "mode": mode,
        "source": source,
        "compact": {
            "mode": "compact",
            "original_english": source["original_english"],
            "speaker": source["speaker"],
            "concise_meaning_uk": annotation_card.get("concise_meaning_uk"),
            "confidence": annotation_card.get("confidence"),
            "risk_flags": risk_flags,
            "has_deep_notes": bool(notes),
            "deep_note_count": len(notes),
        },
        "deep": {
            "mode": "deep",
            "original_english": source["original_english"],
            "speaker": source["speaker"],
            "literary_rendering_uk": annotation_card.get("literary_rendering_uk"),
            "explanation_uk": annotation_card.get("explanation_uk"),
            "idiom_reference_subtext_notes": [
                note for note in notes if note["kind"] in IDIOM_REFERENCE_KINDS
            ],
            "character_tone_notes": [note for note in notes if note["kind"] in TONE_VOICE_KINDS],
            "character_voice_note_uk": annotation_card.get("character_voice_note_uk"),
            "glossary_terms": glossary_terms,
            "confidence": annotation_card.get("confidence"),
            "risk_flags": risk_flags,
            "spoiler_budget": context_packet.get("spoiler_budget"),
        },
        "debug": debug,
    }


def build_safe_privacy_summary(
    context_packet: dict[str, Any],
    *,
    config_path: Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    try:
        config = load_config(config_path)
        execution_plan = build_provider_execution_plan(config, provider_id="mock")
        provider_request = build_provider_request(context_packet, provider_name="mock")
        envelope = build_provider_privacy_envelope(provider_request, config, execution_plan)
    except (
        OSError,
        ProviderPipelineError,
        ProviderPrivacyError,
        ProviderRuntimeSafetyError,
        ValueError,
    ) as exc:
        return {
            "available": False,
            "error": str(exc),
            "dry_run": True,
            "calls_external_services": False,
        }

    cache_plan = envelope["cache_write_plan"]
    return {
        "available": True,
        "schema_version": envelope["schema_version"],
        "provider_id": envelope["provider_id"],
        "provider_mode": envelope["provider_mode"],
        "prompt_pack_id": envelope["prompt_pack_id"],
        "prompt_pack_version": envelope["prompt_pack_version"],
        "context_packet_id": envelope["context_packet_id"],
        "line_id": envelope["line_id"],
        "cache_key": envelope["cache_key"],
        "cache_root": envelope["cache_root"],
        "cache_write_plan": {
            "planned_relative_path": cache_plan["planned_relative_path"],
            "dry_run": cache_plan["dry_run"],
            "would_write": cache_plan["would_write"],
            "writes_raw_payload": cache_plan["writes_raw_payload"],
            "cache_root_is_private": cache_plan["cache_root_is_private"],
            "cache_root_is_repo_ignored": cache_plan["cache_root_is_repo_ignored"],
            "blocked_reasons": list(cache_plan.get("blocked_reasons", [])),
        },
        "request_summary": {
            "glossary_hint_count": envelope["request_summary"]["glossary_hint_count"],
            "requested_output_field_count": envelope["request_summary"][
                "requested_output_field_count"
            ],
            "quality_priority_count": envelope["request_summary"]["quality_priority_count"],
            "prompt_pack_section_count": envelope["request_summary"]["prompt_pack_section_count"],
        },
        "text_metadata": {
            "original_english_length": envelope["text_metadata"]["original_english_length"],
            "visible_history_count": envelope["text_metadata"]["visible_history_count"],
            "nearby_tree_count": envelope["text_metadata"]["nearby_tree_count"],
            "player_options_count": envelope["text_metadata"]["player_options_count"],
        },
        "dry_run": envelope["dry_run"],
        "calls_external_services": envelope["calls_external_services"],
        "raw_provider_payload_persisted": envelope["raw_provider_payload_persisted"],
    }


def render_overlay_html(view_model: dict[str, Any]) -> str:
    mode = view_model.get("mode")
    if mode not in MODES:
        raise LocalOverlayPrototypeError(f"Unsupported overlay mode: {mode}")

    body = {
        "compact": _render_compact_mode,
        "deep": _render_deep_mode,
        "debug": _render_debug_mode,
    }[mode](view_model)

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="uk">',
            "<head>",
            '  <meta charset="utf-8">',
            "  <title>Revachol Local Overlay Prototype</title>",
            "  <style>",
            "    body { margin: 0; background: #111; color: #eee; font-family: sans-serif; }",
            "    main { max-width: 760px; margin: 2rem auto; padding: 0 1rem; }",
            "    .overlay { border: 1px solid #555; padding: 1rem; background: #1b1b1b; }",
            "    .label { color: #aaa; font-size: 0.85rem; text-transform: uppercase; }",
            "    .source { color: #ddd; }",
            "    .uk { color: #f2f2f2; font-size: 1.1rem; }",
            "    .flag { display: inline-block; border: 1px solid #666; padding: 0.1rem 0.35rem; margin: 0.1rem; }",
            "    section { margin-top: 1rem; }",
            "    h1, h2, h3, p { margin-top: 0; }",
            "    code { background: #2b2b2b; padding: 0.1rem 0.25rem; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <main>",
            f"    <h1>{_text('Local Overlay Prototype')}</h1>",
            f'    <p class="label">{_text("Mode")}: {_text(mode)}</p>',
            body,
            "  </main>",
            "</body>",
            "</html>",
        ]
    )


def _render_compact_mode(view_model: dict[str, Any]) -> str:
    compact = view_model["compact"]
    return "\n".join(
        [
            '    <section class="overlay" id="compact-mode">',
            f'      <p class="label">{_text("Original English")}</p>',
            f'      <p class="source">{_text(compact.get("original_english"))}</p>',
            f'      <p class="label">{_text("Ukrainian concise meaning")}</p>',
            f'      <p class="uk">{_text(compact.get("concise_meaning_uk"))}</p>',
            "      <section>",
            f"        <p><strong>{_text('Confidence')}:</strong> {_text(compact.get('confidence'))}</p>",
            f"        <p><strong>{_text('Risk flags')}:</strong> {_flags(compact.get('risk_flags'))}</p>",
            f"        <p><strong>{_text('Deep notes available')}:</strong> {_text(compact.get('has_deep_notes'))}</p>",
            "      </section>",
            "    </section>",
        ]
    )


def _render_deep_mode(view_model: dict[str, Any]) -> str:
    deep = view_model["deep"]
    return "\n".join(
        [
            '    <section class="overlay" id="deep-mode">',
            f'      <p class="label">{_text("Original English")}</p>',
            f'      <p class="source">{_text(deep.get("original_english"))}</p>',
            f"      <h2>{_text('Literary Ukrainian Rendering')}</h2>",
            f'      <p class="uk">{_text(deep.get("literary_rendering_uk"))}</p>',
            f"      <h2>{_text('Deep Explanation')}</h2>",
            f"      <p>{_text(deep.get('explanation_uk'))}</p>",
            f"      <h3>{_text('Idiom / Reference / Subtext Notes')}</h3>",
            _note_list(deep.get("idiom_reference_subtext_notes")),
            f"      <h3>{_text('Tone / Character Voice')}</h3>",
            f"      <p>{_text(deep.get('character_voice_note_uk'))}</p>",
            _note_list(deep.get("character_tone_notes")),
            f"      <p><strong>{_text('Glossary terms')}:</strong> {_flags(deep.get('glossary_terms'))}</p>",
            f"      <p><strong>{_text('Spoiler budget')}:</strong> {_text(deep.get('spoiler_budget'))}</p>",
            f"      <p><strong>{_text('Risk flags')}:</strong> {_flags(deep.get('risk_flags'))}</p>",
            "    </section>",
        ]
    )


def _render_debug_mode(view_model: dict[str, Any]) -> str:
    debug = view_model["debug"]
    provider = _as_dict(debug.get("provider"))
    provider_debug = _as_dict(debug.get("provider_debug"))
    prompt_pack = _as_dict(debug.get("prompt_pack"))
    privacy = _as_dict(debug.get("privacy"))
    cache_plan = _as_dict(privacy.get("cache_write_plan"))

    return "\n".join(
        [
            '    <section class="overlay" id="debug-mode">',
            f"      <h2>{_text('Debug / Developer Metadata')}</h2>",
            f"      <p><strong>{_text('Packet')}:</strong> {_text(debug.get('packet_id'))}</p>",
            f"      <p><strong>{_text('Line')}:</strong> {_text(debug.get('line_id'))}</p>",
            f"      <p><strong>{_text('Retrieval')}:</strong> {_text(debug.get('retrieval_strategy'))}</p>",
            f"      <h3>{_text('Provider')}</h3>",
            f"      <p><strong>{_text('Name')}:</strong> {_text(provider_debug.get('provider_name') or provider.get('provider_name'))}</p>",
            f"      <p><strong>{_text('Role')}:</strong> {_text(provider_debug.get('provider_role') or provider.get('provider_kind'))}</p>",
            f"      <p><strong>{_text('Offline')}:</strong> {_text(provider.get('offline'))}</p>",
            f"      <h3>{_text('Prompt Pack')}</h3>",
            f"      <p><strong>{_text('Pack')}:</strong> {_text(prompt_pack.get('pack_id') or provider_debug.get('prompt_pack_id'))}</p>",
            f"      <p><strong>{_text('Version')}:</strong> {_text(prompt_pack.get('version') or provider_debug.get('prompt_pack_version'))}</p>",
            f"      <p><strong>{_text('Player-facing language')}:</strong> {_text(prompt_pack.get('player_facing_language_default') or provider_debug.get('player_facing_language_default'))}</p>",
            f"      <p><strong>{_text('Policy keys')}:</strong> {_flags(prompt_pack.get('policy_note_keys') or provider_debug.get('policy_note_keys'))}</p>",
            f"      <h3>{_text('Privacy / Cache Dry Run')}</h3>",
            f"      <p><strong>{_text('Privacy envelope available')}:</strong> {_text(privacy.get('available'))}</p>",
            f"      <p><strong>{_text('Cache key')}:</strong> <code>{_text(privacy.get('cache_key'))}</code></p>",
            f"      <p><strong>{_text('Cache root')}:</strong> {_text(privacy.get('cache_root'))}</p>",
            f"      <p><strong>{_text('Planned relative path')}:</strong> {_text(cache_plan.get('planned_relative_path'))}</p>",
            f"      <p><strong>{_text('Dry run')}:</strong> {_text(privacy.get('dry_run'))}</p>",
            f"      <p><strong>{_text('Would write')}:</strong> {_text(cache_plan.get('would_write'))}</p>",
            f"      <p><strong>{_text('Writes raw payload')}:</strong> {_text(cache_plan.get('writes_raw_payload'))}</p>",
            f"      <p><strong>{_text('Calls external services')}:</strong> {_text(privacy.get('calls_external_services'))}</p>",
            "    </section>",
        ]
    )


def _notes(annotation_card: dict[str, Any]) -> list[dict[str, str]]:
    notes = []
    for note in annotation_card.get("deep_notes", []):
        if not isinstance(note, dict):
            continue
        kind = str(note.get("kind", "note"))
        notes.append(
            {
                "kind": kind,
                "title": NOTE_TITLES.get(kind, kind.replace("_", " ").title()),
                "text": str(note.get("text", "")),
            }
        )
    return notes


def _note_list(notes: Any) -> str:
    if not isinstance(notes, list) or not notes:
        return "      <p></p>"
    items = "\n".join(
        [
            "        <li>"
            f"<strong>{_text(note.get('title'))}</strong> "
            f"<code>{_text(note.get('kind'))}</code>: {_text(note.get('text'))}"
            "</li>"
            for note in notes
            if isinstance(note, dict)
        ]
    )
    return "\n".join(["      <ul>", items, "      </ul>"])


def _flags(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    return "".join(f'<span class="flag">{_text(value)}</span> ' for value in values)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=True)
