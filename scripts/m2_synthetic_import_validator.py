from __future__ import annotations

from pathlib import Path
import re
from typing import Any

try:
    from scripts.schema_validator import collect_errors, load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import collect_errors, load_json
    from synthetic_slice import ROOT


SCHEMA_PATH = ROOT / "specs/m2-synthetic-import-db.schema.json"
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


class M2SyntheticImportValidationError(ValueError):
    """Raised when an M2 synthetic import payload violates the static contract."""


def load_and_validate_m2_synthetic_import(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    assert_valid_m2_synthetic_import(payload)
    return payload


def assert_valid_m2_synthetic_import(payload: Any) -> None:
    errors = collect_m2_synthetic_import_errors(payload)
    if errors:
        raise M2SyntheticImportValidationError("; ".join(errors))


def collect_m2_synthetic_import_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["$: M2 synthetic import payload must be an object."]

    errors = collect_errors(payload, load_json(SCHEMA_PATH))
    record_ids: set[str] = set()
    records = payload.get("records")
    if isinstance(records, list):
        if not records:
            errors.append("$.records: must be a non-empty list.")
        for index, record in enumerate(records):
            errors.extend(_record_errors(record, index, record_ids))

    edges = payload.get("context_edges")
    if isinstance(edges, list):
        if not edges:
            errors.append("$.context_edges: must be a non-empty list.")
        seen_edges: set[tuple[str, str, str]] = set()
        for index, edge in enumerate(edges):
            errors.extend(_edge_errors(edge, index, record_ids, seen_edges))

    errors.extend(_unsafe_value_errors(payload))
    return errors


def _record_errors(record: Any, index: int, record_ids: set[str]) -> list[str]:
    if not isinstance(record, dict):
        return []
    errors: list[str] = []
    record_id = record.get("record_id")
    if not isinstance(record_id, str) or not record_id.startswith("synthetic.m2.line."):
        errors.append(f"$.records[{index}].record_id: must use synthetic.m2.line.*.")
    elif record_id in record_ids:
        errors.append(f"$.records[{index}].record_id: duplicate id {record_id!r}.")
    else:
        record_ids.add(record_id)
    if record.get("line_id") != record_id:
        errors.append(f"$.records[{index}].line_id: must match record_id.")
    for field, prefix in (
        ("conversation_id", "synthetic.m2.conversation."),
        ("speaker_id", "synthetic.m2.speaker."),
        ("speaker_label", "synthetic_"),
        ("context_placeholder", "synthetic_"),
    ):
        value = record.get(field)
        if not isinstance(value, str) or not value.startswith(prefix):
            errors.append(f"$.records[{index}].{field}: must use {prefix}*.")
    source_text = record.get("source_text")
    if not isinstance(source_text, str) or not source_text.strip():
        errors.append(f"$.records[{index}].source_text: must include invented text.")
    tags = record.get("context_tags")
    if isinstance(tags, list) and (
        not tags
        or not all(
            isinstance(tag, str) and tag.startswith(("synthetic-", "invented-")) for tag in tags
        )
    ):
        errors.append(f"$.records[{index}].context_tags: must use synthetic placeholders.")
    return errors


def _edge_errors(
    edge: Any,
    index: int,
    record_ids: set[str],
    seen_edges: set[tuple[str, str, str]],
) -> list[str]:
    if not isinstance(edge, dict):
        return []
    errors: list[str] = []
    from_id = edge.get("from_record_id")
    to_id = edge.get("to_record_id")
    relation = edge.get("relation")
    if from_id not in record_ids:
        errors.append(f"$.context_edges[{index}].from_record_id: references an unknown record.")
    if to_id not in record_ids:
        errors.append(f"$.context_edges[{index}].to_record_id: references an unknown record.")
    if from_id == to_id:
        errors.append(f"$.context_edges[{index}]: must not reference itself.")
    if relation not in ALLOWED_RELATIONS:
        errors.append(f"$.context_edges[{index}].relation: uses an unknown relation.")
    if isinstance(from_id, str) and isinstance(to_id, str) and isinstance(relation, str):
        identity = (from_id, to_id, relation)
        if identity in seen_edges:
            errors.append(f"$.context_edges[{index}]: duplicates an earlier edge.")
        seen_edges.add(identity)
    return errors


def _unsafe_value_errors(payload: Any) -> list[str]:
    errors: list[str] = []
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


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_string_values(nested)
