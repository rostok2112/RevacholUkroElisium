from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import load_json
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/m2_synthetic_import_db.synthetic.json"
DOC_PATH = ROOT / "docs/m2-synthetic-import-format-contract.md"
ADR_PATH = ROOT / "docs/adr/0012-m2-local-extraction-import-scope.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
SCHEMA_VERSION = "m2-synthetic-import-db.v1"
SOURCE_KIND = "synthetic_fixture"
RECOMMENDED_NEXT_STEP = "m2_synthetic_import_validator_or_line_index_contract"
ALLOWED_RELATIONS = ("previous_visible", "nearby_branch", "player_option")

SAFETY_FLAG_FIELDS = (
    "real_game_text_included",
    "extracted_game_db_included",
    "private_input_read",
    "automatic_game_install_scanning",
    "arbitrary_drive_scanning",
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
    "extracted_text_committed",
    "generated_index_committed",
    "raw_payloads_included",
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
    "real extraction approved",
    "real db import approved",
    "real local input reads approved",
    "game file reads approved",
    "steam scanning approved",
    "automatic game install scanning approved",
    "bepinex log reads approved",
    "current-line capture approved",
    "current line capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "harmony patch approved",
    "hook implementation approved",
    "ocr approved",
    "provider execution approved",
    "companion contract change approved",
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
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the M2 synthetic import format.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m2_synthetic_import_format_errors()
    if errors:
        if args.quiet:
            print("M2 synthetic import format check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("M2 synthetic import format check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m2-synthetic-import-format-check.v1",
                    "fixture_schema_version": SCHEMA_VERSION,
                    "source_kind": SOURCE_KIND,
                    "implementation_added": False,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m2_synthetic_import_format_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 synthetic import fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 synthetic import fixture must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_unsafe_value_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"M2 synthetic import schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("source_kind") != SOURCE_KIND:
        errors.append(f"M2 synthetic import source_kind must be {SOURCE_KIND!r}.")

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        errors.append("M2 synthetic import metadata must be an object.")
    else:
        for field in ("fixture_only", "invented_text_only", "contract_only"):
            if metadata.get(field) is not True:
                errors.append(f"M2 synthetic import metadata must set {field}=true.")
        for field in (
            "m2_import_locally_extracted_db_done",
            "m2_line_index_done",
            "m2_context_graph_done",
        ):
            if metadata.get(field) is not False:
                errors.append(f"M2 synthetic import metadata must keep {field}=false.")
        if metadata.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
            errors.append(f"M2 synthetic import next step must be {RECOMMENDED_NEXT_STEP!r}.")

    flags = payload.get("safety_flags")
    if not isinstance(flags, dict):
        errors.append("M2 synthetic import safety_flags must be an object.")
    else:
        for field in SAFETY_FLAG_FIELDS:
            if flags.get(field) is not False:
                errors.append(f"M2 synthetic import fixture must keep safety_flags.{field}=false.")

    record_ids: set[str] = set()
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append("M2 synthetic import records must be a non-empty list.")
    else:
        for index, record in enumerate(records):
            errors.extend(_record_errors(record, index, record_ids))

    edges = payload.get("context_edges")
    if not isinstance(edges, list) or not edges:
        errors.append("M2 synthetic import context_edges must be a non-empty list.")
    else:
        seen_edges: set[tuple[str, str, str]] = set()
        for index, edge in enumerate(edges):
            errors.extend(_edge_errors(edge, index, record_ids, seen_edges))
    return errors


def _record_errors(record: Any, index: int, record_ids: set[str]) -> list[str]:
    if not isinstance(record, dict):
        return [f"M2 synthetic import record {index} must be an object."]
    errors: list[str] = []
    record_id = record.get("record_id")
    if not isinstance(record_id, str) or not record_id.startswith("synthetic.m2.line."):
        errors.append(f"M2 synthetic import record {index} must use a synthetic.m2.line.* id.")
    elif record_id in record_ids:
        errors.append(f"Duplicate M2 synthetic import record_id {record_id!r}.")
    else:
        record_ids.add(record_id)
    if record.get("line_id") != record_id:
        errors.append(f"M2 synthetic import record {record_id!r} line_id must match record_id.")
    for field, prefix in (
        ("conversation_id", "synthetic.m2.conversation."),
        ("speaker_id", "synthetic.m2.speaker."),
        ("speaker_label", "synthetic_"),
        ("context_placeholder", "synthetic_"),
    ):
        value = record.get(field)
        if not isinstance(value, str) or not value.startswith(prefix):
            errors.append(
                f"M2 synthetic import record {record_id!r} must use {prefix}* for {field}."
            )
    if not isinstance(record.get("source_text"), str) or not record["source_text"].strip():
        errors.append(
            f"M2 synthetic import record {record_id!r} must include invented source_text."
        )
    tags = record.get("context_tags")
    if (
        not isinstance(tags, list)
        or not tags
        or not all(
            isinstance(tag, str) and tag.startswith(("synthetic-", "invented-")) for tag in tags
        )
    ):
        errors.append(f"M2 synthetic import record {record_id!r} must use synthetic context_tags.")
    redacted = record.get("redacted_metadata")
    if not isinstance(redacted, dict):
        errors.append(f"M2 synthetic import record {record_id!r} must include redacted_metadata.")
    else:
        if redacted.get("fixture_only") is not True:
            errors.append(f"M2 synthetic import record {record_id!r} must set fixture_only=true.")
        if redacted.get("invented_text_only") is not True:
            errors.append(
                f"M2 synthetic import record {record_id!r} must set invented_text_only=true."
            )
        if redacted.get("real_game_text") is not False:
            errors.append(
                f"M2 synthetic import record {record_id!r} must set real_game_text=false."
            )
    return errors


def _edge_errors(
    edge: Any,
    index: int,
    record_ids: set[str],
    seen_edges: set[tuple[str, str, str]],
) -> list[str]:
    if not isinstance(edge, dict):
        return [f"M2 synthetic import context edge {index} must be an object."]
    errors: list[str] = []
    from_id = edge.get("from_record_id")
    to_id = edge.get("to_record_id")
    relation = edge.get("relation")
    if from_id not in record_ids:
        errors.append(f"M2 synthetic import edge {index} references unknown from_record_id.")
    if to_id not in record_ids:
        errors.append(f"M2 synthetic import edge {index} references unknown to_record_id.")
    if from_id == to_id:
        errors.append(f"M2 synthetic import edge {index} must not reference itself.")
    if relation not in ALLOWED_RELATIONS:
        errors.append(f"M2 synthetic import edge {index} uses an unknown relation.")
    if isinstance(from_id, str) and isinstance(to_id, str) and isinstance(relation, str):
        identity = (from_id, to_id, relation)
        if identity in seen_edges:
            errors.append(f"M2 synthetic import edge {index} duplicates an earlier edge.")
        seen_edges.add(identity)
    return errors


def _unsafe_value_errors(payload: Any, path: Path) -> list[str]:
    errors: list[str] = []
    relative = _display_path(path)
    for value in _iter_string_values(payload):
        for url in URL_PATTERN.findall(value):
            errors.append(f"{relative}: contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(value):
            errors.append(f"{relative}: contains a secret/API-key-looking value.")
        if WINDOWS_PRIVATE_PATH_PATTERN.search(value) or POSIX_PRIVATE_PATH_PATTERN.search(value):
            errors.append(f"{relative}: contains a private absolute path.")
        lowered = value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{relative}: contains forbidden marker {marker!r}.")
    return errors


def _doc_errors() -> list[str]:
    errors: list[str] = []
    fixture_ref = "tests/fixtures/m2_synthetic_import_db.synthetic.json"
    checker_ref = "scripts/check_m2_synthetic_import_format.py"
    doc_ref = "docs/m2-synthetic-import-format-contract.md"
    for path in (DOC_PATH, ADR_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
        if not path.exists():
            errors.append(f"Missing M2 synthetic import format doc: {_display_path(path)}.")
            continue
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for required in (fixture_ref, checker_ref, doc_ref):
            if required not in text:
                errors.append(f"{_display_path(path)} must point to {required}.")
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
