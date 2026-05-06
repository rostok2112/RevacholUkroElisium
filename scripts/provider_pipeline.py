from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

try:
    from scripts.schema_validator import SchemaValidationError, assert_valid, load_json
    from scripts.synthetic_slice import (
        ANNOTATION_CARD_SCHEMA,
        CONTEXT_PACKET_SCHEMA,
        MOCK_CHARACTER_VOICE_UK,
        MOCK_CONCISE_MEANING_UK,
        MOCK_EXPLANATION_UK,
        MOCK_LITERARY_RENDERING_UK,
    )
except ModuleNotFoundError:  # pragma: no cover - used when run as a script dependency.
    from schema_validator import SchemaValidationError, assert_valid, load_json
    from synthetic_slice import (
        ANNOTATION_CARD_SCHEMA,
        CONTEXT_PACKET_SCHEMA,
        MOCK_CHARACTER_VOICE_UK,
        MOCK_CONCISE_MEANING_UK,
        MOCK_EXPLANATION_UK,
        MOCK_LITERARY_RENDERING_UK,
    )


REQUESTED_OUTPUT_FIELDS = (
    "original_english",
    "concise_meaning_uk",
    "literary_rendering_uk",
    "translation_uk",
    "literal_gloss",
    "quick_note",
    "explanation_uk",
    "deep_notes",
    "character_voice_note_uk",
    "ukrainian_cultural_equivalents",
    "glossary_terms",
    "confidence",
    "risk_flags",
    "quality",
)

QUALITY_PRIORITIES = (
    "preserve_original_english",
    "produce_ukrainian_concise_meaning",
    "produce_literary_ukrainian_rendering",
    "explain_idioms_references_subtext",
    "preserve_character_voice",
    "include_uncertainty_and_risk_flags",
    "avoid_hallucination",
    "do_not_silently_overlocalize_ukrainian_cultural_adaptations",
)

SAFETY_RULES = (
    "do_not_invent_lore",
    "do_not_exceed_spoiler_budget",
    "do_not_call_external_services",
    "use_synthetic_fixture_data_only_in_tests",
)


class ProviderPipelineError(ValueError):
    """Raised when provider request, response, or normalization fails."""


@dataclass(frozen=True)
class ProviderMetadata:
    provider_name: str
    provider_kind: str
    version: str
    offline: bool
    deterministic: bool
    requires_api_key: bool
    future_roles: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["future_roles"] = list(self.future_roles)
        return data


@dataclass(frozen=True)
class ProviderRequest:
    request_id: str
    provider_name: str
    context_packet_id: str
    line_id: str
    original_english: str
    speaker: str | None
    speaker_type: str | None
    scene_id: str | None
    conversation_id: str | None
    skill: str | None
    visible_history: tuple[dict[str, Any], ...]
    nearby_tree: tuple[dict[str, Any], ...]
    player_options: tuple[dict[str, Any], ...]
    spoiler_budget: str
    glossary_hints: tuple[str, ...]
    requested_output_fields: tuple[str, ...]
    quality_priorities: tuple[str, ...]
    safety_rules: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in (
            "visible_history",
            "nearby_tree",
            "player_options",
            "glossary_hints",
            "requested_output_fields",
            "quality_priorities",
            "safety_rules",
        ):
            data[key] = list(data[key])
        return data


@dataclass(frozen=True)
class ProviderResponse:
    metadata: ProviderMetadata
    request_id: str
    line_id: str
    output: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "request_id": self.request_id,
            "line_id": self.line_id,
            "output": self.output,
        }


MOCK_PROVIDER_METADATA = ProviderMetadata(
    provider_name="mock",
    provider_kind="deterministic_mock",
    version="provider-pipeline.mock.v1",
    offline=True,
    deterministic=True,
    requires_api_key=False,
    future_roles=(
        "openai_compatible_api",
        "deepl_glossary_helper",
        "local_model",
        "ensemble_reviewer",
    ),
)


def build_provider_request(
    context_packet: dict[str, Any],
    provider_name: str = "mock",
) -> ProviderRequest:
    assert_valid(context_packet, load_json(CONTEXT_PACKET_SCHEMA))
    current_line = context_packet["current_line"]
    return ProviderRequest(
        request_id=f"provider-request.{context_packet['packet_id']}",
        provider_name=provider_name,
        context_packet_id=context_packet["packet_id"],
        line_id=current_line["line_id"],
        original_english=current_line["source_text"],
        speaker=current_line.get("speaker"),
        speaker_type=current_line.get("speaker_type"),
        scene_id=current_line.get("location"),
        conversation_id=current_line.get("conversation_id"),
        skill=current_line.get("skill"),
        visible_history=_line_refs(context_packet.get("visible_history", [])),
        nearby_tree=_line_refs(context_packet.get("nearby_tree", [])),
        player_options=_line_refs(context_packet.get("player_options", [])),
        spoiler_budget=context_packet["spoiler_budget"],
        glossary_hints=tuple(context_packet.get("glossary_hits", [])),
        requested_output_fields=REQUESTED_OUTPUT_FIELDS,
        quality_priorities=QUALITY_PRIORITIES,
        safety_rules=SAFETY_RULES,
    )


class MockAnnotationProvider:
    metadata = MOCK_PROVIDER_METADATA

    def annotate(self, request: ProviderRequest) -> ProviderResponse:
        if request.provider_name != "mock":
            raise ProviderPipelineError("Only the deterministic mock provider is implemented.")

        output = {
            "line_id": request.line_id,
            "original_english": request.original_english,
            "translation_uk": MOCK_LITERARY_RENDERING_UK,
            "concise_meaning_uk": MOCK_CONCISE_MEANING_UK,
            "literary_rendering_uk": MOCK_LITERARY_RENDERING_UK,
            "literal_gloss": (
                "The synthetic line frames cosmetic recognition as a substitute for repair."
            ),
            "quick_note": MOCK_EXPLANATION_UK,
            "explanation_uk": MOCK_EXPLANATION_UK,
            "character_voice_note_uk": MOCK_CHARACTER_VOICE_UK,
            "deep_notes": [
                {
                    "kind": "idiom",
                    "text": "The image treats praise for a broken object as a deadpan joke.",
                },
                {
                    "kind": "reference",
                    "text": "Synthetic bureaucracy reference only; no game dialogue is sourced.",
                },
                {
                    "kind": "skill_voice",
                    "text": MOCK_CHARACTER_VOICE_UK,
                },
                {
                    "kind": "translation_choice",
                    "text": "The mock keeps the civic absurdity and avoids silent localization.",
                },
            ],
            "ukrainian_cultural_equivalents": [],
            "glossary_terms": list(request.glossary_hints),
            "confidence": 0.77,
            "risk_flags": [
                "synthetic_fixture",
                "deterministic_mock_provider",
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
        return ProviderResponse(
            metadata=self.metadata,
            request_id=request.request_id,
            line_id=request.line_id,
            output=output,
        )


def normalize_provider_response(
    context_packet: dict[str, Any],
    provider_response: ProviderResponse,
) -> dict[str, Any]:
    assert_valid(context_packet, load_json(CONTEXT_PACKET_SCHEMA))
    current_line = context_packet["current_line"]

    if provider_response.line_id != current_line["line_id"]:
        raise ProviderPipelineError("Provider response line_id does not match context packet.")

    output = provider_response.output
    if not isinstance(output, dict):
        raise ProviderPipelineError("Provider output must be an object.")

    output_line_id = output.get("line_id")
    if output_line_id is not None and output_line_id != current_line["line_id"]:
        raise ProviderPipelineError("Provider output line_id does not match context packet.")

    card = {
        "line_id": current_line["line_id"],
        "source_text": current_line["source_text"],
        "original_english": current_line["source_text"],
        "translation_uk": _required_string(output, "translation_uk"),
        "concise_meaning_uk": _required_string(output, "concise_meaning_uk"),
        "literary_rendering_uk": _required_string(output, "literary_rendering_uk"),
        "literal_gloss": _required_string(output, "literal_gloss"),
        "quick_note": _required_string(output, "quick_note"),
        "explanation_uk": _required_string(output, "explanation_uk"),
        "character_voice_note_uk": _required_string(output, "character_voice_note_uk"),
        "deep_notes": _required_list(output, "deep_notes"),
        "ukrainian_cultural_equivalents": _optional_list(output, "ukrainian_cultural_equivalents"),
        "glossary_terms": _optional_list(output, "glossary_terms")
        or list(context_packet.get("glossary_hits", [])),
        "confidence": _required_number(output, "confidence"),
        "risk_flags": _required_list(output, "risk_flags"),
        "quality": _required_object(output, "quality"),
        "provider": provider_response.metadata.to_dict(),
    }

    try:
        assert_valid(card, load_json(ANNOTATION_CARD_SCHEMA))
    except SchemaValidationError as exc:
        raise ProviderPipelineError(f"Normalized annotation card is invalid: {exc}") from exc
    return card


def run_provider_pipeline(
    context_packet: dict[str, Any],
    provider_name: str = "mock",
) -> dict[str, Any]:
    if provider_name != "mock":
        raise ProviderPipelineError("Only provider 'mock' is implemented in Milestone 2A.")
    request = build_provider_request(context_packet, provider_name)
    response = MockAnnotationProvider().annotate(request)
    return normalize_provider_response(context_packet, response)


def _line_refs(lines: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(lines, list):
        return ()
    return tuple(dict(line) for line in lines if isinstance(line, dict))


def _required_string(output: dict[str, Any], key: str) -> str:
    value = output.get(key)
    if not isinstance(value, str) or not value:
        raise ProviderPipelineError(f"Provider output missing required string: {key}")
    return value


def _required_number(output: dict[str, Any], key: str) -> int | float:
    value = output.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ProviderPipelineError(f"Provider output missing required number: {key}")
    return value


def _required_list(output: dict[str, Any], key: str) -> list[Any]:
    value = output.get(key)
    if not isinstance(value, list):
        raise ProviderPipelineError(f"Provider output missing required list: {key}")
    return value


def _optional_list(output: dict[str, Any], key: str) -> list[Any]:
    value = output.get(key, [])
    if not isinstance(value, list):
        raise ProviderPipelineError(f"Provider output field must be a list: {key}")
    return value


def _required_object(output: dict[str, Any], key: str) -> dict[str, Any]:
    value = output.get(key)
    if not isinstance(value, dict):
        raise ProviderPipelineError(f"Provider output missing required object: {key}")
    return value
