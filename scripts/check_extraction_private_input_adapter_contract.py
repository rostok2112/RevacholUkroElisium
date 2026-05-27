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


FIXTURE_PATH = ROOT / "tests/fixtures/extraction_private_input_adapter_scope.synthetic.json"
DOC_PATH = ROOT / "docs/extraction-indexing-private-input-adapter-contract.md"
ADR_PATH = ROOT / "docs/adr/0011-real-extraction-indexing-scope.md"
INDEX_CONTRACT_DOC = ROOT / "docs/extraction-indexing-private-index-contract.md"
GITIGNORE_PATH = ROOT / ".gitignore"
SCHEMA_VERSION = "extraction-private-input-adapter-scope.v1"
MILESTONE = "5A.2"
RECOMMENDED_NEXT_STEP = "private_input_adapter_dry_run"
ALLOWED_PRIVATE_INPUT_ROOTS = ("workspace/local-private/extraction-indexing/input/",)
ALLOWED_PRIVATE_OUTPUT_ROOTS = ("workspace/local-private/extraction-indexing/",)

REQUIRED_TRUE_FIELDS = (
    "explicit_user_selected_input_required",
    "dry_run_metadata_summary_default",
    "contract_notes_redacted",
)

FORBIDDEN_PERMISSION_FIELDS = (
    "implementation_allowed_next",
    "external_absolute_input_paths_allowed",
    "automatic_game_install_scanning_allowed",
    "arbitrary_drive_scan_allowed",
    "recursive_drive_scan_allowed",
    "bepinex_log_reads_allowed",
    "game_log_reads_allowed",
    "save_file_parsing_allowed",
    "real_game_text_commit_allowed",
    "raw_localization_dump_commit_allowed",
    "raw_extracted_payload_commit_allowed",
    "screenshots_allowed",
    "ocr_allowed",
    "hooks_allowed",
    "unity_scanning_allowed",
    "current_line_capture_allowed",
    "ui_text_reading_allowed",
    "decompiled_code_allowed",
    "companion_contract_change_allowed",
    "real_provider_execution_allowed",
    "production_overlay_shell_allowed",
)

REQUIRED_SUMMARY_FIELDS = (
    "input_exists",
    "input_kind",
    "file_count",
    "byte_count",
    "hash_summary",
    "schema_status",
    "blocker_categories",
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
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:")

FORBIDDEN_STRING_MARKERS = (
    "current-line capture approved",
    "current line capture approved",
    "real text capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "hook implementation approved",
    "harmony patch approved",
    "ocr approved",
    "automatic game install scanning approved",
    "arbitrary drive scan approved",
    "real extraction approved",
    "real extraction from game files approved",
    "bepinex log read approved",
    "save parsing approved",
    "real provider execution approved",
    "companion contract change approved",
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


class ExtractionPrivateInputAdapterContractError(RuntimeError):
    """Raised when the private input adapter contract is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the Milestone 5A.2 private input adapter contract fixture."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_extraction_private_input_adapter_contract_errors()
    if errors:
        if args.quiet:
            print("Extraction private input adapter contract check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("Extraction private input adapter contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "extraction-private-input-adapter-contract-check.v1",
                    "fixture": str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/"),
                    "milestone": MILESTONE,
                    "implementation_allowed_next": False,
                    "explicit_user_selected_input_required": True,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_extraction_private_input_adapter_contract_safe() -> None:
    errors = collect_extraction_private_input_adapter_contract_errors()
    if errors:
        raise ExtractionPrivateInputAdapterContractError("; ".join(errors))


def collect_extraction_private_input_adapter_contract_errors(
    path: Path = FIXTURE_PATH,
) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load private input adapter contract fixture: {exc}"]

    if not isinstance(payload, dict):
        return ["Private input adapter contract fixture must be a JSON object."]

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
        errors.append(f"Private input adapter schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("milestone") != MILESTONE:
        errors.append(f"Private input adapter milestone must be {MILESTONE!r}.")
    if payload.get("scope_status") != "contract_only":
        errors.append("Private input adapter scope_status must be 'contract_only'.")
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(
            f"Private input adapter recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}."
        )
    if payload.get("required_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(
            f"Private input adapter required_next_step must be {RECOMMENDED_NEXT_STEP!r}."
        )

    for field in REQUIRED_TRUE_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Private input adapter field {field!r} must be a boolean.")
        elif payload.get(field) is not True:
            errors.append(f"Private input adapter fixture must set {field}=true.")

    for field in FORBIDDEN_PERMISSION_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Private input adapter field {field!r} must be a boolean.")
        elif payload.get(field) is not False:
            errors.append(f"Private input adapter fixture must keep {field}=false.")

    summary_fields = payload.get("allowed_tracked_summary_fields")
    if not isinstance(summary_fields, list) or not all(
        isinstance(item, str) for item in summary_fields
    ):
        errors.append("Private input adapter allowed_tracked_summary_fields must be strings.")
    else:
        if tuple(summary_fields) != REQUIRED_SUMMARY_FIELDS:
            errors.append(
                "Private input adapter allowed_tracked_summary_fields must exactly match: "
                + ", ".join(REQUIRED_SUMMARY_FIELDS)
                + "."
            )

    return errors


def _root_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(
        _validate_roots(
            payload.get("allowed_private_input_roots"),
            ALLOWED_PRIVATE_INPUT_ROOTS,
            label="input",
        )
    )
    errors.extend(
        _validate_roots(
            payload.get("allowed_private_output_roots"),
            ALLOWED_PRIVATE_OUTPUT_ROOTS,
            label="output",
        )
    )
    if "workspace/" not in GITIGNORE_PATH.read_text(encoding="utf-8"):
        errors.append(".gitignore must keep workspace/ ignored for private extraction artifacts.")
    return errors


def _validate_roots(value: Any, expected: tuple[str, ...], *, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return [f"Private input adapter allowed_private_{label}_roots must be strings."]

    if tuple(value) != expected:
        errors.append(
            f"Private input adapter allowed_private_{label}_roots must exactly match: "
            + ", ".join(expected)
            + "."
        )

    for root in value:
        normalized = root.replace("\\", "/")
        if normalized != root:
            errors.append(f"Private {label} root {root!r} must use forward slashes.")
        if not normalized.startswith("workspace/"):
            errors.append(f"Private {label} root {root!r} must stay under workspace/.")
        if not normalized.endswith("/"):
            errors.append(f"Private {label} root {root!r} must end with '/'.")
        if ".." in Path(normalized).parts or normalized.startswith("../"):
            errors.append(f"Private {label} root {root!r} must not contain '..'.")
        if normalized.startswith("/") or WINDOWS_ABSOLUTE_PATH_PATTERN.match(normalized):
            errors.append(f"Private {label} root {root!r} must be repo-relative, not absolute.")
        if "extraction-indexing" not in normalized:
            errors.append(f"Private {label} root {root!r} must be scoped to extraction-indexing.")
        if label == "input" and not normalized.endswith("/input/"):
            errors.append(f"Private input root {root!r} must end with /input/.")
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
        for marker in FORBIDDEN_STRING_MARKERS:
            if marker in lowered:
                errors.append(f"{relative}: contains forbidden marker {marker!r}.")
    return errors


def _doc_link_errors() -> list[str]:
    errors: list[str] = []
    fixture_ref = str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/")
    checker_ref = "scripts/check_extraction_private_input_adapter_contract.py"
    for doc_path in (DOC_PATH, ADR_PATH, INDEX_CONTRACT_DOC):
        if not doc_path.exists():
            errors.append(
                f"Missing private input adapter doc link target: {_display_path(doc_path)}."
            )
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        if fixture_ref not in text:
            errors.append(f"{_display_path(doc_path)} must point to {fixture_ref}.")
        if checker_ref not in text:
            errors.append(f"{_display_path(doc_path)} must point to {checker_ref}.")

    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (DOC_PATH, ADR_PATH, INDEX_CONTRACT_DOC)
        if path.exists()
    )
    for phrase in (
        "current-line capture is approved",
        "real text capture is approved",
        "automatic game install scanning is approved",
        "real extraction implementation is approved",
        "external absolute input paths are approved",
    ):
        if phrase in combined:
            errors.append(f"Private input adapter docs must not say {phrase!r}.")
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
