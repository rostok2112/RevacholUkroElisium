from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


DEFAULT_PROVIDER_ID = "mock"


class ProviderRegistryError(ValueError):
    """Raised when provider selection is unsafe or unsupported."""


@dataclass(frozen=True)
class ProviderDefinition:
    provider_id: str
    role: str
    display_name: str
    implemented: bool
    enabled_by_default: bool
    offline: bool
    deterministic: bool
    external: bool
    requires_secret: bool
    requires_local_runtime: bool
    roadmap_note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PROVIDER_DEFINITIONS: tuple[ProviderDefinition, ...] = (
    ProviderDefinition(
        provider_id="mock",
        role="annotation_provider",
        display_name="Deterministic mock annotation provider",
        implemented=True,
        enabled_by_default=True,
        offline=True,
        deterministic=True,
        external=False,
        requires_secret=False,
        requires_local_runtime=False,
        roadmap_note="Implemented for offline tests and synthetic local development.",
    ),
    ProviderDefinition(
        provider_id="openai_compatible",
        role="future_openai_compatible_annotation_provider",
        display_name="Future OpenAI-compatible annotation provider",
        implemented=False,
        enabled_by_default=False,
        offline=False,
        deterministic=False,
        external=True,
        requires_secret=True,
        requires_local_runtime=False,
        roadmap_note="Roadmap only; disabled until explicit runtime integration exists.",
    ),
    ProviderDefinition(
        provider_id="deepl_glossary",
        role="future_deepl_glossary_helper",
        display_name="Future DeepL/glossary helper",
        implemented=False,
        enabled_by_default=False,
        offline=False,
        deterministic=False,
        external=True,
        requires_secret=True,
        requires_local_runtime=False,
        roadmap_note="Roadmap only; disabled until explicit runtime integration exists.",
    ),
    ProviderDefinition(
        provider_id="local_model",
        role="future_local_model_provider",
        display_name="Future local model provider",
        implemented=False,
        enabled_by_default=False,
        offline=True,
        deterministic=False,
        external=False,
        requires_secret=False,
        requires_local_runtime=True,
        roadmap_note="Roadmap only; disabled until local runtime integration exists.",
    ),
    ProviderDefinition(
        provider_id="ensemble_reviewer",
        role="future_ensemble_reviewer",
        display_name="Future ensemble reviewer",
        implemented=False,
        enabled_by_default=False,
        offline=False,
        deterministic=False,
        external=True,
        requires_secret=True,
        requires_local_runtime=False,
        roadmap_note="Roadmap only; disabled until explicit runtime integration exists.",
    ),
)

_PROVIDERS_BY_ID = {definition.provider_id: definition for definition in PROVIDER_DEFINITIONS}


def list_provider_definitions() -> tuple[ProviderDefinition, ...]:
    return PROVIDER_DEFINITIONS


def provider_ids() -> tuple[str, ...]:
    return tuple(definition.provider_id for definition in PROVIDER_DEFINITIONS)


def get_provider_definition(provider_id: str) -> ProviderDefinition:
    try:
        return _PROVIDERS_BY_ID[provider_id]
    except KeyError as exc:
        known = ", ".join(sorted(_PROVIDERS_BY_ID))
        raise ProviderRegistryError(
            f"Unknown provider {provider_id!r}. Known providers: {known}."
        ) from exc


def resolve_provider_selection(
    provider_id: str | None = None,
    *,
    enabled_overrides: Mapping[str, bool] | None = None,
    allow_external_providers: bool = False,
) -> ProviderDefinition:
    selected_id = DEFAULT_PROVIDER_ID if provider_id is None else provider_id
    if not selected_id.strip():
        raise ProviderRegistryError("Provider id must be a non-empty string.")
    definition = get_provider_definition(selected_id)
    enabled = (
        enabled_overrides[definition.provider_id]
        if enabled_overrides and definition.provider_id in enabled_overrides
        else definition.enabled_by_default
    )

    if not enabled:
        raise ProviderRegistryError(
            f"Provider {definition.provider_id!r} is disabled. "
            "Enable it explicitly before selecting it."
        )
    if definition.external and not allow_external_providers:
        raise ProviderRegistryError(
            f"Provider {definition.provider_id!r} is external and requires "
            "allow_external_providers = true."
        )
    if not definition.implemented:
        raise ProviderRegistryError(
            f"Provider {definition.provider_id!r} is not implemented in this milestone."
        )
    return definition


def provider_summary() -> dict[str, Any]:
    return {
        "schema_version": "provider-registry.v1",
        "default_provider": DEFAULT_PROVIDER_ID,
        "runtime_default_mock_only": True,
        "providers": [definition.to_dict() for definition in PROVIDER_DEFINITIONS],
    }
