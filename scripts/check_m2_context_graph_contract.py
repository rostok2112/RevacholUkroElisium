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


FIXTURE_PATH = ROOT / "tests/fixtures/m2_context_graph_scope.synthetic.json"
DOC_PATH = ROOT / "docs/m2-context-graph-contract.md"
ADR_PATH = ROOT / "docs/adr/0012-m2-local-extraction-import-scope.md"
LINE_INDEX_DOC_PATH = ROOT / "docs/m2-line-index-contract.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
GITIGNORE_PATH = ROOT / ".gitignore"

SCHEMA_VERSION = "m2-context-graph-scope.v1"
ROADMAP_MILESTONE = "M2"
PRIVATE_DB_SCHEMA_VERSION = "m2-local-import-db.v1"
LINE_INDEX_SCHEMA_VERSION = "m2-line-index.v1"
CONTEXT_GRAPH_SCHEMA_VERSION = "m2-context-graph.v1"
RECOMMENDED_NEXT_STEP = "m2_context_graph_implementation"
ALLOWED_PRIVATE_INPUT_ROOTS = (
    "workspace/local-private/extraction-indexing/import/db/",
    "workspace/local-private/extraction-indexing/import/line-index/",
)
ALLOWED_PRIVATE_OUTPUT_ROOTS = (
    "workspace/local-private/extraction-indexing/import/context-graph/",
)
ALLOWED_NEXT_GRAPH_INPUTS = ("line_index_entries", "context_edges")
ALLOWED_PRIVATE_GRAPH_FIELDS = (
    "schema_version",
    "source_db_schema_version",
    "source_line_index_schema_version",
    "source_kind",
    "nodes",
    "edges",
    "metadata",
)
ALLOWED_PRIVATE_NODE_FIELDS = (
    "record_id",
    "line_id",
    "conversation_id",
    "speaker_id",
    "context_placeholder",
    "context_tags",
    "redacted_metadata",
)
ALLOWED_PRIVATE_EDGE_FIELDS = (
    "from_record_id",
    "to_record_id",
    "relation",
    "retrieval_bucket",
)
ALLOWED_RELATION_TO_BUCKET_MAPPINGS = (
    "previous_visible:visible_history",
    "nearby_branch:nearby_tree",
    "player_option:player_options",
)
ALLOWED_PUBLIC_SUMMARY_FIELDS = (
    "db_input_exists",
    "line_index_input_exists",
    "db_schema_version_matches",
    "line_index_schema_version_matches",
    "node_count",
    "edge_count",
    "context_graph_output_written",
    "context_graph_status",
    "blocker_categories",
)
REQUIRED_TRUE_FIELDS = (
    "local_import_implementation_available",
    "line_index_implementation_available",
    "context_graph_implementation_allowed_next",
    "explicit_user_selected_private_db_required",
    "explicit_user_selected_private_line_index_required",
    "single_explicit_db_file_required",
    "single_explicit_line_index_file_required",
    "m2_import_locally_extracted_db_implementation_available",
    "m2_line_index_implementation_available",
)
FORBIDDEN_FALSE_FIELDS = (
    "m2_context_graph_done",
    "directory_inputs_allowed",
    "external_absolute_input_paths_allowed",
    "recursive_discovery_allowed",
    "automatic_game_install_scanning_allowed",
    "arbitrary_drive_scanning_allowed",
    "arbitrary_future_branch_traversal_allowed",
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
    "generated_line_index_commit_allowed",
    "generated_context_graph_commit_allowed",
    "private_paths_commit_allowed",
    "public_stdout_private_values_allowed",
    "public_review_private_values_allowed",
    "source_text_duplication_in_graph_allowed",
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
    "game file reads approved",
    "steam scanning approved",
    "automatic game install scanning approved",
    "arbitrary future branch traversal approved",
    "directory input approved",
    "recursive discovery approved",
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
    "commit line index approved",
    "commit context graph approved",
    "commit private paths approved",
    "duplicate source text into graph",
    "source text duplication approved",
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
    parser = argparse.ArgumentParser(description="Validate the M2 context-graph contract.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m2_context_graph_contract_errors()
    if errors:
        if args.quiet:
            print("M2 context-graph contract check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M2 context-graph contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m2-context-graph-contract-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m2_context_graph_contract_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 context-graph fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 context-graph fixture must be a JSON object."]

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
        "scope_status": "context_graph_contract",
        "future_private_db_schema_version": PRIVATE_DB_SCHEMA_VERSION,
        "future_line_index_schema_version": LINE_INDEX_SCHEMA_VERSION,
        "future_context_graph_schema_version": CONTEXT_GRAPH_SCHEMA_VERSION,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "required_next_step": RECOMMENDED_NEXT_STEP,
        "default_spoiler_budget": "none",
        "retrieval_bucket_mapping_allowed_next": "context_graph_relation_mapping_only",
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M2 context-graph {field} must be {expected!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M2 context-graph fixture must set {field}=true.")
    for field in FORBIDDEN_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M2 context-graph fixture must keep {field}=false.")
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_next_graph_inputs"),
            expected=ALLOWED_NEXT_GRAPH_INPUTS,
            label="allowed_next_graph_inputs",
        )
    )
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_private_graph_fields"),
            expected=ALLOWED_PRIVATE_GRAPH_FIELDS,
            label="allowed_private_graph_fields",
        )
    )
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_private_node_fields"),
            expected=ALLOWED_PRIVATE_NODE_FIELDS,
            label="allowed_private_node_fields",
        )
    )
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_private_edge_fields"),
            expected=ALLOWED_PRIVATE_EDGE_FIELDS,
            label="allowed_private_edge_fields",
        )
    )
    errors.extend(
        _exact_string_list_errors(
            payload.get("allowed_relation_to_bucket_mappings"),
            expected=ALLOWED_RELATION_TO_BUCKET_MAPPINGS,
            label="allowed_relation_to_bucket_mappings",
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
        errors.append(".gitignore must keep workspace/ ignored for private M2 graph artifacts.")
    return errors


def _exact_string_list_errors(value: Any, *, expected: tuple[str, ...], label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return [f"M2 context-graph {label} must be a list of strings."]
    if tuple(value) != expected:
        return [f"M2 context-graph {label} must exactly match: {', '.join(expected)}."]
    return []


def _validate_roots(value: Any, *, expected: tuple[str, ...], label: str) -> list[str]:
    errors = _exact_string_list_errors(value, expected=expected, label=f"private {label} roots")
    if errors:
        return errors
    for root in value:
        normalized = root.replace("\\", "/")
        if normalized != root:
            errors.append(f"M2 context-graph private {label} root must use forward slashes.")
        if not normalized.startswith("workspace/local-private/extraction-indexing/import/"):
            errors.append(f"M2 context-graph private {label} root must stay ignored/private.")
        if not normalized.endswith("/"):
            errors.append(f"M2 context-graph private {label} root must end with '/'.")
        if ".." in Path(normalized).parts or normalized.startswith("../"):
            errors.append(f"M2 context-graph private {label} root must not contain '..'.")
        if normalized.startswith("/") or WINDOWS_ABSOLUTE_PATH_PATTERN.match(normalized):
            errors.append(f"M2 context-graph private {label} root must be repo-relative.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        PRIVATE_DB_SCHEMA_VERSION,
        LINE_INDEX_SCHEMA_VERSION,
        CONTEXT_GRAPH_SCHEMA_VERSION,
        RECOMMENDED_NEXT_STEP,
        "context_graph_contract",
        "none",
        "context_graph_relation_mapping_only",
        *ALLOWED_PRIVATE_INPUT_ROOTS,
        *ALLOWED_PRIVATE_OUTPUT_ROOTS,
        *ALLOWED_NEXT_GRAPH_INPUTS,
        *ALLOWED_PRIVATE_GRAPH_FIELDS,
        *ALLOWED_PRIVATE_NODE_FIELDS,
        *ALLOWED_PRIVATE_EDGE_FIELDS,
        *ALLOWED_RELATION_TO_BUCKET_MAPPINGS,
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
        "docs/m2-context-graph-contract.md",
        "tests/fixtures/m2_context_graph_scope.synthetic.json",
        "scripts/check_m2_context_graph_contract.py",
    )
    for path in (DOC_PATH, ADR_PATH, LINE_INDEX_DOC_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
        if not path.exists():
            errors.append(f"Missing M2 context-graph doc: {_display_path(path)}.")
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
