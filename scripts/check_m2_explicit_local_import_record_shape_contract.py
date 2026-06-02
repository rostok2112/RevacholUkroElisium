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


FIXTURE_PATH = ROOT / "tests/fixtures/m2_explicit_local_import_record_shape_scope.synthetic.json"
DOC_PATH = ROOT / "docs/m2-explicit-local-import-record-shape-contract.md"
COMPATIBILITY_DOC_PATH = ROOT / "docs/m2-explicit-local-import-schema-compatibility-contract.md"
ADR_PATH = ROOT / "docs/adr/0012-m2-local-extraction-import-scope.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
GITIGNORE_PATH = ROOT / ".gitignore"
SCHEMA_VERSION = "m2-explicit-local-import-record-shape-scope.v1"
ROADMAP_MILESTONE = "M2"
FUTURE_PROFILE_SCHEMA_VERSION = "m2-local-private-export.v1"
RECOMMENDED_NEXT_STEP = "m2_explicit_local_import_record_shape_dry_run"
ALLOWED_PRIVATE_INPUT_ROOTS = ("workspace/local-private/extraction-indexing/input/",)
ALLOWED_PRIVATE_OUTPUT_ROOTS = ("workspace/local-private/extraction-indexing/import/record-shape/",)
ALLOWED_RECORD_FIELDS = (
    "record_id",
    "line_id",
    "conversation_id",
    "speaker_id",
    "speaker_label",
    "context_placeholder",
    "source_text",
    "context_tags",
    "redacted_metadata",
)
ALLOWED_RECORD_TYPES = {
    "record_id": "string",
    "line_id": "string",
    "conversation_id": "string",
    "speaker_id": "string",
    "speaker_label": "string",
    "context_placeholder": "string",
    "source_text": "string",
    "context_tags": "array",
    "redacted_metadata": "object",
}
ALLOWED_FUTURE_SUMMARY_FIELDS = (
    "input_exists",
    "input_kind",
    "envelope_compatible",
    "records_array_present",
    "records_count",
    "records_inspected_count",
    "compatible_record_count",
    "incompatible_record_count",
    "all_record_shapes_compatible",
    "record_shape_status",
    "blocker_categories",
)
REQUIRED_TRUE_FIELDS = (
    "explicit_user_selected_private_export_required",
    "single_explicit_file_required",
    "schema_compatibility_review_required",
    "contract_notes_redacted",
)
INCOMPLETE_M2_FIELDS = (
    "m2_import_locally_extracted_db_done",
    "m2_line_index_done",
    "m2_context_graph_done",
)
FORBIDDEN_PERMISSION_FIELDS = (
    "implementation_allowed_next",
    "private_export_reopen_allowed_in_contract",
    "json_decoding_allowed_in_contract",
    "record_shape_inspection_allowed_in_contract",
    "record_value_inspection_allowed",
    "record_value_emission_allowed",
    "record_value_logging_allowed",
    "record_value_comparison_allowed",
    "record_value_normalization_allowed",
    "context_tags_content_traversal_allowed",
    "redacted_metadata_content_traversal_allowed",
    "context_edge_inspection_allowed",
    "metadata_content_inspection_allowed",
    "source_text_emission_allowed",
    "content_hashing_allowed",
    "path_string_hashing_allowed",
    "filename_hashing_allowed",
    "real_db_import_allowed_next",
    "line_index_construction_allowed_next",
    "context_graph_construction_allowed_next",
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
    "generated_index_commit_allowed",
    "private_paths_commit_allowed",
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
    "record inspection approved",
    "record value emission approved",
    "record value logging approved",
    "record value comparison approved",
    "record value normalization approved",
    "context tags traversal approved",
    "redacted metadata traversal approved",
    "context edge inspection approved",
    "source text emission approved",
    "metadata content inspection approved",
    "real db import approved",
    "line index construction approved",
    "context graph construction approved",
    "recursive discovery approved",
    "game file reads approved",
    "steam scanning approved",
    "automatic game install scanning approved",
    "bepinex log reads approved",
    "current-line capture approved",
    "ui text reading approved",
    "unity scanning approved",
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


class M2ExplicitLocalImportRecordShapeContractError(RuntimeError):
    """Raised when the M2 record-shape contract is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the M2 explicit local-import record-shape contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)
    errors = collect_m2_explicit_local_import_record_shape_contract_errors()
    if errors:
        if args.quiet:
            print("M2 explicit local-import record-shape contract check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M2 explicit local-import record-shape contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m2-explicit-local-import-record-shape-contract-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "implementation_allowed_next": False,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m2_explicit_local_import_record_shape_contract_errors(
    path: Path = FIXTURE_PATH,
) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 record-shape fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 record-shape fixture must be a JSON object."]
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
        "scope_status": "contract_only",
        "future_profile_schema_version": FUTURE_PROFILE_SCHEMA_VERSION,
        "inspection_depth": "all_record_objects_top_level_shape_only",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "required_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M2 record-shape {field} must be {expected!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M2 record-shape fixture must set {field}=true.")
    for field in (*INCOMPLETE_M2_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
        if payload.get(field) is not False:
            errors.append(f"M2 record-shape fixture must keep {field}=false.")
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_record_top_level_fields"),
            expected=ALLOWED_RECORD_FIELDS,
            label="allowed_record_top_level_fields",
        )
    )
    if payload.get("allowed_record_top_level_types") != ALLOWED_RECORD_TYPES:
        errors.append("M2 record-shape allowed_record_top_level_types must match exactly.")
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_future_summary_fields"),
            expected=ALLOWED_FUTURE_SUMMARY_FIELDS,
            label="allowed_future_summary_fields",
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
        errors.append(".gitignore must keep workspace/ ignored for private M2 record-shape data.")
    return errors


def _exact_string_list_errors(value: Any, *, expected: tuple[str, ...], label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return [f"M2 record-shape {label} must be a list of strings."]
    if tuple(value) != expected:
        return [f"M2 record-shape {label} must exactly match: {', '.join(expected)}."]
    return []


def _validate_roots(value: Any, *, expected: tuple[str, ...], label: str) -> list[str]:
    errors = _exact_string_list_errors(value, expected=expected, label=f"private {label} roots")
    if errors:
        return errors
    for root in value:
        normalized = root.replace("\\", "/")
        if normalized != root:
            errors.append(f"M2 record-shape private {label} root must use forward slashes.")
        if not normalized.startswith("workspace/local-private/extraction-indexing/"):
            errors.append(f"M2 record-shape private {label} root must stay ignored/private.")
        if not normalized.endswith("/"):
            errors.append(f"M2 record-shape private {label} root must end with '/'.")
        if ".." in Path(normalized).parts or normalized.startswith("../"):
            errors.append(f"M2 record-shape private {label} root must not contain '..'.")
        if normalized.startswith("/") or WINDOWS_ABSOLUTE_PATH_PATTERN.match(normalized):
            errors.append(f"M2 record-shape private {label} root must be repo-relative.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        FUTURE_PROFILE_SCHEMA_VERSION,
        RECOMMENDED_NEXT_STEP,
        "contract_only",
        "all_record_objects_top_level_shape_only",
        *ALLOWED_PRIVATE_INPUT_ROOTS,
        *ALLOWED_PRIVATE_OUTPUT_ROOTS,
        *ALLOWED_RECORD_FIELDS,
        *ALLOWED_RECORD_TYPES.values(),
        *ALLOWED_FUTURE_SUMMARY_FIELDS,
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
        "docs/m2-explicit-local-import-record-shape-contract.md",
        "tests/fixtures/m2_explicit_local_import_record_shape_scope.synthetic.json",
        "scripts/check_m2_explicit_local_import_record_shape_contract.py",
    )
    for path in (
        DOC_PATH,
        COMPATIBILITY_DOC_PATH,
        ADR_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
    ):
        if not path.exists():
            errors.append(f"Missing M2 record-shape doc: {_display_path(path)}.")
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
