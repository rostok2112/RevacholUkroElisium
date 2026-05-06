from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tomllib
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

APPROVED_PRIVATE_ROOTS = [
    Path(".local-game"),
    Path("data/local"),
    Path("data/extracted"),
    Path("data/generated"),
    Path("extracted"),
    Path("game-data"),
    Path("private-data"),
    Path("workspace"),
    Path(".cache"),
    Path("vector-store"),
    Path("translation-memory/private"),
    Path("audio-index/private"),
    Path("screenshots/private"),
    Path("llm-cache"),
]

QUALITY_MODES = {"deterministic_test", "cheap_baseline", "interactive", "maximum_quality"}
OVERLAY_MODES = {
    "minimal_hint",
    "full_translation",
    "deep_explanation",
    "joke_idiom_reference",
    "voice_audio_note",
    "debug",
}


def load_config(path: Path | str) -> dict[str, Any]:
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)


def validate_config_file(path: Path | str, *, example: bool = False) -> list[str]:
    config_path = Path(path)
    config = load_config(config_path)
    return validate_config(config, example=example)


def validate_config(config: dict[str, Any], *, example: bool = False) -> list[str]:
    errors: list[str] = []
    paths = _as_table(config.get("paths"), "paths", errors)
    translation = _as_table(config.get("translation"), "translation", errors)
    overlay = _as_table(config.get("overlay"), "overlay", errors)
    llm = _as_table(config.get("llm"), "llm", errors)
    network = _as_table(config.get("network_enrichment"), "network_enrichment", errors)

    _validate_paths(paths, example=example, errors=errors)
    _validate_modes(translation, overlay, errors)
    _validate_runtime_policy(llm, network, errors)
    _validate_no_inline_secrets(config, errors)
    return errors


def _validate_paths(paths: dict[str, Any], *, example: bool, errors: list[str]) -> None:
    if not paths:
        return

    game_path = paths.get("game_install_path", "")
    if not isinstance(game_path, str):
        errors.append("paths.game_install_path must be a string")
    elif not game_path.strip():
        if not example:
            errors.append("paths.game_install_path is required outside --example validation")
    else:
        resolved_game = _resolve_repo_relative(game_path)
        if _is_inside_repo(resolved_game):
            errors.append("paths.game_install_path must not point inside the public repository")

    for key, value in paths.items():
        if key == "game_install_path" or not key.endswith("_path"):
            continue
        _validate_private_path(f"paths.{key}", value, errors)


def _validate_modes(
    translation: dict[str, Any],
    overlay: dict[str, Any],
    errors: list[str],
) -> None:
    quality_mode = translation.get("quality_mode")
    if quality_mode not in QUALITY_MODES:
        errors.append(
            f"translation.quality_mode must be one of {sorted(QUALITY_MODES)}, "
            f"got {quality_mode!r}"
        )

    overlay_mode = overlay.get("default_mode")
    if overlay_mode not in OVERLAY_MODES:
        errors.append(
            f"overlay.default_mode must be one of {sorted(OVERLAY_MODES)}, "
            f"got {overlay_mode!r}"
        )


def _validate_runtime_policy(
    llm: dict[str, Any],
    network: dict[str, Any],
    errors: list[str],
) -> None:
    providers = llm.get("providers", {})
    if providers and not isinstance(providers, dict):
        errors.append("llm.providers must be a table")
        return

    for provider_name, provider in providers.items():
        if not isinstance(provider, dict):
            errors.append(f"llm.providers.{provider_name} must be a table")
            continue
        if provider.get("enabled") and provider_name != "mock":
            has_env_pointer = any(key.endswith("_env") and provider.get(key) for key in provider)
            if not has_env_pointer:
                errors.append(f"llm.providers.{provider_name} is enabled but has no *_env setting")

    if network.get("enabled") and not network.get("lawful_opt_in_required"):
        errors.append("network_enrichment.enabled requires lawful_opt_in_required = true")
    if "cache_path" in network:
        _validate_private_path("network_enrichment.cache_path", network["cache_path"], errors)


def _validate_private_path(label: str, value: Any, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")
        return

    resolved = _resolve_repo_relative(value)
    if not _is_inside_repo(resolved):
        return

    if not any(_is_relative_to(resolved, _resolve_repo_relative(root)) for root in APPROVED_PRIVATE_ROOTS):
        errors.append(f"{label} points inside the repo but not under an approved ignored private root")


def _validate_no_inline_secrets(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            lower_key = str(key).lower()
            looks_secret_key = any(
                marker in lower_key for marker in ("api_key", "secret", "token", "password")
            )
            if looks_secret_key and not lower_key.endswith("_env"):
                errors.append(f"{child_path} looks like an inline secret; use an *_env setting instead")
            _validate_no_inline_secrets(child, errors, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_inline_secrets(child, errors, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if value.startswith(("sk-", "sk_", "pk-")) or "api_key=" in lowered:
            errors.append(f"{path} looks like a secret value; use an environment variable name instead")


def _as_table(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if value is None:
        errors.append(f"Missing [{label}] table")
        return {}
    if not isinstance(value, dict):
        errors.append(f"[{label}] must be a table")
        return {}
    return value


def _resolve_repo_relative(path: str | Path) -> Path:
    raw = Path(path).expanduser()
    if raw.is_absolute():
        return raw.resolve(strict=False)
    return (ROOT / raw).resolve(strict=False)


def _is_inside_repo(path: Path) -> bool:
    return _is_relative_to(path, ROOT)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Revachol companion config safety.")
    parser.add_argument("config", type=Path, help="Path to a TOML config file")
    parser.add_argument("--example", action="store_true", help="Allow placeholder example values")
    args = parser.parse_args()

    errors = validate_config_file(args.config, example=args.example)
    if errors:
        print("\n".join(errors))
        return 1

    print(f"Config validation passed: {args.config}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
