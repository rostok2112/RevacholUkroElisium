from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from scripts.provider_pipeline import (
        PLAYER_FACING_LANGUAGE_DEFAULT,
        POLICY_FOCUS_KEYS,
        QUALITY_PRIORITIES,
        REQUESTED_OUTPUT_FIELDS,
        run_provider_pipeline,
    )
    from scripts.schema_validator import assert_valid, load_json
    from scripts.synthetic_review_renderer import render_review_html
    from scripts.synthetic_slice import (
        ANNOTATION_CARD_SCHEMA,
        CONTEXT_PACKET_SCHEMA,
        build_context_packet,
        build_overlay_demo_model,
    )
except ModuleNotFoundError:  # pragma: no cover - used when run as a script dependency.
    from provider_pipeline import (
        PLAYER_FACING_LANGUAGE_DEFAULT,
        POLICY_FOCUS_KEYS,
        QUALITY_PRIORITIES,
        REQUESTED_OUTPUT_FIELDS,
        run_provider_pipeline,
    )
    from schema_validator import assert_valid, load_json
    from synthetic_review_renderer import render_review_html
    from synthetic_slice import (
        ANNOTATION_CARD_SCHEMA,
        CONTEXT_PACKET_SCHEMA,
        build_context_packet,
        build_overlay_demo_model,
    )


SCORE_KEYS = (
    "section_coverage",
    "compact_brevity",
    "deep_explanation_presence",
    "glossary_coverage",
    "risk_flag_coverage",
    "spoiler_safety",
    "prompt_pack_metadata",
    "required_output_field_coverage",
    "quality_priority_coverage",
    "policy_coverage",
    "provider_debug_coverage",
    "renderer_completeness",
)

STRUCTURAL_EVAL_DISCLAIMER = (
    "Synthetic evals are deterministic structural/coverage checks only. "
    "They verify prompt-pack policy wiring but are not semantic translation quality, "
    "not an LLM judge, and not production evaluation."
)

FORBIDDEN_SYNTHETIC_MARKERS = (
    "data/extracted",
    "data/local",
    ".local-game",
    "private-data",
    "llm-cache",
    "http://",
    "https://",
    "steamapps",
    "database.json",
)


@dataclass(frozen=True)
class SyntheticEvalCase:
    case_id: str
    name: str
    fake_event: dict[str, Any]
    required_sections: tuple[str, ...]
    expected_glossary_terms: tuple[str, ...]
    expected_risk_flags: tuple[str, ...]
    expected_spoiler_budget: str
    compact_max_chars: int
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "name": self.name,
            "coverage_requirements": {
                "required_sections": list(self.required_sections),
                "expected_glossary_terms": list(self.expected_glossary_terms),
                "expected_risk_flags": list(self.expected_risk_flags),
                "expected_spoiler_budget": self.expected_spoiler_budget,
                "compact_max_chars": self.compact_max_chars,
            },
            "notes": self.notes,
            "fake_game_event": self.fake_event,
        }


@dataclass
class SyntheticEvalResult:
    case_id: str
    name: str
    notes: str
    scores: dict[str, float]
    failures: list[str] = field(default_factory=list)
    review_html: str = ""
    slice_result: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures

    @property
    def overall_score(self) -> float:
        return round(sum(self.scores.values()) / len(SCORE_KEYS), 3)

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "name": self.name,
            "notes": self.notes,
            "passed": self.passed,
            "overall_score": self.overall_score,
            "scores": self.scores,
            "failures": self.failures,
        }


def get_synthetic_eval_cases() -> list[SyntheticEvalCase]:
    sections = ("idiom", "reference", "skill_voice", "translation_choice")
    risk_flags = (
        "synthetic_fixture",
        "mock_provider",
        "deterministic_mock_provider",
        "needs_human_review_before_real_use",
        "prompt_pack_guided",
    )
    return [
        SyntheticEvalCase(
            case_id="synthetic.eval.m1c.bureaucratic_irony",
            name="Bureaucratic irony",
            fake_event=_event(
                case_id="bureaucratic_irony",
                speaker="Synthetic Clerk",
                speaker_type="npc",
                text="The committee named the broken pipe a wellness fountain and filed it under infrastructure.",
                scene="synthetic.scene.records-window",
                conversation="synthetic.conv.paperwork-water",
                previous="A form insists the hallway is dry because the form is dry.",
                option="Ask whether the committee has met the pipe in person.",
                skill="Composure",
                voice="deadpan municipal witness",
            ),
            required_sections=sections,
            expected_glossary_terms=("committee", "infrastructure", "pipe"),
            expected_risk_flags=risk_flags,
            expected_spoiler_budget="none",
            compact_max_chars=160,
            notes="Checks dry bureaucratic irony, glossary hits, compact/deep coverage.",
        ),
        SyntheticEvalCase(
            case_id="synthetic.eval.m1c.idiom_subtext",
            name="Idiom and subtext",
            fake_event=_event(
                case_id="idiom_subtext",
                speaker="Synthetic Neighbor",
                speaker_type="npc",
                text="The pipe coughed like a clerk with a secret, and the committee applauded the paperwork.",
                scene="synthetic.scene.stairwell",
                conversation="synthetic.conv.secret-pipe",
                previous="Someone put a ribbon on the drip and called it weather.",
                option="Ask what the pipe is trying not to say.",
                skill="Rhetoric",
                voice="playful suspicion",
            ),
            required_sections=sections,
            expected_glossary_terms=("committee", "pipe"),
            expected_risk_flags=risk_flags,
            expected_spoiler_budget="none",
            compact_max_chars=160,
            notes="Checks that idiom/subtext annotation sections exist in the review flow.",
        ),
        SyntheticEvalCase(
            case_id="synthetic.eval.m1c.character_voice",
            name="Character voice",
            fake_event=_event(
                case_id="character_voice",
                speaker="Synthetic Inner Voice",
                speaker_type="skill",
                text="Steady. The pipe is losing water; the committee is losing face.",
                scene="synthetic.scene.quiet-corner",
                conversation="synthetic.conv.inner-register",
                previous="Your jaw remains professional while the ceiling practices rain.",
                option="Maintain eye contact with the leak.",
                skill="Composure",
                voice="controlled inward commentary",
            ),
            required_sections=sections,
            expected_glossary_terms=("committee", "pipe"),
            expected_risk_flags=risk_flags,
            expected_spoiler_budget="none",
            compact_max_chars=160,
            notes="Checks skill/voice metadata preservation and voice-note coverage.",
        ),
        SyntheticEvalCase(
            case_id="synthetic.eval.m1c.reference_like_philosophy",
            name="Reference-like political phrasing",
            fake_event=_event(
                case_id="reference_like_philosophy",
                speaker="Synthetic Lecturer",
                speaker_type="npc",
                text="The committee declared the pipe a public consensus and called infrastructure a feeling.",
                scene="synthetic.scene.civic-hall",
                conversation="synthetic.conv.consensus-pipe",
                previous="A poster asks citizens to believe harder in maintenance.",
                option="Ask if the feeling requires a budget.",
                skill="Conceptualization",
                voice="dry civic abstraction",
            ),
            required_sections=sections,
            expected_glossary_terms=("committee", "infrastructure", "pipe"),
            expected_risk_flags=risk_flags,
            expected_spoiler_budget="none",
            compact_max_chars=160,
            notes="Checks reference-like phrasing without using real-world/game source text.",
        ),
        SyntheticEvalCase(
            case_id="synthetic.eval.m1c.ukrainian_fields",
            name="Ukrainian field presence",
            fake_event=_event(
                case_id="ukrainian_fields",
                speaker="Synthetic Sign Painter",
                speaker_type="npc",
                text="A polite sign asks citizens to admire the pipe from a safer distance.",
                scene="synthetic.scene.signage-desk",
                conversation="synthetic.conv.safe-distance",
                previous="The new warning sign is larger than the old repair plan.",
                option="Ask if admiration comes with protective glasses.",
                skill="Drama",
                voice="formal absurd politeness",
            ),
            required_sections=sections,
            expected_glossary_terms=("pipe",),
            expected_risk_flags=risk_flags,
            expected_spoiler_budget="none",
            compact_max_chars=160,
            notes="Checks compact and literary Ukrainian fields are present and bounded.",
        ),
        SyntheticEvalCase(
            case_id="synthetic.eval.m1c.spoiler_default",
            name="Spoiler safety default",
            fake_event=_event(
                case_id="spoiler_default",
                speaker="Synthetic Clerk",
                speaker_type="npc",
                text="The committee hints that tomorrow may explain the pipe, but today only shows the form.",
                scene="synthetic.scene.calendar-office",
                conversation="synthetic.conv.tomorrow-form",
                previous="The current page has no prophecy, just a wet signature.",
                option="Ask only about what is visible today.",
                skill="Logic",
                voice="strict present-tense caution",
            ),
            required_sections=sections,
            expected_glossary_terms=("committee", "pipe"),
            expected_risk_flags=risk_flags,
            expected_spoiler_budget="none",
            compact_max_chars=160,
            notes="Checks that the synthetic adapter keeps spoiler budget at none.",
        ),
    ]


def validate_eval_case(case: SyntheticEvalCase) -> None:
    if not case.case_id.startswith("synthetic.eval."):
        raise ValueError(f"Eval case id must be synthetic: {case.case_id}")
    if not case.fake_event.get("event_id", "").startswith("synthetic.event."):
        raise ValueError(f"Fake event id must be synthetic: {case.case_id}")
    _assert_synthetic_text(case.case_id, case.to_dict())


def run_synthetic_eval(cases: list[SyntheticEvalCase] | None = None) -> dict[str, Any]:
    selected_cases = cases or get_synthetic_eval_cases()
    results = [run_eval_case(case) for case in selected_cases]
    passed = all(result.passed for result in results)
    overall = round(sum(result.overall_score for result in results) / len(results), 3)
    return {
        "schema_version": "synthetic-eval.v1",
        "disclaimer": STRUCTURAL_EVAL_DISCLAIMER,
        "score_keys": list(SCORE_KEYS),
        "case_count": len(results),
        "passed": passed,
        "overall_score": overall,
        "results": [result.to_summary_dict() for result in results],
    }


def run_eval_case(case: SyntheticEvalCase) -> SyntheticEvalResult:
    validate_eval_case(case)
    context_packet = build_context_packet(case.fake_event)
    annotation_card = run_provider_pipeline(context_packet)
    overlay_demo = build_overlay_demo_model(context_packet, annotation_card)
    slice_result = {
        "fake_game_event": case.fake_event,
        "context_packet": context_packet,
        "annotation_card": annotation_card,
        "overlay_demo": overlay_demo,
    }
    assert_valid(slice_result["context_packet"], load_json(CONTEXT_PACKET_SCHEMA))
    assert_valid(slice_result["annotation_card"], load_json(ANNOTATION_CARD_SCHEMA))
    review_html = render_review_html(slice_result)
    return score_slice_result(case, slice_result, review_html)


def score_slice_result(
    case: SyntheticEvalCase,
    slice_result: dict[str, Any],
    review_html: str | None = None,
) -> SyntheticEvalResult:
    review = review_html if review_html is not None else render_review_html(slice_result)
    overlay = slice_result["overlay_demo"]
    card = slice_result["annotation_card"]
    packet = slice_result["context_packet"]

    scores = {
        "section_coverage": _section_coverage(case, overlay),
        "compact_brevity": _compact_brevity(case, overlay),
        "deep_explanation_presence": _deep_explanation_presence(overlay),
        "glossary_coverage": _glossary_coverage(case, packet, card),
        "risk_flag_coverage": _risk_flag_coverage(case, card),
        "spoiler_safety": _spoiler_safety(case, packet),
        "prompt_pack_metadata": _prompt_pack_metadata(card),
        "required_output_field_coverage": _required_output_field_coverage(card),
        "quality_priority_coverage": _quality_priority_coverage(card),
        "policy_coverage": _policy_coverage(card),
        "provider_debug_coverage": _provider_debug_coverage(card),
        "renderer_completeness": _renderer_completeness(case, slice_result, review),
    }
    failures = [f"{key}={value}" for key, value in scores.items() if value < 1.0]
    return SyntheticEvalResult(
        case_id=case.case_id,
        name=case.name,
        notes=case.notes,
        scores=scores,
        failures=failures,
        review_html=review,
        slice_result=slice_result,
    )


def _section_coverage(case: SyntheticEvalCase, overlay: dict[str, Any]) -> float:
    sections = {
        section.get("kind") for section in overlay["modes"]["deep_explanation"].get("sections", [])
    }
    return _ratio(case.required_sections, sections)


def _compact_brevity(case: SyntheticEvalCase, overlay: dict[str, Any]) -> float:
    compact = overlay["modes"]["compact"]
    meaning = compact.get("concise_meaning_uk")
    translation = compact.get("translation_uk")
    if not meaning or not translation:
        return 0.0
    return 1.0 if len(str(meaning)) <= case.compact_max_chars else 0.0


def _deep_explanation_presence(overlay: dict[str, Any]) -> float:
    deep = overlay["modes"]["deep_explanation"]
    checks = [
        bool(deep.get("original_english")),
        bool(deep.get("literary_rendering_uk")),
        bool(deep.get("explanation_uk")),
        bool(deep.get("character_voice_note_uk")),
        bool(deep.get("sections")),
    ]
    return round(sum(1 for check in checks if check) / len(checks), 3)


def _glossary_coverage(
    case: SyntheticEvalCase,
    packet: dict[str, Any],
    card: dict[str, Any],
) -> float:
    packet_terms = set(packet.get("glossary_hits", []))
    card_terms = set(card.get("glossary_terms", []))
    found = packet_terms.intersection(card_terms)
    return _ratio(case.expected_glossary_terms, found)


def _risk_flag_coverage(case: SyntheticEvalCase, card: dict[str, Any]) -> float:
    return _ratio(case.expected_risk_flags, set(card.get("risk_flags", [])))


def _spoiler_safety(case: SyntheticEvalCase, packet: dict[str, Any]) -> float:
    if packet.get("spoiler_budget") != case.expected_spoiler_budget:
        return 0.0
    return 1.0 if case.expected_spoiler_budget == "none" else 0.5


def _renderer_completeness(
    case: SyntheticEvalCase,
    slice_result: dict[str, Any],
    review_html: str,
) -> float:
    card = slice_result["annotation_card"]
    packet = slice_result["context_packet"]
    required_fragments = [
        "Compact Mode",
        "Deep Explanation Mode",
        packet["current_line"]["source_text"],
        card.get("concise_meaning_uk", ""),
        card.get("literary_rendering_uk", ""),
        "Risk flags",
        "Provider",
        "Prompt pack",
        "Player-facing language default",
    ]
    for term in case.expected_glossary_terms:
        required_fragments.append(term)
    checks = [fragment in review_html for fragment in required_fragments if fragment]
    return round(sum(1 for check in checks if check) / len(checks), 3)


def _prompt_pack_metadata(card: dict[str, Any]) -> float:
    prompt_pack = _as_dict(card.get("prompt_pack"))
    checks = [
        prompt_pack.get("pack_id") == "ukrainian_annotation_v1",
        bool(prompt_pack.get("version")),
        prompt_pack.get("player_facing_language_default") == PLAYER_FACING_LANGUAGE_DEFAULT,
        prompt_pack.get("internal_guidance_language") == "english_allowed_for_provider_guidance",
    ]
    return _checks_ratio(checks)


def _required_output_field_coverage(card: dict[str, Any]) -> float:
    prompt_pack = _as_dict(card.get("prompt_pack"))
    return _ratio(REQUESTED_OUTPUT_FIELDS, set(prompt_pack.get("required_output_fields", [])))


def _quality_priority_coverage(card: dict[str, Any]) -> float:
    prompt_pack = _as_dict(card.get("prompt_pack"))
    return _ratio(QUALITY_PRIORITIES, set(prompt_pack.get("quality_priorities", [])))


def _policy_coverage(card: dict[str, Any]) -> float:
    prompt_pack = _as_dict(card.get("prompt_pack"))
    provider_debug = _as_dict(card.get("provider_debug"))
    pack_keys = set(prompt_pack.get("policy_note_keys", []))
    debug_keys = set(provider_debug.get("policy_note_keys", []))
    return _ratio(POLICY_FOCUS_KEYS, pack_keys.intersection(debug_keys))


def _provider_debug_coverage(card: dict[str, Any]) -> float:
    provider_debug = _as_dict(card.get("provider_debug"))
    checks = [
        provider_debug.get("provider_name") == "mock",
        provider_debug.get("provider_role") == "deterministic_mock",
        provider_debug.get("prompt_pack_id") == "ukrainian_annotation_v1",
        bool(provider_debug.get("prompt_pack_version")),
        provider_debug.get("player_facing_language_default") == PLAYER_FACING_LANGUAGE_DEFAULT,
        set(POLICY_FOCUS_KEYS).issubset(set(provider_debug.get("policy_note_keys", []))),
        set(REQUESTED_OUTPUT_FIELDS).issubset(
            set(provider_debug.get("required_output_fields_seen", []))
        ),
        set(QUALITY_PRIORITIES).issubset(set(provider_debug.get("quality_priorities_seen", []))),
    ]
    return _checks_ratio(checks)


def _ratio(expected: tuple[str, ...], actual: set[str]) -> float:
    if not expected:
        return 1.0
    hits = sum(1 for item in expected if item in actual)
    return round(hits / len(expected), 3)


def _checks_ratio(checks: list[bool]) -> float:
    return round(sum(1 for check in checks if check) / len(checks), 3)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _event(
    *,
    case_id: str,
    speaker: str,
    speaker_type: str,
    text: str,
    scene: str,
    conversation: str,
    previous: str,
    option: str,
    skill: str,
    voice: str,
) -> dict[str, Any]:
    return {
        "event_id": f"synthetic.event.m1c.{case_id}",
        "synthetic_line_id": f"synthetic.m1c.{case_id}.001",
        "speaker": speaker,
        "speaker_type": speaker_type,
        "raw_english_text": text,
        "scene_id": scene,
        "conversation_id": conversation,
        "nearby_context": [
            {
                "synthetic_line_id": f"synthetic.m1c.{case_id}.000",
                "raw_english_text": previous,
                "speaker": speaker,
                "relation": "previous_visible",
            },
            {
                "synthetic_line_id": f"synthetic.m1c.{case_id}.option.001",
                "raw_english_text": option,
                "speaker": "Player",
                "relation": "player_option",
            },
        ],
        "skill_voice": {
            "skill": skill,
            "voice": voice,
            "tone": "synthetic structural eval tone",
            "audio_ref": None,
        },
        "timestamp": "2026-05-06T10:00:00Z",
    }


def _assert_synthetic_text(case_id: str, value: Any) -> None:
    text = repr(value).lower()
    if "synthetic" not in text:
        raise ValueError(f"Eval case must be clearly marked synthetic: {case_id}")
    for marker in FORBIDDEN_SYNTHETIC_MARKERS:
        if marker in text:
            raise ValueError(f"Forbidden marker {marker!r} in eval case {case_id}")
