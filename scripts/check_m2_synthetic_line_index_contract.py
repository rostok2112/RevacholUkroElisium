from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.m2_synthetic_import_validator import (
        SCHEMA_VERSION as IMPORT_SCHEMA_VERSION,
        load_and_validate_m2_synthetic_import,
    )
    from scripts.run_m2_synthetic_line_index_builder_dry_run import (
        build_m2_synthetic_line_index,
    )
    from scripts.schema_validator import collect_errors, load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from m2_synthetic_import_validator import (
        SCHEMA_VERSION as IMPORT_SCHEMA_VERSION,
        load_and_validate_m2_synthetic_import,
    )
    from run_m2_synthetic_line_index_builder_dry_run import build_m2_synthetic_line_index
    from schema_validator import collect_errors, load_json
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/m2_synthetic_line_index.synthetic.json"
IMPORT_FIXTURE_PATH = ROOT / "tests/fixtures/m2_synthetic_import_db.synthetic.json"
SCHEMA_PATH = ROOT / "specs/m2-synthetic-line-index.schema.json"
DOC_PATH = ROOT / "docs/m2-synthetic-line-index-contract.md"
ADR_PATH = ROOT / "docs/adr/0012-m2-local-extraction-import-scope.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
SCHEMA_VERSION = "m2-synthetic-line-index.v1"
RECOMMENDED_NEXT_STEP = "m2_synthetic_line_index_builder_dry_run"
SAFETY_FLAG_FIELDS = (
    "real_game_text_included",
    "source_text_included",
    "file_contents_included",
    "paths_included",
    "filenames_included",
    "hashes_included",
    "raw_payloads_included",
    "logs_included",
    "context_edges_included",
    "private_input_read",
    "automatic_game_install_scanning",
    "game_files_read",
    "bepinex_logs_read",
    "screenshots_read",
    "ocr_used",
    "save_files_read",
    "decompiled_code_used",
    "current_line_capture_used",
    "ui_text_reading_used",
    "unity_scanning_used",
    "hooks_used",
    "provider_called",
    "companion_contract_changed",
    "generated_index_committed",
)
FORBIDDEN_FIELD_NAMES = (
    "source_text",
    "filename",
    "path",
    "digest",
    "hash",
    "context_edges",
    "raw_payload",
    "log",
)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:[\\/](?:Users|Program Files|Games|Steam|GOG|AppData)[\\/]",
    re.IGNORECASE,
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")
FORBIDDEN_VALUE_MARKERS = (
    "raw payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "screen capture",
    "steamapps",
    "savegame",
    ".sav",
    "decompiled",
    "dnspy",
    "ilspy",
    "real extraction approved",
    "current-line capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "provider execution approved",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the M2 synthetic line-index contract.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m2_synthetic_line_index_contract_errors()
    if errors:
        if args.quiet:
            print("M2 synthetic line-index contract check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M2 synthetic line-index contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m2-synthetic-line-index-contract-check.v1",
                    "fixture_schema_version": SCHEMA_VERSION,
                    "builder_added": False,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m2_synthetic_line_index_contract_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 synthetic line-index fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 synthetic line-index fixture must be an object."]

    errors = collect_errors(payload, load_json(SCHEMA_PATH))
    try:
        source = load_and_validate_m2_synthetic_import(IMPORT_FIXTURE_PATH)
    except Exception as exc:
        errors.append(f"Could not validate M2 synthetic import fixture: {exc}")
        source = None
    if source is not None:
        errors.extend(_mapping_errors(payload, source))
        if payload != build_m2_synthetic_line_index(source):
            errors.append("$: must match deterministic synthetic line-index builder output.")
    errors.extend(_safety_errors(payload))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
    return errors


def _mapping_errors(payload: dict[str, Any], source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    entries = payload.get("entries")
    if not isinstance(entries, list):
        return errors
    source_records = {record["record_id"]: record for record in source["records"]}
    expected_ids = sorted(source_records)
    actual_ids = [entry.get("record_id") for entry in entries if isinstance(entry, dict)]
    if payload.get("record_count") != len(entries):
        errors.append("$.record_count: must match entries length.")
    if actual_ids != expected_ids:
        errors.append("$.entries: must contain each synthetic import record exactly once in order.")
    line_ids = [entry.get("line_id") for entry in entries if isinstance(entry, dict)]
    if line_ids != sorted(line_ids):
        errors.append("$.entries: must be sorted by line_id.")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        record = source_records.get(entry.get("record_id"))
        if record is None:
            continue
        for field in (
            "line_id",
            "record_id",
            "conversation_id",
            "speaker_id",
            "context_placeholder",
        ):
            if entry.get(field) != record.get(field):
                errors.append(f"$.entries[{index}].{field}: must match the source record.")
        if entry.get("context_tags") != sorted(record["context_tags"]):
            errors.append(f"$.entries[{index}].context_tags: must match sorted source tags.")
    return errors


def _safety_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("source_schema_version") != IMPORT_SCHEMA_VERSION:
        errors.append(f"$.source_schema_version: must be {IMPORT_SCHEMA_VERSION!r}.")
    flags = payload.get("safety_flags")
    if isinstance(flags, dict):
        for field in SAFETY_FLAG_FIELDS:
            if flags.get(field) is not False:
                errors.append(f"$.safety_flags.{field}: must remain false.")
    for field in _iter_field_names(payload):
        if field in FORBIDDEN_FIELD_NAMES:
            errors.append(f"$: contains forbidden field {field!r}.")
    for value in _iter_string_values(payload):
        for url in URL_PATTERN.findall(value):
            errors.append(f"$: contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(value):
            errors.append("$: contains a secret/API-key-looking value.")
        if WINDOWS_PRIVATE_PATH_PATTERN.search(value) or POSIX_PRIVATE_PATH_PATTERN.search(value):
            errors.append("$: contains a private absolute path.")
        lowered = value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"$: contains forbidden marker {marker!r}.")
    return errors


def _doc_errors() -> list[str]:
    errors: list[str] = []
    required_refs = (
        "docs/m2-synthetic-line-index-contract.md",
        "specs/m2-synthetic-line-index.schema.json",
        "tests/fixtures/m2_synthetic_line_index.synthetic.json",
        "scripts/check_m2_synthetic_line_index_contract.py",
    )
    for path in (DOC_PATH, ADR_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
        if not path.exists():
            errors.append(f"Missing M2 line-index contract doc: {_display_path(path)}.")
            continue
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for required in required_refs:
            if required not in text:
                errors.append(f"{_display_path(path)} must point to {required}.")
    return errors


def _iter_field_names(value: Any):
    if isinstance(value, dict):
        for field, nested in value.items():
            yield field
            yield from _iter_field_names(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_field_names(nested)


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
