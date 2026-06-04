from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import load_json
    from synthetic_slice import ROOT


URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
PRIVATE_PATH_PATTERN = re.compile(
    r"(\b[A-Za-z]:[\\/](?:Users|Program Files|Games|Steam|GOG|AppData)[\\/]|/(?:home|Users|mnt|Volumes|Applications)/)",
    re.IGNORECASE,
)
FORBIDDEN_VALUE_MARKERS = (
    "raw payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "steamapps",
    "savegame",
    ".sav",
    "decompiled",
    "private path",
    "real game text",
)


def load_fixture(path: Path) -> dict[str, Any] | list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load {display_path(path)}: {exc}"]
    if not isinstance(payload, dict):
        return [f"{display_path(path)} must be a JSON object."]
    return payload


def strict_status_errors(payload: dict[str, Any], *, label: str) -> list[str]:
    errors: list[str] = []
    for field in (
        "automated_complete",
        "manual_verification_required",
        "manual_verification_complete",
        "fully_complete",
    ):
        if not isinstance(payload.get(field), bool):
            errors.append(f"{label} must set {field} to a boolean.")
    if (
        payload.get("manual_verification_required") is True
        and payload.get("manual_verification_complete") is False
        and payload.get("fully_complete") is True
    ):
        errors.append(
            f"{label} cannot set fully_complete=true without completed manual verification."
        )
    return errors


def forbidden_boolean_errors(
    payload: dict[str, Any], fields: tuple[str, ...], *, label: str
) -> list[str]:
    return [
        f"{label} must keep {field}=false." for field in fields if payload.get(field) is not False
    ]


def unsafe_value_errors(payload: Any, *, label: str, allowed_values: set[str]) -> list[str]:
    errors: list[str] = []
    for value in iter_string_values(payload):
        if value in allowed_values:
            continue
        for url in URL_PATTERN.findall(value):
            errors.append(f"{label} contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(value):
            errors.append(f"{label} contains a secret/API-key-looking value.")
        if PRIVATE_PATH_PATTERN.search(value):
            errors.append(f"{label} contains a private absolute path.")
        lowered = value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{label} contains forbidden marker {marker!r}.")
    return errors


def doc_reference_errors(paths: tuple[Path, ...], refs: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        if not path.exists():
            errors.append(f"Missing doc target: {display_path(path)}.")
            continue
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for ref in refs:
            if ref not in text:
                errors.append(f"{display_path(path)} must reference {ref}.")
    return errors


def iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_string_values(nested)


def display_path(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(ROOT.resolve(strict=False))).replace(
            "\\", "/"
        )
    except ValueError:
        return str(path).replace("\\", "/")
