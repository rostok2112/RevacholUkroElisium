from __future__ import annotations

from pathlib import Path
import re
from typing import Any

try:
    from scripts.prompt_pack import PromptPack, load_prompt_pack
    from scripts.provider_registry import (
        DEFAULT_PROVIDER_ID,
        ProviderRegistryError,
        get_provider_definition,
    )
    from scripts.validate_config import APPROVED_PRIVATE_ROOTS, ROOT
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from prompt_pack import PromptPack, load_prompt_pack
    from provider_registry import (
        DEFAULT_PROVIDER_ID,
        ProviderRegistryError,
        get_provider_definition,
    )
    from validate_config import APPROVED_PRIVATE_ROOTS, ROOT


DEFAULT_PROVIDER_CACHE_ROOT = "workspace/provider-cache"
REDACTED_VALUE = "[REDACTED]"
REDACTED_PATH = "[REDACTED_PATH]"

SECRET_KEY_MARKERS = (
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "secret",
    "token",
    "password",
    "credential",
    "bearer",
)


class ProviderRuntimeSafetyError(ValueError):
    """Raised when provider runtime preflight cannot produce a safe plan."""


def build_provider_execution_plan(
    config: dict[str, Any],
    provider_id: str | None = "mock",
    prompt_pack: PromptPack | None = None,
) -> dict[str, Any]:
    if not isinstance(config, dict):
        raise ProviderRuntimeSafetyError("Provider preflight config must be an object.")

    llm = config.get("llm", {})
    if not isinstance(llm, dict):
        raise ProviderRuntimeSafetyError("Provider preflight requires an [llm] table.")

    selected_provider_id = _selected_provider_id(llm, provider_id)
    try:
        definition = get_provider_definition(selected_provider_id)
    except ProviderRegistryError as exc:
        raise ProviderRuntimeSafetyError(str(exc)) from exc

    providers = llm.get("providers", {})
    if providers is None:
        providers = {}
    if not isinstance(providers, dict):
        raise ProviderRuntimeSafetyError("Provider preflight requires llm.providers to be a table.")

    provider_config = providers.get(selected_provider_id, {})
    blocked_reasons: list[str] = []
    warnings: list[str] = []
    if provider_config is None:
        provider_config = {}
    if not isinstance(provider_config, dict):
        provider_config = {}
        blocked_reasons.append("provider_config_not_a_table")

    provider_enabled = _provider_enabled(definition.enabled_by_default, provider_config)
    if provider_enabled is None:
        provider_enabled = False
        blocked_reasons.append("provider_enabled_not_boolean")
    elif not provider_enabled:
        blocked_reasons.append("provider_disabled")

    external_provider_allowed = bool(llm.get("allow_external_providers", False))
    if definition.external and not external_provider_allowed:
        blocked_reasons.append("external_provider_not_allowed")

    if not definition.implemented:
        blocked_reasons.append("provider_unimplemented")

    cache_status = inspect_provider_cache_root(
        llm.get("provider_cache_dir", DEFAULT_PROVIDER_CACHE_ROOT)
    )
    warnings.extend(cache_status["warnings"])
    if not cache_status["ok"]:
        blocked_reasons.extend(cache_status["errors"])

    selected_pack = prompt_pack
    if selected_pack is None:
        try:
            selected_pack = load_prompt_pack()
        except Exception as exc:  # pragma: no cover - defensive, prompt pack has tests.
            warnings.append(f"prompt_pack_unavailable: {exc}")

    ok = not blocked_reasons
    return {
        "schema_version": "provider-execution-plan.v1",
        "ok": ok,
        "active_provider": selected_provider_id,
        "provider_implemented": definition.implemented,
        "provider_enabled": provider_enabled,
        "provider_mode": _provider_mode(selected_provider_id, ok),
        "provider_role": definition.role,
        "provider_offline": definition.offline,
        "provider_deterministic": definition.deterministic,
        "network_allowed": False,
        "secrets_required": definition.requires_secret,
        "external_provider_allowed": external_provider_allowed,
        "local_runtime_required": definition.requires_local_runtime,
        "cache_root": cache_status["display_path"],
        "cache_root_is_private": cache_status["is_private"],
        "cache_root_is_repo_ignored": cache_status["is_repo_ignored"],
        "prompt_pack_id": selected_pack.metadata.pack_id if selected_pack else None,
        "prompt_pack_version": selected_pack.metadata.version if selected_pack else None,
        "dry_run": True,
        "calls_external_services": False,
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "redaction_applied": True,
        "redacted_runtime_config": {
            "active_provider": selected_provider_id,
            "allow_external_providers": external_provider_allowed,
            "provider_cache_dir": redact_sensitive(
                llm.get("provider_cache_dir", DEFAULT_PROVIDER_CACHE_ROOT),
                key_path="llm.provider_cache_dir",
            ),
            "selected_provider_config": redact_sensitive(provider_config),
        },
    }


def inspect_provider_cache_root(value: Any) -> dict[str, Any]:
    if not isinstance(value, str) or not value.strip():
        return _cache_status(
            display_path=REDACTED_PATH,
            ok=False,
            is_private=False,
            is_repo_ignored=False,
            errors=["provider_cache_root_must_be_non_empty_string"],
            warnings=[],
        )

    resolved = _resolve_repo_relative(value)
    inside_repo = _is_relative_to(resolved, ROOT.resolve(strict=False))
    approved_root = _approved_private_root(resolved)
    display_path = _display_cache_path(value, resolved)

    if inside_repo and approved_root is None:
        return _cache_status(
            display_path=display_path,
            ok=False,
            is_private=False,
            is_repo_ignored=False,
            errors=["provider_cache_root_not_ignored_private_root"],
            warnings=[],
        )

    warnings: list[str] = []
    if not inside_repo:
        warnings.append("provider_cache_root_outside_repo_assumed_private")

    return _cache_status(
        display_path=display_path,
        ok=True,
        is_private=True,
        is_repo_ignored=inside_repo,
        errors=[],
        warnings=warnings,
    )


def validate_provider_cache_root(value: Any) -> dict[str, Any]:
    status = inspect_provider_cache_root(value)
    if not status["ok"]:
        raise ProviderRuntimeSafetyError("; ".join(status["errors"]))
    return status


def redact_sensitive(value: Any, *, key_path: str = "") -> Any:
    if _looks_sensitive_key(key_path):
        return REDACTED_VALUE
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, child in sorted(value.items(), key=lambda item: str(item[0])):
            child_path = f"{key_path}.{key}" if key_path else str(key)
            redacted[str(key)] = redact_sensitive(child, key_path=child_path)
        return redacted
    if isinstance(value, list):
        return [
            redact_sensitive(child, key_path=f"{key_path}[{index}]")
            for index, child in enumerate(value)
        ]
    if isinstance(value, str):
        if _looks_secret_value(value):
            return REDACTED_VALUE
        if _looks_private_absolute_path(value):
            return REDACTED_PATH
    return value


def _selected_provider_id(llm: dict[str, Any], provider_id: str | None) -> str:
    selected = provider_id
    if selected is None:
        selected = llm.get("active_provider", DEFAULT_PROVIDER_ID)
    if not isinstance(selected, str) or not selected.strip():
        raise ProviderRuntimeSafetyError("Provider id must be a non-empty string.")
    return selected


def _provider_enabled(default_enabled: bool, provider_config: dict[str, Any]) -> bool | None:
    enabled = provider_config.get("enabled", default_enabled)
    return enabled if isinstance(enabled, bool) else None


def _provider_mode(provider_id: str, ok: bool) -> str:
    if provider_id == "mock" and ok:
        return "mock_offline_deterministic"
    return "blocked_dry_run"


def _cache_status(
    *,
    display_path: str,
    ok: bool,
    is_private: bool,
    is_repo_ignored: bool,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "ok": ok,
        "display_path": display_path,
        "is_private": is_private,
        "is_repo_ignored": is_repo_ignored,
        "errors": errors,
        "warnings": warnings,
    }


def _display_cache_path(raw_value: str, resolved: Path) -> str:
    raw_path = Path(raw_value)
    if raw_path.is_absolute():
        return REDACTED_PATH
    try:
        relative = resolved.relative_to(ROOT.resolve(strict=False))
    except ValueError:
        return REDACTED_PATH
    return str(relative).replace("\\", "/")


def _approved_private_root(resolved: Path) -> Path | None:
    for root in APPROVED_PRIVATE_ROOTS:
        candidate = _resolve_repo_relative(root)
        if _is_relative_to(resolved, candidate):
            return candidate
    return None


def _resolve_repo_relative(path: str | Path) -> Path:
    raw = Path(path).expanduser()
    if raw.is_absolute():
        return raw.resolve(strict=False)
    return (ROOT / raw).resolve(strict=False)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _looks_sensitive_key(key_path: str) -> bool:
    lowered = key_path.lower()
    if any(marker in lowered for marker in SECRET_KEY_MARKERS):
        return True
    return lowered.endswith(".key") or lowered == "key"


def _looks_secret_value(value: str) -> bool:
    lowered = value.lower()
    if lowered.startswith(("sk-", "sk_", "pk-", "rk-", "bearer ", "token ")):
        return True
    if "api_key=" in lowered or "access_token=" in lowered or "secret=" in lowered:
        return True
    return False


def _looks_private_absolute_path(value: str) -> bool:
    if re.match(r"^[a-zA-Z]:[\\/]", value):
        return True
    if value.startswith("/") and not value.startswith("//"):
        return True
    lowered = value.lower().replace("\\", "/")
    return "/users/" in lowered or "/documents/" in lowered or "/appdata/" in lowered
