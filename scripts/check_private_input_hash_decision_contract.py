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


FIXTURE_PATH = ROOT / "tests/fixtures/private_input_hash_decision.synthetic.json"
DOC_PATH = ROOT / "docs/extraction-indexing-private-input-hash-contract.md"
ADR_PATH = ROOT / "docs/adr/0011-real-extraction-indexing-scope.md"
INPUT_CONTRACT_DOC = ROOT / "docs/extraction-indexing-private-input-adapter-contract.md"
INDEX_CONTRACT_DOC = ROOT / "docs/extraction-indexing-private-index-contract.md"
SCHEMA_VERSION = "private-input-hash-decision.v1"
MILESTONE = "5A.5"
RECOMMENDED_NEXT_STEP = "dry_run_summary_hash_contract"
PRIVATE_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/"

FORBIDDEN_PERMISSION_FIELDS = (
    "hash_implementation_allowed_next",
    "file_content_hashing_allowed",
    "path_string_hashing_allowed",
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
    "verbose_path_summary_hashing_allowed",
    "tracked_hash_output_allowed",
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


class PrivateInputHashDecisionContractError(RuntimeError):
    """Raised when the private input hash decision contract is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Milestone 5A.5 private input hash decision contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_private_input_hash_decision_contract_errors()
    if errors:
        if args.quiet:
            print("Private input hash decision contract check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("Private input hash decision contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "private-input-hash-decision-contract-check.v1",
                    "fixture": str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/"),
                    "milestone": MILESTONE,
                    "hash_implementation_allowed_next": False,
                    "file_content_hashing_allowed": False,
                    "path_string_hashing_allowed": False,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_private_input_hash_decision_contract_safe() -> None:
    errors = collect_private_input_hash_decision_contract_errors()
    if errors:
        raise PrivateInputHashDecisionContractError("; ".join(errors))


def collect_private_input_hash_decision_contract_errors(
    path: Path = FIXTURE_PATH,
) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load private input hash decision fixture: {exc}"]

    if not isinstance(payload, dict):
        return ["Private input hash decision fixture must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_root_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_link_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Private input hash decision schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("milestone") != MILESTONE:
        errors.append(f"Private input hash decision milestone must be {MILESTONE!r}.")
    if payload.get("decision_status") != "contract_only":
        errors.append("Private input hash decision_status must be 'contract_only'.")
    if payload.get("dry_run_summary_hashing_allowed_next") != "decision_pending":
        errors.append(
            "Private input hash decision must keep "
            "dry_run_summary_hashing_allowed_next='decision_pending'."
        )
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(
            f"Private input hash decision recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}."
        )
    if payload.get("tracked_artifacts_redacted") is not True:
        errors.append("Private input hash decision must set tracked_artifacts_redacted=true.")

    for field in FORBIDDEN_PERMISSION_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Private input hash decision field {field!r} must be a boolean.")
        elif payload.get(field) is not False:
            errors.append(f"Private input hash decision fixture must keep {field}=false.")
    return errors


def _root_errors(payload: dict[str, Any]) -> list[str]:
    root = payload.get("private_output_root")
    if root != PRIVATE_OUTPUT_ROOT:
        return [f"Private input hash decision private_output_root must be {PRIVATE_OUTPUT_ROOT!r}."]

    errors: list[str] = []
    normalized = root.replace("\\", "/")
    if normalized != root:
        errors.append("Private input hash decision private_output_root must use forward slashes.")
    if not normalized.startswith("workspace/"):
        errors.append("Private input hash decision private_output_root must stay under workspace/.")
    if not normalized.endswith("/"):
        errors.append("Private input hash decision private_output_root must end with '/'.")
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        errors.append("Private input hash decision private_output_root must not contain '..'.")
    if normalized.startswith("/") or WINDOWS_ABSOLUTE_PATH_PATTERN.match(normalized):
        errors.append("Private input hash decision private_output_root must be repo-relative.")
    if "extraction-indexing" not in normalized:
        errors.append(
            "Private input hash decision private_output_root must be scoped to extraction-indexing."
        )
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
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


def _doc_link_errors() -> list[str]:
    errors: list[str] = []
    fixture_ref = str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/")
    checker_ref = "scripts/check_private_input_hash_decision_contract.py"
    doc_ref = "docs/extraction-indexing-private-input-hash-contract.md"

    for doc_path in (DOC_PATH, ADR_PATH, INPUT_CONTRACT_DOC, INDEX_CONTRACT_DOC):
        if not doc_path.exists():
            errors.append(f"Missing private input hash contract doc: {_display_path(doc_path)}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for required in (fixture_ref, checker_ref, doc_ref):
            if required not in text:
                errors.append(f"{_display_path(doc_path)} must point to {required}.")

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (DOC_PATH, ADR_PATH, INPUT_CONTRACT_DOC, INDEX_CONTRACT_DOC)
        if path.exists()
    )
    for phrase in (
        "hash implementation is approved",
        "file content hashing is approved",
        "path string hashing is approved",
        "private index construction is approved",
        "real extraction is approved",
        "current-line capture is approved",
        "real text capture is approved",
        "automatic game install scanning is approved",
    ):
        if phrase in combined:
            errors.append(f"Private input hash docs must not say {phrase!r}.")
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
