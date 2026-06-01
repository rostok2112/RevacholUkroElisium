from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.m2_synthetic_import_validator import (
        SCHEMA_VERSION as IMPORT_SCHEMA_VERSION,
        load_and_validate_m2_synthetic_import,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from m2_synthetic_import_validator import (
        SCHEMA_VERSION as IMPORT_SCHEMA_VERSION,
        load_and_validate_m2_synthetic_import,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


INDEX_SCHEMA_VERSION = "m2-synthetic-line-index.v1"
SUMMARY_SCHEMA_VERSION = "m2-synthetic-line-index-builder-dry-run-summary.v1"
SOURCE_FIXTURE = ROOT / "tests/fixtures/m2_synthetic_import_db.synthetic.json"
EXPECTED_INDEX_FIXTURE = ROOT / "tests/fixtures/m2_synthetic_line_index.synthetic.json"
PRIVATE_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/import/line-index/"

FALSE_SAFETY_FIELDS = (
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


class M2SyntheticLineIndexBuilderDryRunError(RuntimeError):
    """Raised when the synthetic line-index dry-run request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a metadata-only M2 line index from an invented synthetic fixture."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=SOURCE_FIXTURE,
        help="Explicit synthetic import JSON. Defaults to the committed invented fixture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional output under workspace/local-private/extraction-indexing/import/line-index/."
        ),
    )
    parser.add_argument(
        "--check-fixture",
        action="store_true",
        help="Compare generated metadata with the committed synthetic line-index fixture.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    try:
        source = load_and_validate_m2_synthetic_import(args.source)
        index = build_m2_synthetic_line_index(source)
        assert_valid_m2_synthetic_line_index(index, source)
        if args.check_fixture and index != load_json(EXPECTED_INDEX_FIXTURE):
            raise M2SyntheticLineIndexBuilderDryRunError(
                "Generated M2 synthetic line index does not match the committed fixture."
            )

        output_path = resolve_output_path(args.output) if args.output else None
        if output_path:
            write_m2_synthetic_line_index(index, output_path)

        if args.quiet:
            print("M2 synthetic line-index builder dry-run passed.")
        else:
            print(json.dumps(build_summary(index, output_written=bool(output_path)), indent=2))
        return 0
    except (OSError, ValueError, M2SyntheticLineIndexBuilderDryRunError) as exc:
        parser.error(str(exc))
    return 0


def build_m2_synthetic_line_index(source: dict[str, Any]) -> dict[str, Any]:
    records = sorted(source["records"], key=lambda record: record["line_id"])
    return {
        "schema_version": INDEX_SCHEMA_VERSION,
        "source_schema_version": IMPORT_SCHEMA_VERSION,
        "source_kind": "synthetic_fixture",
        "generated_from_synthetic_fixture": True,
        "record_count": len(records),
        "entries": [
            {
                "line_id": record["line_id"],
                "record_id": record["record_id"],
                "conversation_id": record["conversation_id"],
                "speaker_id": record["speaker_id"],
                "context_placeholder": record["context_placeholder"],
                "context_tags": sorted(record["context_tags"]),
            }
            for record in records
        ],
        "metadata": {
            "fixture_only": True,
            "contract_only": True,
            "m2_import_locally_extracted_db_done": False,
            "m2_line_index_done": False,
            "m2_context_graph_done": False,
            "recommended_next_step": "m2_synthetic_line_index_builder_dry_run",
        },
        "safety_flags": {field: False for field in FALSE_SAFETY_FIELDS},
    }


def assert_valid_m2_synthetic_line_index(index: dict[str, Any], source: dict[str, Any]) -> None:
    errors: list[str] = []
    entries = index.get("entries")
    if index.get("schema_version") != INDEX_SCHEMA_VERSION:
        errors.append(f"schema_version must be {INDEX_SCHEMA_VERSION!r}.")
    if index.get("source_schema_version") != IMPORT_SCHEMA_VERSION:
        errors.append(f"source_schema_version must be {IMPORT_SCHEMA_VERSION!r}.")
    if index.get("source_kind") != "synthetic_fixture":
        errors.append("source_kind must be 'synthetic_fixture'.")
    if index.get("generated_from_synthetic_fixture") is not True:
        errors.append("generated_from_synthetic_fixture must remain true.")
    if not isinstance(entries, list):
        errors.append("entries must be a list.")
        entries = []
    if index.get("record_count") != len(entries):
        errors.append("record_count must match entries length.")

    expected = build_m2_synthetic_line_index(source)
    if index != expected:
        errors.append("line index must match the deterministic metadata-only source projection.")
    if errors:
        raise M2SyntheticLineIndexBuilderDryRunError("; ".join(errors))


def build_summary(index: dict[str, Any], *, output_written: bool) -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "index_schema_version": index["schema_version"],
        "record_count": index["record_count"],
        "generated_from_synthetic_fixture": True,
        "output_written": output_written,
        "real_game_text_included": False,
        "source_text_included": False,
        "context_edges_included": False,
        "paths_included": False,
        "filenames_included": False,
        "hashes_included": False,
        "raw_payloads_included": False,
        "logs_included": False,
        "private_input_read": False,
        "game_files_read": False,
        "automatic_game_install_scanning": False,
    }


def resolve_output_path(output: Path, *, root: Path = ROOT) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (root / raw).resolve(strict=False)
    )
    output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise M2SyntheticLineIndexBuilderDryRunError(
            "Unsafe output path. Use "
            "workspace/local-private/extraction-indexing/import/line-index/."
        )
    if resolved.exists() and resolved.is_dir():
        raise M2SyntheticLineIndexBuilderDryRunError("Output path must point to a JSON file.")
    return resolved


def write_m2_synthetic_line_index(index: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
