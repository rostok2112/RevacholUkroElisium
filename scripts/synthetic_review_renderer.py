from __future__ import annotations

from html import escape
from typing import Any


def render_review_html(slice_result: dict[str, Any]) -> str:
    overlay = slice_result["overlay_demo"]
    annotation = slice_result["annotation_card"]
    context = slice_result["context_packet"]
    compact = overlay["modes"]["compact"]
    deep = overlay["modes"]["deep_explanation"]

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "<head>",
            '  <meta charset="utf-8">',
            "  <title>Revachol Synthetic Review</title>",
            "  <style>",
            "    body { font-family: sans-serif; max-width: 900px; margin: 2rem auto; line-height: 1.5; }",
            "    section { border: 1px solid #bbb; padding: 1rem; margin: 1rem 0; }",
            "    h1, h2, h3 { margin-top: 0; }",
            "    code, .flag { background: #eee; padding: 0.1rem 0.3rem; }",
            "    .muted { color: #555; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>Revachol Synthetic Review</h1>",
            f'  <p class="muted">Line: {_text(overlay["line_id"])}</p>',
            _render_source(overlay),
            _render_visibility(overlay),
            _render_compact(compact),
            _render_deep(deep),
            _render_quality(annotation),
            _render_debug(context, overlay),
            "</body>",
            "</html>",
        ]
    )


def _render_source(overlay: dict[str, Any]) -> str:
    source = overlay["source"]
    return "\n".join(
        [
            '  <section id="source">',
            "    <h2>Original</h2>",
            f"    <p><strong>Speaker:</strong> {_text(source.get('speaker'))}</p>",
            f"    <p><strong>English:</strong> {_text(source.get('original_english'))}</p>",
            f"    <p><strong>Scene:</strong> {_text(source.get('scene_id'))}</p>",
            f"    <p><strong>Conversation:</strong> {_text(source.get('conversation_id'))}</p>",
            "  </section>",
        ]
    )


def _render_visibility(overlay: dict[str, Any]) -> str:
    toggles = overlay["toggles"]
    sections = ", ".join(_text(section) for section in toggles.get("available_sections", []))
    return "\n".join(
        [
            '  <section id="visibility">',
            "    <h2>Visibility States</h2>",
            f"    <p><strong>Original visible:</strong> {_text(toggles.get('show_original'))}</p>",
            f"    <p><strong>Translation visible:</strong> {_text(toggles.get('show_translation'))}</p>",
            f"    <p><strong>Available annotation sections:</strong> {sections}</p>",
            "  </section>",
        ]
    )


def _render_compact(compact: dict[str, Any]) -> str:
    return "\n".join(
        [
            '  <section id="compact-mode">',
            "    <h2>Compact Mode</h2>",
            f"    <p><strong>Compact Ukrainian meaning:</strong> {_text(compact.get('concise_meaning_uk'))}</p>",
            f"    <p><strong>Literary Ukrainian rendering:</strong> {_text(compact.get('translation_uk'))}</p>",
            f"    <p><strong>Annotation available:</strong> {_text(compact.get('annotation_available'))}</p>",
            f"    <p><strong>Confidence:</strong> {_text(compact.get('confidence'))}</p>",
            "  </section>",
        ]
    )


def _render_deep(deep: dict[str, Any]) -> str:
    section_items = "\n".join(
        [
            "      <li>"
            f"<strong>{_text(section.get('title'))}</strong> "
            f"<code>{_text(section.get('kind'))}</code>: {_text(section.get('text'))}"
            "</li>"
            for section in deep.get("sections", [])
        ]
    )
    glossary = "".join(
        f'<span class="flag">{_text(term)}</span> ' for term in deep.get("glossary_terms", [])
    )
    risks = "".join(
        f'<span class="flag">{_text(flag)}</span> ' for flag in deep.get("risk_flags", [])
    )
    return "\n".join(
        [
            '  <section id="deep-explanation-mode">',
            "    <h2>Deep Explanation Mode</h2>",
            f"    <p><strong>Original English:</strong> {_text(deep.get('original_english'))}</p>",
            f"    <p><strong>Literary Ukrainian rendering:</strong> {_text(deep.get('literary_rendering_uk'))}</p>",
            f"    <p><strong>Deep explanation:</strong> {_text(deep.get('explanation_uk'))}</p>",
            f"    <p><strong>Character voice note:</strong> {_text(deep.get('character_voice_note_uk'))}</p>",
            "    <h3>Idiom / Reference / Voice Notes</h3>",
            "    <ul>",
            section_items,
            "    </ul>",
            f"    <p><strong>Glossary terms:</strong> {glossary}</p>",
            f"    <p><strong>Risk flags:</strong> {risks}</p>",
            "  </section>",
        ]
    )


def _render_quality(annotation: dict[str, Any]) -> str:
    quality = annotation.get("quality", {})
    quality_items = "\n".join(
        f"      <li><strong>{_text(key)}:</strong> {_text(value)}</li>"
        for key, value in sorted(quality.items())
    )
    return "\n".join(
        [
            '  <section id="quality">',
            "    <h2>Quality Snapshot</h2>",
            f"    <p><strong>Confidence:</strong> {_text(annotation.get('confidence'))}</p>",
            "    <ul>",
            quality_items,
            "    </ul>",
            "  </section>",
        ]
    )


def _render_debug(context: dict[str, Any], overlay: dict[str, Any]) -> str:
    debug = overlay.get("debug", {})
    provider = _as_dict(debug.get("provider"))
    provider_debug = _as_dict(debug.get("provider_debug"))
    prompt_pack = _as_dict(debug.get("prompt_pack"))
    provider_name = provider_debug.get("provider_name") or provider.get("provider_name")
    provider_role = provider_debug.get("provider_role") or provider.get("provider_kind")
    pack_id = prompt_pack.get("pack_id") or provider_debug.get("prompt_pack_id")
    pack_version = prompt_pack.get("version") or provider_debug.get("prompt_pack_version")
    language_default = prompt_pack.get("player_facing_language_default") or provider_debug.get(
        "player_facing_language_default"
    )
    policy_keys = (
        prompt_pack.get("policy_note_keys") or provider_debug.get("policy_note_keys") or []
    )
    return "\n".join(
        [
            '  <section id="debug">',
            "    <h2>Debug</h2>",
            f"    <p><strong>Packet:</strong> {_text(context.get('packet_id'))}</p>",
            f"    <p><strong>Retrieval strategy:</strong> {_text(debug.get('retrieval_strategy'))}</p>",
            f"    <p><strong>Mock pipeline:</strong> {_text(debug.get('mock_pipeline'))}</p>",
            f"    <p><strong>Provider:</strong> {_text(provider_name)}</p>",
            f"    <p><strong>Provider role:</strong> {_text(provider_role)}</p>",
            f"    <p><strong>Prompt pack:</strong> {_text(pack_id)}</p>",
            f"    <p><strong>Prompt pack version:</strong> {_text(pack_version)}</p>",
            f"    <p><strong>Player-facing language default:</strong> {_text(language_default)}</p>",
            f"    <p><strong>Policy note keys:</strong> {_flags(policy_keys)}</p>",
            "  </section>",
        ]
    )


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _flags(values: Any) -> str:
    if not isinstance(values, list):
        return ""
    return "".join(f'<span class="flag">{_text(value)}</span> ' for value in values)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value), quote=True)
