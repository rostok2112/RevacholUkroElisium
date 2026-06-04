from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover
    from schema_validator import load_json
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/runtime_translation_memory_contract.synthetic.json"
DOC_PATH = ROOT / "docs/runtime-translation-memory-contract.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
KNOWN_RISKS_PATH = ROOT / "docs/devlog/KNOWN_RISKS.md"
DECISIONS_PENDING_PATH = ROOT / "docs/devlog/DECISIONS_PENDING.md"
GITIGNORE_PATH = ROOT / ".gitignore"

SCHEMA_VERSION = "runtime-translation-memory-contract.v1"
RECOMMENDED_NEXT_STEP = "runtime_current_line_capture_contract"
EVENT_ROOT = "workspace/local-private/runtime-events/"
ANNOTATION_ROOT = "workspace/local-private/runtime-annotations/"
CACHE_ROOT = "workspace/local-private/runtime-cache/translation-memory/"
SUMMARY_ROOT = "workspace/local-private/runtime-cache/translation-memory-summary/"

REQUIRED_TRUE_FIELDS = (
    "runtime_first_path_active",
    "translation_memory_required_before_provider",
    "line_id_key_preferred",
    "fallback_private_content_key_allowed",
)
REQUIRED_FALSE_FIELDS = (
    "provider_call_required_on_cache_hit",
    "provider_execution_allowed",
    "game_file_reads_allowed",
    "automatic_game_install_scanning_allowed",
    "bepinex_log_reads_allowed",
    "ocr_allowed",
    "screenshots_allowed",
    "companion_contract_change_allowed",
    "cache_artifact_commit_allowed",
    "source_text_commit_allowed",
    "translated_text_commit_allowed",
    "hash_or_key_public_output_allowed",
    "raw_provider_payload_public_output_allowed",
    "private_paths_public_output_allowed",
)

SECRET_PATTERN = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|api[_-]?key\s*=|bearer\s+)", re.I)
URL_PATTERN = re.compile(r"https?://", re.I)
PRIVATE_PATH_PATTERN = re.compile(r"(\b[A-Za-z]:[\\/]|/(?:home|Users|mnt|Volumes)/)", re.I)
FORBIDDEN_MARKERS = (
    "provider execution approved",
    "game file reads approved",
    "raw provider payload",
    "payload dump",
    "raw prompt",
    "raw log",
    "logoutput.log",
    "screenshot",
    "steamapps",
    "decompiled",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate runtime translation-memory contract.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    errors = collect_runtime_translation_memory_contract_errors()
    if errors:
        if args.quiet:
            print("Runtime translation memory contract check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("Runtime translation memory contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "runtime-translation-memory-contract-check.v1",
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_runtime_translation_memory_contract_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load runtime translation memory fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["Runtime translation memory fixture must be a JSON object."]
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(f"recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"{field} must be true.")
    for field in REQUIRED_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"{field} must be false.")
    expected_roots = {
        "allowed_private_event_roots": [EVENT_ROOT],
        "allowed_private_annotation_roots": [ANNOTATION_ROOT],
        "allowed_private_cache_roots": [CACHE_ROOT],
        "allowed_private_summary_roots": [SUMMARY_ROOT],
    }
    for field, expected in expected_roots.items():
        if payload.get(field) != expected:
            errors.append(f"{field} must be {expected!r}.")
        for root in payload.get(field, []):
            if not isinstance(root, str) or not root.startswith("workspace/local-private/"):
                errors.append(f"{field} must stay under workspace/local-private/.")
            if isinstance(root, str) and (".." in Path(root).parts or not root.endswith("/")):
                errors.append(f"{field} roots must end with '/' and not contain '..'.")
    if "workspace/" not in GITIGNORE_PATH.read_text(encoding="utf-8"):
        errors.append(".gitignore must keep workspace/ ignored.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    expected = {
        SCHEMA_VERSION,
        RECOMMENDED_NEXT_STEP,
        EVENT_ROOT,
        ANNOTATION_ROOT,
        CACHE_ROOT,
        SUMMARY_ROOT,
    }
    for value in _iter_string_values(payload):
        if value in expected:
            continue
        lowered = value.lower()
        if URL_PATTERN.search(value):
            errors.append(f"{_display_path(path)} contains an external URL.")
        if SECRET_PATTERN.search(value):
            errors.append(f"{_display_path(path)} contains a secret-looking value.")
        if PRIVATE_PATH_PATTERN.search(value):
            errors.append(f"{_display_path(path)} contains a private absolute path.")
        for marker in FORBIDDEN_MARKERS:
            if marker in lowered:
                errors.append(f"{_display_path(path)} contains forbidden marker {marker!r}.")
    return errors


def _doc_errors() -> list[str]:
    required_refs = (
        "docs/runtime-translation-memory-contract.md",
        "tests/fixtures/runtime_translation_memory_contract.synthetic.json",
        "scripts/check_runtime_translation_memory_contract.py",
        "scripts/run_runtime_translation_memory.py",
        RECOMMENDED_NEXT_STEP,
    )
    errors: list[str] = []
    for doc_path in (
        DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        KNOWN_RISKS_PATH,
        DECISIONS_PENDING_PATH,
    ):
        if not doc_path.exists():
            errors.append(f"Missing doc target: {_display_path(doc_path)}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for ref in required_refs:
            if ref not in text:
                errors.append(f"{_display_path(doc_path)} must reference {ref}.")
    return errors


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_string_values(nested)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(ROOT.resolve(strict=False))).replace(
            "\\", "/"
        )
    except ValueError:
        return path.name


if __name__ == "__main__":
    raise SystemExit(main())
