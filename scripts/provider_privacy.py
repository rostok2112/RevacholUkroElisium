from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from scripts.provider_pipeline import ProviderRequest
    from scripts.provider_runtime_safety import (
        DEFAULT_PROVIDER_CACHE_ROOT,
        build_provider_execution_plan,
        inspect_provider_cache_root,
        redact_sensitive,
    )
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from provider_pipeline import ProviderRequest
    from provider_runtime_safety import (
        DEFAULT_PROVIDER_CACHE_ROOT,
        build_provider_execution_plan,
        inspect_provider_cache_root,
        redact_sensitive,
    )


CACHE_KEY_SCHEMA_VERSION = "provider-cache-key.v1"
PRIVACY_ENVELOPE_SCHEMA_VERSION = "provider-privacy-envelope.v1"
CACHE_KEY_PREFIX = "provider-cache-v1"

TEXT_FIELD_NAMES = (
    "original_english",
    "visible_history",
    "nearby_tree",
    "player_options",
    "prompt_pack_sections",
    "prompt_pack_focus_sections",
)


class ProviderPrivacyError(ValueError):
    """Raised when provider privacy planning cannot produce a safe summary."""


def build_provider_privacy_envelope(
    provider_request: ProviderRequest,
    config: dict[str, Any],
    execution_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = execution_plan or build_provider_execution_plan(
        config,
        provider_id=provider_request.provider_name,
    )
    cache_plan = build_cache_write_plan(provider_request, config, plan)
    cache_key = compute_provider_cache_key(provider_request)
    request_summary = _request_summary(provider_request)
    redacted_config = redact_sensitive(config)

    envelope = {
        "schema_version": PRIVACY_ENVELOPE_SCHEMA_VERSION,
        "ok": bool(plan.get("ok")) and bool(cache_plan.get("write_allowed")),
        "provider_id": provider_request.provider_name,
        "provider_mode": plan.get("provider_mode"),
        "prompt_pack_id": provider_request.prompt_pack_id,
        "prompt_pack_version": provider_request.prompt_pack_version,
        "context_packet_id": provider_request.context_packet_id,
        "line_id": provider_request.line_id,
        "synthetic": True,
        "mock": provider_request.provider_name == "mock",
        "request_field_presence": _request_field_presence(provider_request),
        "request_summary": request_summary,
        "text_metadata": _text_metadata(provider_request),
        "cache_key": cache_key,
        "cache_key_policy": {
            "schema_version": CACHE_KEY_SCHEMA_VERSION,
            "algorithm": "sha256",
            "printed_key_length": 32,
            "raw_text_included_in_printed_summary": False,
            "full_prompt_text_included_in_printed_summary": False,
            "hashed_components": [
                "provider_id",
                "request_id",
                "context_packet_id",
                "line_id",
                "prompt_pack_id",
                "prompt_pack_version",
                "requested_output_fields",
                "quality_priorities",
                "spoiler_budget",
                "glossary_hints",
                "text_field_sha256_digests",
                "text_field_lengths",
            ],
        },
        "redacted_config_summary": redacted_config,
        "cache_root": cache_plan["cache_root"],
        "cache_write_plan": cache_plan,
        "dry_run": True,
        "calls_external_services": False,
        "raw_provider_request_logged": False,
        "raw_provider_payload_persisted": False,
    }
    _assert_no_raw_request_text(provider_request, envelope)
    return envelope


def compute_provider_cache_key(provider_request: ProviderRequest) -> str:
    canonical_payload = {
        "schema_version": CACHE_KEY_SCHEMA_VERSION,
        "provider_id": provider_request.provider_name,
        "request_id": provider_request.request_id,
        "context_packet_id": provider_request.context_packet_id,
        "line_id": provider_request.line_id,
        "prompt_pack_id": provider_request.prompt_pack_id,
        "prompt_pack_version": provider_request.prompt_pack_version,
        "requested_output_fields": list(provider_request.requested_output_fields),
        "quality_priorities": list(provider_request.quality_priorities),
        "spoiler_budget": provider_request.spoiler_budget,
        "glossary_hints": list(provider_request.glossary_hints),
        "text_digests": _text_digests(provider_request),
        "text_lengths": _text_lengths(provider_request),
    }
    digest = hashlib.sha256(_canonical_json(canonical_payload).encode("utf-8")).hexdigest()
    return f"{CACHE_KEY_PREFIX}.{digest[:32]}"


def build_cache_write_plan(
    provider_request: ProviderRequest,
    config: dict[str, Any],
    execution_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = execution_plan or build_provider_execution_plan(
        config,
        provider_id=provider_request.provider_name,
    )
    llm = config.get("llm", {}) if isinstance(config, dict) else {}
    if not isinstance(llm, dict):
        raise ProviderPrivacyError("Provider privacy planning requires an [llm] table.")
    cache_status = inspect_provider_cache_root(
        llm.get("provider_cache_dir", DEFAULT_PROVIDER_CACHE_ROOT)
    )
    cache_key = compute_provider_cache_key(provider_request)
    relative_path = _planned_relative_cache_path(provider_request, cache_key)
    blocked_reasons = list(plan.get("blocked_reasons", []))
    if not cache_status["ok"]:
        blocked_reasons.extend(cache_status["errors"])
    write_allowed = bool(plan.get("ok")) and bool(cache_status["ok"])
    return {
        "schema_version": "provider-cache-write-plan.v1",
        "ok": write_allowed,
        "provider_id": provider_request.provider_name,
        "prompt_pack_id": provider_request.prompt_pack_id,
        "prompt_pack_version": provider_request.prompt_pack_version,
        "cache_root": cache_status["display_path"],
        "cache_root_is_private": cache_status["is_private"],
        "cache_root_is_repo_ignored": cache_status["is_repo_ignored"],
        "cache_key": cache_key,
        "planned_relative_path": relative_path,
        "write_allowed": write_allowed,
        "would_write": False,
        "dry_run": True,
        "writes_raw_payload": False,
        "blocked_reasons": blocked_reasons,
        "warnings": list(cache_status["warnings"]),
    }


def envelope_contains_raw_text(envelope: dict[str, Any], raw_text: str) -> bool:
    if not raw_text:
        return False
    return raw_text in _canonical_json(envelope)


def envelope_contains_prompt_text(
    envelope: dict[str, Any], provider_request: ProviderRequest
) -> bool:
    rendered = _canonical_json(envelope)
    for section in provider_request.prompt_pack_sections.values():
        if isinstance(section, str) and len(section) > 80 and section in rendered:
            return True
    for section in provider_request.prompt_pack_focus_sections.values():
        if isinstance(section, str) and len(section) > 80 and section in rendered:
            return True
    return False


def _request_field_presence(provider_request: ProviderRequest) -> dict[str, bool]:
    request_dict = provider_request.to_dict()
    return {key: value is not None and value != "" for key, value in sorted(request_dict.items())}


def _request_summary(provider_request: ProviderRequest) -> dict[str, Any]:
    return {
        "request_id": provider_request.request_id,
        "speaker_present": bool(provider_request.speaker),
        "speaker_type_present": bool(provider_request.speaker_type),
        "scene_id_present": bool(provider_request.scene_id),
        "conversation_id_present": bool(provider_request.conversation_id),
        "skill_present": bool(provider_request.skill),
        "visible_history_count": len(provider_request.visible_history),
        "nearby_tree_count": len(provider_request.nearby_tree),
        "player_options_count": len(provider_request.player_options),
        "glossary_hint_count": len(provider_request.glossary_hints),
        "requested_output_field_count": len(provider_request.requested_output_fields),
        "quality_priority_count": len(provider_request.quality_priorities),
        "prompt_pack_policy_ref_count": len(provider_request.prompt_pack_policy_refs),
        "prompt_pack_section_count": len(provider_request.prompt_pack_sections),
        "prompt_pack_focus_policy_ref_count": len(provider_request.prompt_pack_focus_policy_refs),
        "prompt_pack_focus_section_count": len(provider_request.prompt_pack_focus_sections),
    }


def _text_metadata(provider_request: ProviderRequest) -> dict[str, Any]:
    lengths = _text_lengths(provider_request)
    return {
        "original_english_length": lengths["original_english"],
        "visible_history_count": len(provider_request.visible_history),
        "nearby_tree_count": len(provider_request.nearby_tree),
        "player_options_count": len(provider_request.player_options),
        "prompt_pack_section_count": len(provider_request.prompt_pack_sections),
        "prompt_pack_focus_section_count": len(provider_request.prompt_pack_focus_sections),
        "text_field_digests": _text_digests(provider_request),
    }


def _text_lengths(provider_request: ProviderRequest) -> dict[str, Any]:
    return {
        "original_english": len(provider_request.original_english),
        "visible_history": _collection_text_length(provider_request.visible_history),
        "nearby_tree": _collection_text_length(provider_request.nearby_tree),
        "player_options": _collection_text_length(provider_request.player_options),
        "prompt_pack_sections": _mapping_text_length(provider_request.prompt_pack_sections),
        "prompt_pack_focus_sections": _mapping_text_length(
            provider_request.prompt_pack_focus_sections
        ),
    }


def _text_digests(provider_request: ProviderRequest) -> dict[str, str]:
    values = {
        "original_english": provider_request.original_english,
        "visible_history": provider_request.visible_history,
        "nearby_tree": provider_request.nearby_tree,
        "player_options": provider_request.player_options,
        "prompt_pack_sections": provider_request.prompt_pack_sections,
        "prompt_pack_focus_sections": provider_request.prompt_pack_focus_sections,
    }
    return {
        key: hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
        for key, value in values.items()
    }


def _collection_text_length(items: tuple[dict[str, Any], ...]) -> int:
    return sum(len(_canonical_json(item)) for item in items)


def _mapping_text_length(mapping: dict[str, str]) -> int:
    return sum(len(value) for value in mapping.values() if isinstance(value, str))


def _planned_relative_cache_path(provider_request: ProviderRequest, cache_key: str) -> str:
    provider = _safe_path_part(provider_request.provider_name)
    pack = _safe_path_part(provider_request.prompt_pack_id)
    return str(Path("workspace/provider-cache") / provider / pack / f"{cache_key}.json").replace(
        "\\", "/"
    )


def _safe_path_part(value: str) -> str:
    safe = "".join(
        character if character.isalnum() or character in "-_." else "_" for character in value
    )
    return safe or "unknown"


def _assert_no_raw_request_text(
    provider_request: ProviderRequest,
    envelope: dict[str, Any],
) -> None:
    if envelope_contains_raw_text(envelope, provider_request.original_english):
        raise ProviderPrivacyError("Privacy envelope contains raw original English text.")
    if envelope_contains_prompt_text(envelope, provider_request):
        raise ProviderPrivacyError("Privacy envelope contains full prompt pack text.")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
