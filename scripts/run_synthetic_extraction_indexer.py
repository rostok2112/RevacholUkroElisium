from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import load_json
    from synthetic_slice import ROOT


SOURCE_SCHEMA_VERSION = "extraction-index-source-records.v1"
INDEX_SCHEMA_VERSION = "extraction-index.v1"
SUMMARY_SCHEMA_VERSION = "extraction-indexer-summary.v1"
SOURCE_FIXTURE = ROOT / "tests/fixtures/extraction_index_source_records.synthetic.json"
EXPECTED_INDEX_FIXTURE = ROOT / "tests/fixtures/extraction_index.synthetic.json"
DEFAULT_OUTPUT_ROOT = ROOT / "workspace/local-private/extraction-indexing"
PRIVATE_INDEX_ROOT = "workspace/local-private/extraction-indexing/"

STOPWORDS = {
    "a",
    "an",
    "and",
    "another",
    "of",
    "the",
    "while",
}

SAFETY_FLAG_FIELDS = (
    "real_game_text_included",
    "raw_payloads_included",
    "automatic_game_install_scanning",
    "game_files_read",
    "bepinex_logs_read",
    "screenshots_read",
    "ocr_used",
    "hooks_used",
    "unity_scanning_used",
    "current_line_capture_used",
    "ui_text_reading_used",
    "decompiled_code_used",
    "companion_contract_changed",
    "provider_called",
)

URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:(?:\\\\|\\)(?:Users|Program Files|Games|Steam|GOG)(?:\\\\|\\)"
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")

FORBIDDEN_VALUE_MARKERS = (
    "current-line capture approved",
    "current line capture approved",
    "real text capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "harmony patch approved",
    "ocr approved",
    "automatic game install scanning approved",
    "raw payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "screen capture",
    "steamapps",
    "data/extracted",
    "data/local",
)


class SyntheticExtractionIndexError(RuntimeError):
    """Raised when synthetic extraction source or index data is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic synthetic extraction index. This helper reads synthetic "
            "fixtures only and never scans game files."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=SOURCE_FIXTURE,
        help="Synthetic source records fixture. Defaults to the committed synthetic fixture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path under workspace/local-private/extraction-indexing/.",
    )
    parser.add_argument(
        "--check-fixture",
        action="store_true",
        help="Compare the generated index with the committed synthetic index fixture.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short status line.")
    args = parser.parse_args(argv)

    try:
        source = load_source_records(args.source)
        index = build_extraction_index(source, source_path=args.source)
        validate_extraction_index(index, source)

        if args.check_fixture:
            expected = load_json(EXPECTED_INDEX_FIXTURE)
            if index != expected:
                raise SyntheticExtractionIndexError(
                    "Generated synthetic extraction index does not match committed fixture."
                )

        output_path = resolve_output_path(args.output) if args.output else None
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

        summary = build_summary(index, output_written=bool(output_path))
        if args.quiet:
            print("Synthetic extraction indexer passed.")
        else:
            print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    except (OSError, SyntheticExtractionIndexError, ValueError) as exc:
        parser.error(str(exc))
    return 0


def load_source_records(path: Path = SOURCE_FIXTURE) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise SyntheticExtractionIndexError(
            "Synthetic extraction source fixture must be an object."
        )
    validate_source_records(payload)
    return payload


def build_extraction_index(
    source: dict[str, Any], *, source_path: Path = SOURCE_FIXTURE
) -> dict[str, Any]:
    validate_source_records(source)
    source_digest = _sha256_json(source)
    records = source["records"]
    indexed_records: list[dict[str, Any]] = []
    term_to_records: dict[str, set[str]] = {}

    for record in records:
        terms = sorted(_terms_for_record(record))
        record_id = record["record_id"]
        for term in terms:
            term_to_records.setdefault(term, set()).add(record_id)
        indexed_records.append(
            {
                "record_id": record_id,
                "source_kind": "synthetic_fixture",
                "text_digest": _sha256_text(record["source_text"]),
                "term_count": len(terms),
                "terms": terms,
                "context_tags": sorted(record.get("context_tags", [])),
                "glossary_tokens": sorted(
                    _normalize_token(token) for token in record["glossary_tokens"]
                ),
            }
        )

    terms = [
        {
            "term": term,
            "record_ids": sorted(record_ids),
            "record_count": len(record_ids),
        }
        for term, record_ids in sorted(term_to_records.items())
    ]

    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "source_schema_version": SOURCE_SCHEMA_VERSION,
        "source_fixture": _relative_source_path(source_path),
        "generated_from_synthetic_fixture": True,
        "private_index_root": PRIVATE_INDEX_ROOT,
        "record_count": len(indexed_records),
        "source_digest": source_digest,
        "records": indexed_records,
        "terms": terms,
        "safety_flags": _safe_flags(),
    }


def validate_source_records(source: dict[str, Any]) -> None:
    errors: list[str] = []
    if source.get("schema_version") != SOURCE_SCHEMA_VERSION:
        errors.append(f"Source schema_version must be {SOURCE_SCHEMA_VERSION!r}.")
    if source.get("source_kind") != "synthetic_fixture":
        errors.append("Source fixture source_kind must be 'synthetic_fixture'.")
    if source.get("generated_from_synthetic_fixture") is not True:
        errors.append("Source fixture must set generated_from_synthetic_fixture=true.")
    _validate_safety_flags(source.get("safety_flags"), errors, label="Source fixture")

    records = source.get("records")
    if not isinstance(records, list) or not records:
        errors.append("Source fixture records must be a non-empty list.")
    else:
        seen_ids: set[str] = set()
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f"Source record {index} must be an object.")
                continue
            record_id = record.get("record_id")
            if not isinstance(record_id, str) or not record_id.startswith("synthetic.extract."):
                errors.append(f"Source record {index} must use a synthetic.extract.* record_id.")
            elif record_id in seen_ids:
                errors.append(f"Duplicate source record_id {record_id!r}.")
            else:
                seen_ids.add(record_id)
            if not isinstance(record.get("source_text"), str) or not record["source_text"].strip():
                errors.append(f"Source record {record_id!r} must include non-empty source_text.")
            if not isinstance(record.get("speaker_label"), str) or not record[
                "speaker_label"
            ].startswith("synthetic_"):
                errors.append(f"Source record {record_id!r} must use a synthetic speaker_label.")
            for field in ("context_tags", "glossary_tokens"):
                values = record.get(field)
                if not isinstance(values, list) or not all(
                    isinstance(item, str) for item in values
                ):
                    errors.append(f"Source record {record_id!r} field {field!r} must be strings.")
            metadata = record.get("redacted_metadata")
            if not isinstance(metadata, dict):
                errors.append(f"Source record {record_id!r} must include redacted_metadata.")
            else:
                if metadata.get("fixture_only") is not True:
                    errors.append(f"Source record {record_id!r} must set fixture_only=true.")
                if metadata.get("real_game_text") is not False:
                    errors.append(f"Source record {record_id!r} must set real_game_text=false.")

    errors.extend(_unsafe_string_errors(source, label="Synthetic extraction source fixture"))
    if errors:
        raise SyntheticExtractionIndexError("; ".join(errors))


def validate_extraction_index(index: dict[str, Any], source: dict[str, Any] | None = None) -> None:
    errors: list[str] = []
    if index.get("schema_version") != INDEX_SCHEMA_VERSION:
        errors.append(f"Index schema_version must be {INDEX_SCHEMA_VERSION!r}.")
    if index.get("source_schema_version") != SOURCE_SCHEMA_VERSION:
        errors.append(f"Index source_schema_version must be {SOURCE_SCHEMA_VERSION!r}.")
    if index.get("generated_from_synthetic_fixture") is not True:
        errors.append("Index must set generated_from_synthetic_fixture=true.")
    if index.get("private_index_root") != PRIVATE_INDEX_ROOT:
        errors.append(f"Index private_index_root must be {PRIVATE_INDEX_ROOT!r}.")
    _validate_safety_flags(index.get("safety_flags"), errors, label="Index fixture")

    records = index.get("records")
    terms = index.get("terms")
    if not isinstance(records, list):
        errors.append("Index records must be a list.")
    elif index.get("record_count") != len(records):
        errors.append("Index record_count must match records length.")
    if not isinstance(terms, list):
        errors.append("Index terms must be a list.")

    if source is not None and index.get("source_digest") != _sha256_json(source):
        errors.append("Index source_digest must match the source fixture digest.")

    errors.extend(_unsafe_string_errors(index, label="Synthetic extraction index fixture"))
    if errors:
        raise SyntheticExtractionIndexError("; ".join(errors))


def build_summary(index: dict[str, Any], *, output_written: bool) -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "index_schema_version": index["schema_version"],
        "record_count": index["record_count"],
        "term_count": len(index["terms"]),
        "generated_from_synthetic_fixture": True,
        "private_index_root": PRIVATE_INDEX_ROOT,
        "output_written": output_written,
        "real_game_text_included": False,
        "raw_payloads_included": False,
        "game_files_read": False,
        "automatic_game_install_scanning": False,
        "bepinex_logs_read": False,
        "screenshots_read": False,
        "provider_called": False,
    }


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    output_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise ValueError(
            "Unsafe output path. Use a path under workspace/local-private/extraction-indexing/ "
            "for generated private extraction indexes."
        )
    return resolved


def _terms_for_record(record: dict[str, Any]) -> set[str]:
    text_terms = {
        _normalize_token(token)
        for token in re.findall(r"[A-Za-z0-9]+", record["source_text"].lower())
    }
    glossary_terms = {_normalize_token(token) for token in record["glossary_tokens"]}
    return {term for term in text_terms | glossary_terms if term and term not in STOPWORDS}


def _normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _validate_safety_flags(value: Any, errors: list[str], *, label: str) -> None:
    if not isinstance(value, dict):
        errors.append(f"{label} must include safety_flags.")
        return
    for field in SAFETY_FLAG_FIELDS:
        if not isinstance(value.get(field), bool):
            errors.append(f"{label} safety flag {field!r} must be a boolean.")
        elif value.get(field) is not False:
            errors.append(f"{label} safety flag {field!r} must remain false.")


def _unsafe_string_errors(value: Any, *, label: str) -> list[str]:
    errors: list[str] = []
    for string_value in _iter_string_values(value):
        for url in URL_PATTERN.findall(string_value):
            errors.append(f"{label} contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(string_value):
            errors.append(f"{label} contains a secret/API-key-looking value.")
        if WINDOWS_PRIVATE_PATH_PATTERN.search(string_value) or POSIX_PRIVATE_PATH_PATTERN.search(
            string_value
        ):
            errors.append(f"{label} contains a private absolute path.")
        lowered = string_value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{label} contains forbidden marker {marker!r}.")
    return errors


def _safe_flags() -> dict[str, bool]:
    return {field: False for field in SAFETY_FLAG_FIELDS}


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _relative_source_path(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(ROOT.resolve(strict=False))).replace(
            "\\", "/"
        )
    except ValueError:
        return "user_supplied_synthetic_source"


def _iter_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(_iter_string_values(item))
        return strings
    if isinstance(value, dict):
        strings = []
        for item in value.values():
            strings.extend(_iter_string_values(item))
        return strings
    return []


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
