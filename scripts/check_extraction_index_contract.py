from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    from scripts.run_synthetic_extraction_indexer import (
        EXPECTED_INDEX_FIXTURE,
        INDEX_SCHEMA_VERSION,
        PRIVATE_INDEX_ROOT,
        SOURCE_FIXTURE,
        SOURCE_SCHEMA_VERSION,
        SyntheticExtractionIndexError,
        build_extraction_index,
        load_source_records,
        validate_extraction_index,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from run_synthetic_extraction_indexer import (
        EXPECTED_INDEX_FIXTURE,
        INDEX_SCHEMA_VERSION,
        PRIVATE_INDEX_ROOT,
        SOURCE_FIXTURE,
        SOURCE_SCHEMA_VERSION,
        SyntheticExtractionIndexError,
        build_extraction_index,
        load_source_records,
        validate_extraction_index,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


DOC_PATH = ROOT / "docs/extraction-indexing-private-index-contract.md"
ADR_PATH = ROOT / "docs/adr/0011-real-extraction-indexing-scope.md"
GITIGNORE_PATH = ROOT / ".gitignore"
CHECKER_REF = "scripts/check_extraction_index_contract.py"
INDEXER_REF = "scripts/run_synthetic_extraction_indexer.py"
SOURCE_FIXTURE_REF = "tests/fixtures/extraction_index_source_records.synthetic.json"
INDEX_FIXTURE_REF = "tests/fixtures/extraction_index.synthetic.json"

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


class ExtractionIndexContractError(RuntimeError):
    """Raised when the synthetic extraction index contract is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the synthetic extraction index/private index contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_extraction_index_contract_errors()
    if errors:
        if args.quiet:
            print("Extraction index contract check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("Extraction index contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "extraction-index-contract-check.v1",
                    "index_schema_version": INDEX_SCHEMA_VERSION,
                    "source_schema_version": SOURCE_SCHEMA_VERSION,
                    "private_index_root": PRIVATE_INDEX_ROOT,
                    "generated_from_synthetic_fixture": True,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_extraction_index_contract_safe() -> None:
    errors = collect_extraction_index_contract_errors()
    if errors:
        raise ExtractionIndexContractError("; ".join(errors))


def collect_extraction_index_contract_errors() -> list[str]:
    errors: list[str] = []
    try:
        source = load_source_records(SOURCE_FIXTURE)
    except Exception as exc:
        errors.append(f"Could not load synthetic extraction source fixture: {exc}")
        source = None

    try:
        expected_index = load_json(EXPECTED_INDEX_FIXTURE)
        if not isinstance(expected_index, dict):
            errors.append("Synthetic extraction index fixture must be a JSON object.")
            expected_index = None
    except Exception as exc:
        errors.append(f"Could not load synthetic extraction index fixture: {exc}")
        expected_index = None

    if source is not None and expected_index is not None:
        try:
            generated_index = build_extraction_index(source, source_path=SOURCE_FIXTURE)
            validate_extraction_index(expected_index, source)
            if generated_index != expected_index:
                errors.append(
                    "Committed synthetic extraction index fixture does not match deterministic "
                    "indexer output."
                )
        except SyntheticExtractionIndexError as exc:
            errors.append(str(exc))

    for path in (SOURCE_FIXTURE, EXPECTED_INDEX_FIXTURE):
        try:
            payload = load_json(path)
        except Exception:
            continue
        errors.extend(_unsafe_value_errors(payload, path))

    errors.extend(_private_root_errors())
    errors.extend(_doc_link_errors())
    return errors


def _private_root_errors() -> list[str]:
    errors: list[str] = []
    if PRIVATE_INDEX_ROOT != "workspace/local-private/extraction-indexing/":
        errors.append(
            "Private index root must remain workspace/local-private/extraction-indexing/."
        )
    if "workspace/" not in GITIGNORE_PATH.read_text(encoding="utf-8"):
        errors.append(".gitignore must keep workspace/ ignored for private extraction indexes.")
    return errors


def _doc_link_errors() -> list[str]:
    errors: list[str] = []
    for doc_path in (DOC_PATH, ADR_PATH):
        if not doc_path.exists():
            errors.append(f"Missing contract doc: {_display_path(doc_path)}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for required in (CHECKER_REF, INDEXER_REF, SOURCE_FIXTURE_REF, INDEX_FIXTURE_REF):
            if required not in text:
                errors.append(f"{_display_path(doc_path)} must point to {required}.")

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in (DOC_PATH, ADR_PATH) if path.exists()
    )
    for phrase in (
        "current-line capture is approved",
        "real text capture is approved",
        "automatic game install scanning is approved",
        "real extraction from game files is approved",
    ):
        if phrase in combined:
            errors.append(f"Extraction index contract docs must not say {phrase!r}.")
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


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
