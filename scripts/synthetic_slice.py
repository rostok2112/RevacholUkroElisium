from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from scripts.schema_validator import SchemaValidationError, assert_valid, load_json
except (
    ModuleNotFoundError
):  # pragma: no cover - used when running this file as a script dependency.
    from schema_validator import SchemaValidationError, assert_valid, load_json


ROOT = Path(__file__).resolve().parents[1]
FAKE_EVENT_SCHEMA = ROOT / "specs/fake-game-event.schema.json"
CONTEXT_PACKET_SCHEMA = ROOT / "specs/context-packet.schema.json"
ANNOTATION_CARD_SCHEMA = ROOT / "specs/annotation-card.schema.json"

GLOSSARY_TERMS = {
    "committee": "committee",
    "infrastructure": "infrastructure",
    "pipe": "pipe",
}

MOCK_CONCISE_MEANING_UK = "\u0423\u0441\u0442\u0430\u043d\u043e\u0432\u0430 \u043d\u0430\u0433\u043e\u0440\u043e\u0434\u0436\u0443\u0454 \u0432\u043b\u0430\u0441\u043d\u0443 \u043f\u043e\u043b\u043e\u043c\u043a\u0443 \u0439 \u0443\u0434\u0430\u0454, \u0449\u043e \u0446\u0435 \u0443\u0441\u043f\u0456\u0445."
MOCK_LITERARY_RENDERING_UK = "\u041a\u043e\u043c\u0456\u0442\u0435\u0442 \u043f\u0440\u0438\u0447\u0435\u043f\u0438\u0432 \u043c\u0435\u0434\u0430\u043b\u044c \u0434\u043e \u0442\u0440\u0443\u0431\u0438, \u0449\u043e \u043f\u0440\u043e\u0442\u0456\u043a\u0430\u043b\u0430, \u0456 \u043d\u0430\u0437\u0432\u0430\u0432 \u0446\u0435 \u0456\u043d\u0444\u0440\u0430\u0441\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u043e\u044e."
MOCK_EXPLANATION_UK = "\u0426\u0435 \u0441\u0438\u043d\u0442\u0435\u0442\u0438\u0447\u043d\u0430 \u0431\u044e\u0440\u043e\u043a\u0440\u0430\u0442\u0438\u0447\u043d\u0430 \u0456\u0440\u043e\u043d\u0456\u044f: \u043f\u0440\u043e\u0431\u043b\u0435\u043c\u0443 \u043d\u0435 \u043b\u0430\u0433\u043e\u0434\u044f\u0442\u044c, \u0430 \u043f\u0435\u0440\u0435\u0439\u043c\u0435\u043d\u043e\u0432\u0443\u044e\u0442\u044c \u043d\u0430 \u0434\u043e\u0441\u044f\u0433\u043d\u0435\u043d\u043d\u044f."
MOCK_CHARACTER_VOICE_UK = "\u0413\u043e\u043b\u043e\u0441 \u0441\u0443\u0445\u0438\u0439 \u0456 \u043a\u0430\u043d\u0446\u0435\u043b\u044f\u0440\u0441\u044c\u043a\u0438\u0439, \u043d\u0456\u0431\u0438 \u0441\u0432\u0456\u0434\u043e\u043a \u0437\u0432\u0456\u0442\u0443\u0454 \u043f\u0440\u043e \u0430\u0431\u0441\u0443\u0440\u0434 \u0431\u0435\u0437 \u043f\u0456\u0434\u0432\u0438\u0449\u0435\u043d\u043d\u044f \u0442\u043e\u043d\u0443."


def load_default_fake_event() -> dict[str, Any]:
    return load_json(ROOT / "tests/fixtures/fake_game_event.synthetic.json")


def validate_fake_game_event(event: dict[str, Any]) -> None:
    assert_valid(event, load_json(FAKE_EVENT_SCHEMA))


def build_context_packet(event: dict[str, Any]) -> dict[str, Any]:
    validate_fake_game_event(event)
    line_id = _line_id(event)
    skill_voice = event.get("skill_voice", {})
    if not isinstance(skill_voice, dict):
        skill_voice = {}

    packet = {
        "packet_id": f"context.{event['event_id']}",
        "game": {
            "title": "Disco Elysium: The Final Cut",
            "version": "synthetic",
        },
        "current_line": {
            "line_id": line_id,
            "source_text": event["raw_english_text"],
            "speaker": event["speaker"],
            "speaker_type": event.get("speaker_type", "unknown"),
            "conversation_id": event["conversation_id"],
            "location": event["scene_id"],
            "skill": skill_voice.get("skill"),
            "audio_ref": skill_voice.get("audio_ref"),
        },
        "visible_history": _nearby_lines(event, "previous_visible"),
        "nearby_tree": _nearby_lines(event, "nearby_branch"),
        "player_options": _nearby_lines(event, "player_option"),
        "glossary_hits": detect_glossary_hits(event),
        "spoiler_budget": "none",
        "retrieval": {
            "strategy": "synthetic_event_adapter_v1",
            "sources": ["synthetic_fake_game_event"],
        },
    }
    assert_valid(packet, load_json(CONTEXT_PACKET_SCHEMA))
    return packet


def build_mock_annotation_card(context_packet: dict[str, Any]) -> dict[str, Any]:
    assert_valid(context_packet, load_json(CONTEXT_PACKET_SCHEMA))
    current_line = context_packet["current_line"]
    source_text = current_line["source_text"]
    glossary_terms = list(context_packet.get("glossary_hits", []))

    card = {
        "line_id": current_line["line_id"],
        "source_text": source_text,
        "original_english": source_text,
        "translation_uk": MOCK_LITERARY_RENDERING_UK,
        "concise_meaning_uk": MOCK_CONCISE_MEANING_UK,
        "literary_rendering_uk": MOCK_LITERARY_RENDERING_UK,
        "literal_gloss": "The committee decorates a leaking pipe and calls the failure public works.",
        "quick_note": MOCK_EXPLANATION_UK,
        "explanation_uk": MOCK_EXPLANATION_UK,
        "character_voice_note_uk": MOCK_CHARACTER_VOICE_UK,
        "deep_notes": [
            {
                "kind": "idiom",
                "text": "The invented image treats cosmetic recognition as a substitute for repair.",
            },
            {
                "kind": "reference",
                "text": "Synthetic civic-bureaucracy reference only; not sourced from game dialogue.",
            },
            {
                "kind": "skill_voice",
                "text": MOCK_CHARACTER_VOICE_UK,
            },
            {
                "kind": "translation_choice",
                "text": "Mock output keeps the deadpan structure and does not localize the setting.",
            },
        ],
        "ukrainian_cultural_equivalents": [],
        "glossary_terms": glossary_terms,
        "confidence": 0.78,
        "risk_flags": [
            "synthetic_fixture",
            "deterministic_mock_pipeline",
            "needs_human_review_before_real_use",
        ],
        "quality": {
            "semantic_accuracy": 4,
            "voice_preservation": 4,
            "ukrainian_naturalness": 3,
            "spoiler_safety": 5,
            "needs_human_review": False,
        },
    }
    assert_valid(card, load_json(ANNOTATION_CARD_SCHEMA))
    return card


def build_overlay_demo_model(
    context_packet: dict[str, Any],
    annotation_card: dict[str, Any],
) -> dict[str, Any]:
    assert_valid(context_packet, load_json(CONTEXT_PACKET_SCHEMA))
    assert_valid(annotation_card, load_json(ANNOTATION_CARD_SCHEMA))

    current_line = context_packet["current_line"]
    sections = [
        {
            "kind": note["kind"],
            "title": _section_title(note["kind"]),
            "text": note["text"],
        }
        for note in annotation_card.get("deep_notes", [])
    ]

    return {
        "schema_version": "overlay-demo.v1",
        "line_id": annotation_card["line_id"],
        "source": {
            "original_english": current_line["source_text"],
            "speaker": current_line.get("speaker"),
            "scene_id": current_line.get("location"),
            "conversation_id": current_line.get("conversation_id"),
        },
        "toggles": {
            "show_original": True,
            "show_translation": True,
            "available_sections": [section["kind"] for section in sections],
        },
        "modes": {
            "compact": {
                "mode": "compact",
                "translation_uk": annotation_card["translation_uk"],
                "concise_meaning_uk": annotation_card.get("concise_meaning_uk"),
                "annotation_available": bool(sections),
                "confidence": annotation_card.get("confidence"),
            },
            "deep_explanation": {
                "mode": "deep_explanation",
                "original_english": current_line["source_text"],
                "translation_uk": annotation_card["translation_uk"],
                "literary_rendering_uk": annotation_card.get("literary_rendering_uk"),
                "explanation_uk": annotation_card.get(
                    "explanation_uk", annotation_card["quick_note"]
                ),
                "character_voice_note_uk": annotation_card.get("character_voice_note_uk"),
                "sections": sections,
                "glossary_terms": annotation_card.get("glossary_terms", []),
                "risk_flags": annotation_card.get("risk_flags", []),
            },
        },
        "debug": {
            "packet_id": context_packet["packet_id"],
            "retrieval_strategy": context_packet["retrieval"]["strategy"],
            "mock_pipeline": True,
        },
    }


def run_synthetic_slice(event: dict[str, Any] | None = None) -> dict[str, Any]:
    fake_event = deepcopy(event) if event is not None else load_default_fake_event()
    context_packet = build_context_packet(fake_event)
    annotation_card = build_mock_annotation_card(context_packet)
    overlay_demo = build_overlay_demo_model(context_packet, annotation_card)
    return {
        "fake_game_event": fake_event,
        "context_packet": context_packet,
        "annotation_card": annotation_card,
        "overlay_demo": overlay_demo,
    }


def detect_glossary_hits(event: dict[str, Any]) -> list[str]:
    text_parts = [event.get("raw_english_text", "")]
    for nearby in event.get("nearby_context", []):
        if isinstance(nearby, dict):
            text_parts.append(nearby.get("raw_english_text", ""))
    full_text = " ".join(text_parts).lower()
    return sorted(term_id for source, term_id in GLOSSARY_TERMS.items() if source in full_text)


def _nearby_lines(event: dict[str, Any], relation: str) -> list[dict[str, Any]]:
    lines = []
    for nearby in event.get("nearby_context", []):
        if not isinstance(nearby, dict) or nearby.get("relation") != relation:
            continue
        lines.append(
            {
                "line_id": _line_id(nearby),
                "source_text": nearby["raw_english_text"],
                "speaker": nearby.get("speaker"),
                "relation": relation,
            }
        )
    return lines


def _line_id(value: dict[str, Any]) -> str:
    line_id = value.get("line_id") or value.get("synthetic_line_id")
    if not isinstance(line_id, str) or not line_id:
        raise SchemaValidationError("Missing line_id or synthetic_line_id")
    return line_id


def _section_title(kind: str) -> str:
    titles = {
        "idiom": "Idiom/Subtext",
        "reference": "Reference",
        "skill_voice": "Character Voice",
        "translation_choice": "Translation Choice",
    }
    return titles.get(kind, kind.replace("_", " ").title())
