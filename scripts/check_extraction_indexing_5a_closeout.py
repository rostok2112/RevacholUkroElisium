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


FIXTURE_PATH = ROOT / "tests/fixtures/extraction_indexing_5a_closeout.synthetic.json"
DOC_PATH = ROOT / "docs/extraction-indexing-milestone-5a-closeout.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
SCHEMA_VERSION = "extraction-indexing-5a-closeout.v1"
MILESTONE = "5A"
RECOMMENDED_NEXT_STEP = "user_selected_private_input_adapter_review_or_milestone_6_planning"

COMPLETED_SAFE_FIELDS = (
    "scope_contract_done",
    "synthetic_indexer_done",
    "private_input_contract_done",
    "private_input_dry_run_done",
    "private_input_review_done",
    "dry_run_summary_hash_done",
    "dry_run_summary_hash_review_done",
    "private_index_construction_contract_done",
    "private_index_builder_dry_run_done",
    "tracked_evidence_redacted",
)

FORBIDDEN_CAPABILITY_FIELDS = (
    "real_extraction_done",
    "real_game_files_read",
    "automatic_game_install_scanning_done",
    "bepinex_logs_read",
    "current_line_capture_done",
    "ui_text_reading_done",
    "unity_scanning_done",
    "hooks_done",
    "ocr_done",
    "screenshots_read",
    "save_files_read",
    "decompiled_code_work_done",
    "provider_execution_done",
    "companion_contract_change_done",
    "real_extracted_text_committed",
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

FORBIDDEN_VALUE_MARKERS = (
    "real extraction approved",
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
    "bepinex",
    "savegame",
    ".sav",
    "decompiled",
    "dnspy",
    "ilspy",
)


class ExtractionIndexing5ACloseoutError(RuntimeError):
    """Raised when the Milestone 5A closeout fixture is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Milestone 5A extraction/indexing closeout evidence fixture."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_extraction_indexing_5a_closeout_errors()
    if errors:
        if args.quiet:
            print("Extraction/indexing Milestone 5A closeout check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("Extraction/indexing Milestone 5A closeout check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "extraction-indexing-5a-closeout-check.v1",
                    "fixture": str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/"),
                    "milestone": MILESTONE,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                    "real_extraction_done": False,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_extraction_indexing_5a_closeout_safe() -> None:
    errors = collect_extraction_indexing_5a_closeout_errors()
    if errors:
        raise ExtractionIndexing5ACloseoutError("; ".join(errors))


def collect_extraction_indexing_5a_closeout_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load extraction/indexing Milestone 5A closeout fixture: {exc}"]

    if not isinstance(payload, dict):
        return ["Extraction/indexing Milestone 5A closeout fixture must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_link_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Milestone 5A closeout schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("milestone") != MILESTONE:
        errors.append(f"Milestone 5A closeout milestone must be {MILESTONE!r}.")
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(f"Milestone 5A closeout next step must be {RECOMMENDED_NEXT_STEP!r}.")

    for field in COMPLETED_SAFE_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Milestone 5A closeout field {field!r} must be a boolean.")
        elif payload.get(field) is not True:
            errors.append(f"Milestone 5A closeout fixture must set {field}=true.")

    for field in FORBIDDEN_CAPABILITY_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Milestone 5A closeout field {field!r} must be a boolean.")
        elif payload.get(field) is not False:
            errors.append(f"Milestone 5A closeout fixture must keep {field}=false.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_terms = {SCHEMA_VERSION, MILESTONE, RECOMMENDED_NEXT_STEP}
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
    checker_ref = "scripts/check_extraction_indexing_5a_closeout.py"
    doc_ref = "docs/extraction-indexing-milestone-5a-closeout.md"

    for doc_path in (DOC_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
        if not doc_path.exists():
            errors.append(f"Missing Milestone 5A closeout doc: {_display_path(doc_path)}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for required in (fixture_ref, checker_ref, doc_ref):
            if required not in text:
                errors.append(f"{_display_path(doc_path)} must point to {required}.")

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (DOC_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH)
        if path.exists()
    )
    for phrase in (
        "real extraction is approved",
        "game file reads are approved",
        "current-line capture is approved",
        "ui text reading is approved",
        "unity scanning is approved",
        "ocr is approved",
        "provider execution is approved",
        "companion contract change is approved",
    ):
        if phrase in combined:
            errors.append(f"Milestone 5A closeout docs must not say {phrase!r}.")
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
