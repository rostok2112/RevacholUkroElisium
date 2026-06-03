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


FIXTURE_PATH = ROOT / "tests/fixtures/m2_local_import_final_approval_scope.synthetic.json"
DOC_PATH = ROOT / "docs/m2-local-import-final-approval-contract.md"
ADR_PATH = ROOT / "docs/adr/0012-m2-local-extraction-import-scope.md"
INTEGRITY_DOC_PATH = ROOT / "docs/m2-explicit-local-import-context-edge-integrity-contract.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
GITIGNORE_PATH = ROOT / ".gitignore"
SCHEMA_VERSION = "m2-local-import-final-approval-scope.v1"
ROADMAP_MILESTONE = "M2"
FUTURE_PROFILE_SCHEMA_VERSION = "m2-local-private-export.v1"
RECOMMENDED_NEXT_STEP = "m2_local_import_implementation"
ALLOWED_PRIVATE_INPUT_ROOTS = ("workspace/local-private/extraction-indexing/input/",)
ALLOWED_PRIVATE_OUTPUT_ROOTS = ("workspace/local-private/extraction-indexing/import/db/",)
ALLOWED_NEXT_IMPORT_INPUTS = (
    "top_level_envelope",
    "records",
    "context_edges",
    "metadata",
)
ALLOWED_PRIVATE_IMPORT_FIELDS = (
    "schema_version",
    "source_kind",
    "records",
    "context_edges",
    "metadata",
)
ALLOWED_PUBLIC_SUMMARY_FIELDS = (
    "input_exists",
    "input_kind",
    "json_object_decoded",
    "profile_schema_version_matches",
    "records_count",
    "context_edges_count",
    "import_status",
    "blocker_categories",
)
REQUIRED_TRUE_FIELDS = (
    "explicit_user_selected_private_export_required",
    "single_explicit_file_required",
    "local_import_implementation_allowed_next",
    "real_local_input_read_allowed_next",
    "private_content_parsing_allowed_next",
    "private_db_output_allowed_next",
    "contract_notes_redacted",
)
INCOMPLETE_M2_FIELDS = (
    "m2_import_locally_extracted_db_done",
    "m2_line_index_done",
    "m2_context_graph_done",
)
FORBIDDEN_PERMISSION_FIELDS = (
    "line_index_construction_allowed_next",
    "context_graph_construction_allowed_next",
    "retrieval_bucket_mapping_allowed_next",
    "directory_inputs_allowed",
    "external_absolute_input_paths_allowed",
    "recursive_discovery_allowed",
    "automatic_game_install_scanning_allowed",
    "arbitrary_drive_scanning_allowed",
    "game_file_reads_allowed",
    "bepinex_log_reads_allowed",
    "screenshots_allowed",
    "ocr_allowed",
    "save_file_reads_allowed",
    "decompiled_code_allowed",
    "current_line_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "real_extracted_text_commit_allowed",
    "raw_extracted_payload_commit_allowed",
    "generated_private_db_commit_allowed",
    "generated_index_commit_allowed",
    "private_paths_commit_allowed",
    "public_stdout_private_values_allowed",
    "public_review_private_values_allowed",
    "content_hashing_allowed",
    "path_string_hashing_allowed",
    "filename_hashing_allowed",
    "id_hashing_allowed",
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
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:")
FORBIDDEN_VALUE_MARKERS = (
    "line index construction approved",
    "context graph construction approved",
    "retrieval bucket mapping approved",
    "directory input approved",
    "recursive discovery approved",
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
    "commit extracted text approved",
    "commit private db approved",
    "commit private paths approved",
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
    parser = argparse.ArgumentParser(
        description="Validate the M2 local import final approval contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m2_local_import_final_approval_contract_errors()
    if errors:
        if args.quiet:
            print("M2 local import final approval contract check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M2 local import final approval contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m2-local-import-final-approval-contract-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "local_import_implementation_allowed_next": True,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m2_local_import_final_approval_contract_errors(
    path: Path = FIXTURE_PATH,
) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 local import final approval fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 local import final approval fixture must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_root_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_scalars = {
        "schema_version": SCHEMA_VERSION,
        "roadmap_milestone": ROADMAP_MILESTONE,
        "scope_status": "final_approval_contract",
        "future_profile_schema_version": FUTURE_PROFILE_SCHEMA_VERSION,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "required_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M2 final approval {field} must be {expected!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M2 final approval fixture must set {field}=true.")
    for field in (*INCOMPLETE_M2_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
        if payload.get(field) is not False:
            errors.append(f"M2 final approval fixture must keep {field}=false.")
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_next_import_inputs"),
            expected=ALLOWED_NEXT_IMPORT_INPUTS,
            label="allowed_next_import_inputs",
        )
    )
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_private_import_fields"),
            expected=ALLOWED_PRIVATE_IMPORT_FIELDS,
            label="allowed_private_import_fields",
        )
    )
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_public_summary_fields"),
            expected=ALLOWED_PUBLIC_SUMMARY_FIELDS,
            label="allowed_public_summary_fields",
        )
    )
    return errors


def _root_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(
        _validate_roots(
            payload.get("allowed_private_input_roots"),
            expected=ALLOWED_PRIVATE_INPUT_ROOTS,
            label="input",
        )
    )
    errors.extend(
        _validate_roots(
            payload.get("allowed_private_output_roots"),
            expected=ALLOWED_PRIVATE_OUTPUT_ROOTS,
            label="output",
        )
    )
    if "workspace/" not in GITIGNORE_PATH.read_text(encoding="utf-8"):
        errors.append(".gitignore must keep workspace/ ignored for private M2 import artifacts.")
    return errors


def _exact_string_list_errors(value: Any, *, expected: tuple[str, ...], label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return [f"M2 final approval {label} must be a list of strings."]
    if tuple(value) != expected:
        return [f"M2 final approval {label} must exactly match: {', '.join(expected)}."]
    return []


def _validate_roots(value: Any, *, expected: tuple[str, ...], label: str) -> list[str]:
    errors = _exact_string_list_errors(value, expected=expected, label=f"private {label} roots")
    if errors:
        return errors
    for root in value:
        normalized = root.replace("\\", "/")
        if normalized != root:
            errors.append(f"M2 final approval private {label} root must use forward slashes.")
        if not normalized.startswith("workspace/local-private/extraction-indexing/"):
            errors.append(f"M2 final approval private {label} root must stay ignored/private.")
        if not normalized.endswith("/"):
            errors.append(f"M2 final approval private {label} root must end with '/'.")
        if ".." in Path(normalized).parts or normalized.startswith("../"):
            errors.append(f"M2 final approval private {label} root must not contain '..'.")
        if normalized.startswith("/") or WINDOWS_ABSOLUTE_PATH_PATTERN.match(normalized):
            errors.append(f"M2 final approval private {label} root must be repo-relative.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        FUTURE_PROFILE_SCHEMA_VERSION,
        RECOMMENDED_NEXT_STEP,
        "final_approval_contract",
        *ALLOWED_PRIVATE_INPUT_ROOTS,
        *ALLOWED_PRIVATE_OUTPUT_ROOTS,
        *ALLOWED_NEXT_IMPORT_INPUTS,
        *ALLOWED_PRIVATE_IMPORT_FIELDS,
        *ALLOWED_PUBLIC_SUMMARY_FIELDS,
    }
    for value in _iter_string_values(payload):
        if value in expected_values:
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


def _doc_errors() -> list[str]:
    errors: list[str] = []
    required_refs = (
        "docs/m2-local-import-final-approval-contract.md",
        "tests/fixtures/m2_local_import_final_approval_scope.synthetic.json",
        "scripts/check_m2_local_import_final_approval_contract.py",
    )
    for path in (
        DOC_PATH,
        ADR_PATH,
        INTEGRITY_DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
    ):
        if not path.exists():
            errors.append(f"Missing M2 final approval doc: {_display_path(path)}.")
            continue
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for required in required_refs:
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
