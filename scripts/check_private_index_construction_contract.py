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


FIXTURE_PATH = ROOT / "tests/fixtures/private_index_construction_contract.synthetic.json"
DOC_PATH = ROOT / "docs/extraction-indexing-private-index-construction-contract.md"
ADR_PATH = ROOT / "docs/adr/0011-real-extraction-indexing-scope.md"
PRIVATE_INDEX_DOC = ROOT / "docs/extraction-indexing-private-index-contract.md"
HASH_CONTRACT_DOC = ROOT / "docs/extraction-indexing-dry-run-summary-hash-contract.md"
INPUT_CONTRACT_DOC = ROOT / "docs/extraction-indexing-private-input-adapter-contract.md"
SCHEMA_VERSION = "private-index-construction-contract.v1"
MILESTONE = "5A.9"
RECOMMENDED_NEXT_STEP = "private_index_builder_dry_run"
ALLOWED_PRIVATE_OUTPUT_ROOTS = ("workspace/local-private/extraction-indexing/index/",)

FORBIDDEN_PERMISSION_FIELDS = (
    "private_index_builder_allowed_next",
    "real_extraction_allowed",
    "file_contents_allowed",
    "real_game_text_allowed",
    "path_strings_allowed",
    "filenames_allowed",
    "raw_payloads_allowed",
    "logs_allowed",
    "screenshots_allowed",
    "ocr_allowed",
    "save_files_allowed",
    "decompiled_code_allowed",
    "current_line_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "provider_execution_allowed",
    "provider_payloads_allowed",
    "companion_contract_change_allowed",
    "companion_runtime_data_allowed",
    "automatic_game_install_scanning_allowed",
    "bepinex_log_reads_allowed",
    "real_game_text_commit_allowed",
    "file_content_hashing_allowed",
    "path_string_hashing_allowed",
    "filename_hashing_allowed",
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
    "private index builder approved",
    "private index construction approved",
    "private index implementation approved",
    "real extraction approved",
    "real extraction from game files approved",
    "file contents approved",
    "file content reads approved",
    "file content hashing approved",
    "path string hashing approved",
    "filename hashing approved",
    "current-line capture approved",
    "current line capture approved",
    "real text capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "harmony patch approved",
    "hook implementation approved",
    "ocr approved",
    "automatic game install scanning approved",
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


class PrivateIndexConstructionContractError(RuntimeError):
    """Raised when the private index construction contract is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Milestone 5A.9 private index construction contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_private_index_construction_contract_errors()
    if errors:
        if args.quiet:
            print("Private index construction contract check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("Private index construction contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "private-index-construction-contract-check.v1",
                    "fixture": str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/"),
                    "milestone": MILESTONE,
                    "private_index_builder_allowed_next": False,
                    "private_index_construction_allowed_next": "contract_defined_only",
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_private_index_construction_contract_safe() -> None:
    errors = collect_private_index_construction_contract_errors()
    if errors:
        raise PrivateIndexConstructionContractError("; ".join(errors))


def collect_private_index_construction_contract_errors(
    path: Path = FIXTURE_PATH,
) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load private index construction contract fixture: {exc}"]

    if not isinstance(payload, dict):
        return ["Private index construction contract fixture must be a JSON object."]

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
        errors.append(f"Private index construction schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("milestone") != MILESTONE:
        errors.append(f"Private index construction milestone must be {MILESTONE!r}.")
    if payload.get("decision_status") != "contract_only":
        errors.append("Private index construction decision_status must be 'contract_only'.")
    if payload.get("private_index_construction_allowed_next") != "contract_defined_only":
        errors.append(
            "Private index construction must keep "
            "private_index_construction_allowed_next='contract_defined_only'."
        )
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(
            f"Private index construction recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}."
        )
    if payload.get("tracked_artifacts_redacted") is not True:
        errors.append("Private index construction must set tracked_artifacts_redacted=true.")

    for field in FORBIDDEN_PERMISSION_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Private index construction field {field!r} must be a boolean.")
        elif payload.get(field) is not False:
            errors.append(f"Private index construction fixture must keep {field}=false.")
    return errors


def _root_errors(payload: dict[str, Any]) -> list[str]:
    roots = payload.get("allowed_private_output_roots")
    if tuple(roots or ()) != ALLOWED_PRIVATE_OUTPUT_ROOTS:
        return [
            "Private index construction allowed_private_output_roots must be "
            f"{list(ALLOWED_PRIVATE_OUTPUT_ROOTS)!r}."
        ]

    errors: list[str] = []
    for root in roots:
        normalized = root.replace("\\", "/")
        if normalized != root:
            errors.append("Private index construction roots must use forward slashes.")
        if not normalized.startswith("workspace/"):
            errors.append("Private index construction roots must stay under workspace/.")
        if not normalized.endswith("/"):
            errors.append("Private index construction roots must end with '/'.")
        if ".." in Path(normalized).parts or normalized.startswith("../"):
            errors.append("Private index construction roots must not contain '..'.")
        if normalized.startswith("/") or WINDOWS_ABSOLUTE_PATH_PATTERN.match(normalized):
            errors.append("Private index construction roots must be repo-relative.")
        if "workspace/local-private/extraction-indexing/index/" != normalized:
            errors.append(
                "Private index construction roots must stay under "
                "workspace/local-private/extraction-indexing/index/."
            )
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_terms = {
        SCHEMA_VERSION,
        MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "contract_only",
        "contract_defined_only",
        *ALLOWED_PRIVATE_OUTPUT_ROOTS,
    }
    for value in _iter_string_values(payload):
        if value in expected_terms:
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
    checker_ref = "scripts/check_private_index_construction_contract.py"
    doc_ref = "docs/extraction-indexing-private-index-construction-contract.md"

    for doc_path in (DOC_PATH, ADR_PATH, PRIVATE_INDEX_DOC, HASH_CONTRACT_DOC, INPUT_CONTRACT_DOC):
        if not doc_path.exists():
            errors.append(f"Missing private index construction doc: {_display_path(doc_path)}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for required in (fixture_ref, checker_ref, doc_ref):
            if required not in text:
                errors.append(f"{_display_path(doc_path)} must point to {required}.")

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (DOC_PATH, ADR_PATH, PRIVATE_INDEX_DOC, HASH_CONTRACT_DOC, INPUT_CONTRACT_DOC)
        if path.exists()
    )
    for phrase in (
        "private index builder is approved",
        "private index implementation is approved",
        "real extraction is approved",
        "file contents are approved",
        "file content hashing is approved",
        "path string hashing is approved",
        "filename hashing is approved",
        "current-line capture is approved",
        "ui text reading is approved",
        "unity scanning is approved",
        "ocr is approved",
        "provider execution is approved",
        "companion contract change is approved",
    ):
        if phrase in combined:
            errors.append(f"Private index construction docs must not say {phrase!r}.")
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
