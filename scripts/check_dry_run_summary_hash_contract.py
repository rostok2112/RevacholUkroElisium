from __future__ import annotations

import argparse
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


FIXTURE_PATH = ROOT / "tests/fixtures/dry_run_summary_hash_contract.synthetic.json"
DOC_PATH = ROOT / "docs/extraction-indexing-dry-run-summary-hash-contract.md"
ADR_PATH = ROOT / "docs/adr/0011-real-extraction-indexing-scope.md"
HASH_DECISION_DOC = ROOT / "docs/extraction-indexing-private-input-hash-contract.md"
INPUT_CONTRACT_DOC = ROOT / "docs/extraction-indexing-private-input-adapter-contract.md"
INDEX_CONTRACT_DOC = ROOT / "docs/extraction-indexing-private-index-contract.md"
SCHEMA_VERSION = "dry-run-summary-hash-contract.v1"
MILESTONE = "5A.6"
RECOMMENDED_NEXT_STEP = "dry_run_summary_hash_dry_run"
PRIVATE_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/"

ALLOWED_CANONICAL_SUMMARY_FIELDS = (
    "schema_version",
    "input_exists",
    "input_kind",
    "file_count",
    "directory_count",
    "total_size_bytes",
    "allowed_root",
    "private_output_root",
    "dry_run",
    "hashes_computed",
    "traversal_limit",
    "traversal_truncated",
    "blocker_categories",
    "output_written",
    "paths_redacted",
    "file_contents_read",
    "real_text_included",
    "raw_payloads_included",
    "raw_logs_included",
    "automatic_game_install_scanning",
    "game_files_read",
    "bepinex_logs_read",
    "game_logs_read",
    "screenshots_read",
    "ocr_used",
    "save_files_read",
    "hooks_used",
    "unity_scanning_used",
    "current_line_capture_used",
    "ui_text_reading_used",
    "decompiled_code_used",
    "companion_contract_changed",
    "provider_called",
)

EXCLUDED_HASH_INPUT_FIELDS = (
    "input_path",
    "allowed_root_path",
    "output_path",
    "filename",
    "directory_name",
    "file_contents",
    "raw_payload",
    "raw_log",
    "screenshot",
    "ocr_output",
    "save_file",
    "decompiled_output",
    "provider_payload",
    "generated_index",
    "timestamp",
    "report_path",
    "free_text_evidence",
)

CANONICALIZATION_RULES = (
    "utf8_json",
    "sorted_keys",
    "deterministic_separators",
    "stable_scalar_values_only",
    "sorted_blocker_categories",
    "no_path_bearing_fields",
    "no_content_bearing_fields",
    "no_timestamps",
    "no_environment_specific_values",
)

FORBIDDEN_PERMISSION_FIELDS = (
    "hash_implementation_allowed_next",
    "file_content_hashing_allowed",
    "path_string_hashing_allowed",
    "filename_hashing_allowed",
    "raw_payload_hashing_allowed",
    "raw_log_hashing_allowed",
    "screenshot_hashing_allowed",
    "ocr_hashing_allowed",
    "save_file_hashing_allowed",
    "decompiled_output_hashing_allowed",
    "provider_payload_hashing_allowed",
    "generated_index_hashing_allowed",
    "timestamp_hashing_allowed",
    "private_index_construction_allowed_next",
    "real_extraction_allowed",
    "automatic_game_install_scanning_allowed",
    "arbitrary_drive_scan_allowed",
    "bepinex_log_reads_allowed",
    "game_log_reads_allowed",
    "real_game_text_commit_allowed",
    "raw_extracted_payload_commit_allowed",
    "file_contents_reading_allowed",
    "current_line_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "ocr_allowed",
    "decompiled_code_allowed",
    "companion_contract_change_allowed",
    "provider_execution_allowed",
    "screenshots_allowed",
    "save_file_parsing_allowed",
)

URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:(?:\\\\|\\)(?:Users|Program Files|Games|Steam|GOG|AppData)(?:\\\\|\\)"
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:")

FORBIDDEN_VALUE_MARKERS = (
    "hash implementation approved",
    "file content hashing approved",
    "path string hashing approved",
    "filename hashing approved",
    "raw payload hashing approved",
    "private index construction approved",
    "current-line capture approved",
    "current line capture approved",
    "real text capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "harmony patch approved",
    "hook implementation approved",
    "ocr approved",
    "automatic game install scanning approved",
    "real extraction approved",
    "real extraction from game files approved",
    "companion contract change approved",
    "provider execution approved",
    "raw payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "screen capture",
    "steamapps",
    "bepinex",
    "savegame",
    ".sav",
    "decompiled",
    "dnspy",
    "ilspy",
)


class DryRunSummaryHashContractError(RuntimeError):
    """Raised when the dry-run summary hash contract is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Milestone 5A.6 dry-run summary hash contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_dry_run_summary_hash_contract_errors()
    if errors:
        if args.quiet:
            print("Dry-run summary hash contract check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("Dry-run summary hash contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "dry-run-summary-hash-contract-check.v1",
                    "fixture": str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/"),
                    "milestone": MILESTONE,
                    "hash_implementation_allowed_next": False,
                    "canonical_redacted_summary_hash_allowed_next": "contract_defined_only",
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_dry_run_summary_hash_contract_safe() -> None:
    errors = collect_dry_run_summary_hash_contract_errors()
    if errors:
        raise DryRunSummaryHashContractError("; ".join(errors))


def collect_dry_run_summary_hash_contract_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load dry-run summary hash contract fixture: {exc}"]

    if not isinstance(payload, dict):
        return ["Dry-run summary hash contract fixture must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_root_errors(payload))
    errors.extend(_list_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_link_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Dry-run summary hash schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("milestone") != MILESTONE:
        errors.append(f"Dry-run summary hash milestone must be {MILESTONE!r}.")
    if payload.get("decision_status") != "contract_only":
        errors.append("Dry-run summary hash decision_status must be 'contract_only'.")
    if payload.get("canonical_redacted_summary_hash_allowed_next") != "contract_defined_only":
        errors.append(
            "Dry-run summary hash fixture must keep "
            "canonical_redacted_summary_hash_allowed_next='contract_defined_only'."
        )
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(
            f"Dry-run summary hash recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}."
        )
    if payload.get("tracked_artifacts_redacted") is not True:
        errors.append("Dry-run summary hash fixture must set tracked_artifacts_redacted=true.")
    for field in FORBIDDEN_PERMISSION_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Dry-run summary hash field {field!r} must be a boolean.")
        elif payload.get(field) is not False:
            errors.append(f"Dry-run summary hash fixture must keep {field}=false.")
    return errors


def _root_errors(payload: dict[str, Any]) -> list[str]:
    root = payload.get("private_output_root")
    if root != PRIVATE_OUTPUT_ROOT:
        return [f"Dry-run summary hash private_output_root must be {PRIVATE_OUTPUT_ROOT!r}."]

    errors: list[str] = []
    normalized = root.replace("\\", "/")
    if normalized != root:
        errors.append("Dry-run summary hash private_output_root must use forward slashes.")
    if not normalized.startswith("workspace/"):
        errors.append("Dry-run summary hash private_output_root must stay under workspace/.")
    if not normalized.endswith("/"):
        errors.append("Dry-run summary hash private_output_root must end with '/'.")
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        errors.append("Dry-run summary hash private_output_root must not contain '..'.")
    if normalized.startswith("/") or WINDOWS_ABSOLUTE_PATH_PATTERN.match(normalized):
        errors.append("Dry-run summary hash private_output_root must be repo-relative.")
    if "extraction-indexing" not in normalized:
        errors.append(
            "Dry-run summary hash private_output_root must be scoped to extraction-indexing."
        )
    return errors


def _list_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if (
        tuple(payload.get("allowed_canonical_summary_fields", ()))
        != ALLOWED_CANONICAL_SUMMARY_FIELDS
    ):
        errors.append("Dry-run summary hash allowed_canonical_summary_fields changed unexpectedly.")
    if tuple(payload.get("excluded_hash_input_fields", ())) != EXCLUDED_HASH_INPUT_FIELDS:
        errors.append("Dry-run summary hash excluded_hash_input_fields changed unexpectedly.")
    if tuple(payload.get("canonicalization_rules", ())) != CANONICALIZATION_RULES:
        errors.append("Dry-run summary hash canonicalization_rules changed unexpectedly.")
    overlap = set(payload.get("allowed_canonical_summary_fields", ())) & set(
        payload.get("excluded_hash_input_fields", ())
    )
    if overlap:
        errors.append(
            "Dry-run summary hash allowed and excluded fields must not overlap: "
            + ", ".join(sorted(overlap))
            + "."
        )
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_contract_terms = (
        set(ALLOWED_CANONICAL_SUMMARY_FIELDS)
        | set(EXCLUDED_HASH_INPUT_FIELDS)
        | set(CANONICALIZATION_RULES)
        | {PRIVATE_OUTPUT_ROOT, RECOMMENDED_NEXT_STEP, SCHEMA_VERSION, MILESTONE, "contract_only"}
    )
    for value in _iter_string_values(payload):
        if value in expected_contract_terms:
            continue
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


def _doc_link_errors() -> list[str]:
    errors: list[str] = []
    fixture_ref = str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/")
    checker_ref = "scripts/check_dry_run_summary_hash_contract.py"
    doc_ref = "docs/extraction-indexing-dry-run-summary-hash-contract.md"

    for doc_path in (DOC_PATH, ADR_PATH, HASH_DECISION_DOC, INPUT_CONTRACT_DOC, INDEX_CONTRACT_DOC):
        if not doc_path.exists():
            errors.append(f"Missing dry-run summary hash doc: {_display_path(doc_path)}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for required in (fixture_ref, checker_ref, doc_ref):
            if required not in text:
                errors.append(f"{_display_path(doc_path)} must point to {required}.")

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (DOC_PATH, ADR_PATH, HASH_DECISION_DOC, INPUT_CONTRACT_DOC, INDEX_CONTRACT_DOC)
        if path.exists()
    )
    for phrase in (
        "hash implementation is approved",
        "file content hashing is approved",
        "path string hashing is approved",
        "filename hashing is approved",
        "private index construction is approved",
        "real extraction is approved",
        "current-line capture is approved",
        "real text capture is approved",
        "automatic game install scanning is approved",
    ):
        if phrase in combined:
            errors.append(f"Dry-run summary hash docs must not say {phrase!r}.")
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
