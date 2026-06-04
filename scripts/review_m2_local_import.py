from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.run_m2_local_import import (
        PRIVATE_DB_SCHEMA_VERSION,
        PRIVATE_INPUT_ROOT,
        SUMMARY_SCHEMA_VERSION,
        run_m2_local_import,
        write_summary,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from run_m2_local_import import (
        PRIVATE_DB_SCHEMA_VERSION,
        PRIVATE_INPUT_ROOT,
        SUMMARY_SCHEMA_VERSION,
        run_m2_local_import,
        write_summary,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


REVIEW_SCHEMA_VERSION = "m2-local-import-review.v1"
SELF_TEST_SCHEMA_VERSION = "m2-local-import-review-self-test.v1"
DECISION_SCHEMA_VERSION = "m2-local-import-review-decision.v1"
SUMMARY_ROOT = "workspace/local-private/extraction-indexing/import/db-summary/"
REVIEW_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/import/db-review/"
DECISION_FIXTURE_PATH = ROOT / "tests/fixtures/m2_local_import_review_decision.synthetic.json"
RECOMMENDED_LINE_INDEX_IMPLEMENTATION_STEP = "m2_line_index_implementation"
RECOMMENDED_REPEAT_IMPORT_STEP = "repeat_m2_local_import_implementation"
ALLOWED_INPUT_KINDS = {"file", "missing", "unsupported"}
ALLOWED_IMPORT_STATUSES = {"imported", "incompatible", "decode_failed"}
FALSE_SAFETY_FIELDS = (
    "private_paths_included",
    "filenames_included",
    "record_values_in_stdout",
    "edge_values_in_stdout",
    "metadata_values_in_stdout",
    "source_text_in_stdout",
    "hashes_computed",
    "content_hashing_used",
    "path_string_hashing_used",
    "filename_hashing_used",
    "line_index_constructed",
    "context_graph_constructed",
    "retrieval_bucket_mapping_used",
    "automatic_game_install_scanning",
    "recursive_discovery_used",
    "game_files_read",
    "bepinex_logs_read",
    "screenshots_read",
    "ocr_used",
    "save_files_read",
    "current_line_capture_used",
    "ui_text_reading_used",
    "unity_scanning_used",
    "hooks_used",
    "decompiled_code_used",
    "provider_called",
    "companion_contract_changed",
    "raw_payloads_included",
    "raw_logs_included",
    "runtime_evidence_included",
)
DECISION_FALSE_FIELDS = (
    "private_db_reopen_allowed_during_review",
    "line_index_construction_allowed_next",
    "context_graph_construction_allowed_next",
    "retrieval_bucket_mapping_allowed_next",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "generated_review_commit_allowed",
    "generated_private_db_commit_allowed",
    "generated_line_index_commit_allowed",
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
    "ocr",
    "decompiled",
    "dnspy",
    "ilspy",
    "record id",
    "edge id",
    "source text",
    "line index construction approved",
    "context graph construction approved",
    "retrieval bucket mapping approved",
    "provider execution approved",
)


class M2LocalImportReviewError(RuntimeError):
    """Raised when M2 local import review input or output is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a redacted M2 local import summary.")
    parser.add_argument("--summary", type=Path, help="Import summary JSON under db-summary/.")
    parser.add_argument("--output", type=Path, help="Optional review JSON under db-review/.")
    parser.add_argument(
        "--markdown-output", type=Path, help="Optional review Markdown under db-review/."
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 local import review self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": SELF_TEST_SCHEMA_VERSION,
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0
        if args.summary is None:
            parser.error("--summary is required unless --self-test is used.")
        summary_path = resolve_summary_input_path(args.summary, root=ROOT)
        review = build_review(load_json(summary_path), summary_path=summary_path, root=ROOT)
        if review["summary_valid"]:
            if args.output:
                write_json_review(review, resolve_review_output_path(args.output, root=ROOT))
            if args.markdown_output:
                write_markdown_review(
                    review, resolve_review_output_path(args.markdown_output, root=ROOT)
                )
        if args.quiet:
            print(
                "M2 local import review passed."
                if review["summary_valid"]
                else "M2 local import review failed."
            )
        else:
            print(json.dumps(review, indent=2, sort_keys=True))
        return 0 if review["summary_valid"] else 1
    except (OSError, ValueError, M2LocalImportReviewError) as exc:
        parser.error(str(exc))
    return 0


def build_review(summary: Any, *, summary_path: Path, root: Path = ROOT) -> dict[str, Any]:
    errors = collect_summary_errors(summary, summary_path=summary_path, root=root)
    blockers = _dedupe([_blocker_for_error(error) for error in errors])
    if not errors:
        blockers.extend(str(item) for item in summary.get("blocker_categories", []))
        blockers = _dedupe(blockers)
    ready = (
        not errors
        and not blockers
        and summary.get("import_status") == "imported"
        and summary.get("input_exists") is True
        and summary.get("input_kind") == "file"
        and summary.get("json_object_decoded") is True
        and summary.get("profile_schema_version_matches") is True
        and summary.get("private_db_output_written") is True
        and summary.get("private_db_schema_version") == PRIVATE_DB_SCHEMA_VERSION
        and summary.get("m2_import_locally_extracted_db_done") is True
    )
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "summary_valid": not errors,
        "input_exists": isinstance(summary, dict) and summary.get("input_exists") is True,
        "input_kind": summary.get("input_kind", "invalid")
        if isinstance(summary, dict)
        else "invalid",
        "json_object_decoded": isinstance(summary, dict)
        and summary.get("json_object_decoded") is True,
        "profile_schema_version_matches": isinstance(summary, dict)
        and summary.get("profile_schema_version_matches") is True,
        "records_count": _safe_int(summary.get("records_count"))
        if isinstance(summary, dict)
        else 0,
        "context_edges_count": _safe_int(summary.get("context_edges_count"))
        if isinstance(summary, dict)
        else 0,
        "private_db_output_written": isinstance(summary, dict)
        and summary.get("private_db_output_written") is True,
        "private_db_schema_version": summary.get("private_db_schema_version", "invalid")
        if isinstance(summary, dict)
        else "invalid",
        "import_status": summary.get("import_status", "invalid")
        if isinstance(summary, dict)
        else "invalid",
        "ready_for_line_index_implementation": ready,
        "line_index_construction_allowed_next": ready,
        "context_graph_construction_allowed_next": False,
        "retrieval_bucket_mapping_allowed_next": False,
        "private_db_reopened_during_review": False,
        "original_m2_import_done": ready,
        "original_m2_line_index_done": False,
        "original_m2_context_graph_done": False,
        "private_paths_included": False,
        "filenames_included": False,
        "record_values_included": False,
        "edge_values_included": False,
        "source_text_included": False,
        "hashes_computed": False,
        "raw_payloads_included": False,
        "logs_included": False,
        "runtime_evidence_included": False,
        "blockers": blockers,
        "recommended_next_step": (
            RECOMMENDED_LINE_INDEX_IMPLEMENTATION_STEP if ready else RECOMMENDED_REPEAT_IMPORT_STEP
        ),
        "summary_path_redacted": True,
        "review_output_private_only": True,
    }


def collect_summary_errors(summary: Any, *, summary_path: Path, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        resolve_summary_input_path(summary_path, root=root)
    except M2LocalImportReviewError as exc:
        errors.append(str(exc))
    if not isinstance(summary, dict):
        return errors + ["M2 local import summary must be a JSON object."]
    if summary.get("schema_version") != SUMMARY_SCHEMA_VERSION:
        errors.append(f"M2 local import summary schema_version must be {SUMMARY_SCHEMA_VERSION!r}.")
    if summary.get("input_kind") not in ALLOWED_INPUT_KINDS:
        errors.append("M2 local import summary input_kind is not recognized.")
    if summary.get("import_status") not in ALLOWED_IMPORT_STATUSES:
        errors.append("M2 local import summary import_status is not recognized.")
    for field in (
        "input_exists",
        "json_object_decoded",
        "profile_schema_version_matches",
        "private_db_output_written",
        "m2_import_locally_extracted_db_done",
        "ready_for_line_index_contract",
    ):
        if not isinstance(summary.get(field), bool):
            errors.append(f"M2 local import summary {field} must be a boolean.")
    for field in (
        "records_count",
        "context_edges_count",
        "self_edge_count",
        "duplicate_edge_count",
    ):
        if not isinstance(summary.get(field), int) or summary.get(field) < 0:
            errors.append(f"M2 local import summary {field} must be a non-negative integer.")
    blockers = summary.get("blocker_categories")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        errors.append("M2 local import summary blocker_categories must be strings.")
    if summary.get("private_db_schema_version") != PRIVATE_DB_SCHEMA_VERSION:
        errors.append("M2 local import summary private DB schema version is invalid.")
    if summary.get("import_status") == "imported":
        if summary.get("private_db_output_written") is not True:
            errors.append("Imported M2 local import summary must write private DB output.")
        if summary.get("m2_import_locally_extracted_db_done") is not True:
            errors.append("Imported M2 local import summary must mark import criterion done.")
        if summary.get("line_index_constructed") is not False:
            errors.append("M2 local import summary must not build a line index.")
        if summary.get("context_graph_constructed") is not False:
            errors.append("M2 local import summary must not build a context graph.")
    for field in FALSE_SAFETY_FIELDS:
        if summary.get(field) is not False:
            errors.append(f"M2 local import summary must keep {field}=false.")
    errors.extend(_unsafe_value_errors(summary, label="M2 local import summary"))
    return _dedupe(errors)


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 local import review decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 local import review decision fixture must be a JSON object."]
    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"Decision fixture schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("roadmap_milestone") != "M2":
        errors.append("Decision fixture roadmap_milestone must be 'M2'.")
    if payload.get("local_import_review_evidence_required") is not True:
        errors.append("Decision fixture must require local import review evidence.")
    if payload.get("line_index_implementation_allowed_next") != "review_required":
        errors.append("Decision fixture must keep line-index implementation review-gated.")
    if payload.get("recommended_next_step") != RECOMMENDED_LINE_INDEX_IMPLEMENTATION_STEP:
        errors.append("Decision fixture next step must be m2_line_index_implementation.")
    for field in DECISION_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"Decision fixture must keep {field}=false.")
    errors.extend(_unsafe_value_errors(payload, label="Decision fixture"))
    return _dedupe(errors)


def resolve_summary_input_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    summary_root = (root / SUMMARY_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, summary_root):
        raise M2LocalImportReviewError(
            "Unsafe summary path. Use workspace/local-private/extraction-indexing/import/db-summary/."
        )
    if not resolved.exists() or not resolved.is_file():
        raise M2LocalImportReviewError(
            "M2 local import summary path must point to an existing file."
        )
    return resolved


def resolve_review_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    review_root = (root / REVIEW_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, review_root):
        raise M2LocalImportReviewError(
            "Unsafe review output path. Use workspace/local-private/extraction-indexing/import/db-review/."
        )
    if resolved.exists() and resolved.is_dir():
        raise M2LocalImportReviewError("Review output path must be a file path.")
    return resolved


def write_json_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M2 Local Import Review",
        "",
        f"- summary_valid: {_yes_no(review['summary_valid'])}",
        f"- input_exists: {_yes_no(review['input_exists'])}",
        f"- input_kind: {review['input_kind']}",
        f"- records_count: {review['records_count']}",
        f"- context_edges_count: {review['context_edges_count']}",
        f"- private_db_output_written: {_yes_no(review['private_db_output_written'])}",
        f"- import_status: {review['import_status']}",
        (
            "- ready_for_line_index_implementation: "
            f"{_yes_no(review['ready_for_line_index_implementation'])}"
        ),
        "- context_graph_construction_allowed_next: no",
        "- retrieval_bucket_mapping_allowed_next: no",
        "- private_db_reopened_during_review: no",
        f"- recommended_next_step: {review['recommended_next_step']}",
    ]
    if review["blockers"]:
        lines.extend(["", "## Blockers"])
        lines.extend(f"- {blocker}" for blocker in review["blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_self_test() -> None:
    decision_errors = collect_decision_fixture_errors()
    if decision_errors:
        raise M2LocalImportReviewError("; ".join(decision_errors))
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        private_marker = "PRIVATE_LOCAL_IMPORT_REVIEW_VALUE_SHOULD_NOT_APPEAR"
        private_file.write_text(json.dumps(_compatible_payload(private_marker)), encoding="utf-8")
        db_output = Path("workspace/local-private/extraction-indexing/import/db/self-test-db.json")
        summary = run_m2_local_import(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            db_output,
            root=root,
        )
        summary_path = root / SUMMARY_ROOT / "summary.json"
        write_summary(summary, summary_path)
        (root / db_output).unlink()
        private_file.unlink()

        review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
        rendered = json.dumps(review, sort_keys=True)
        if not review["summary_valid"] or not review["ready_for_line_index_implementation"]:
            raise M2LocalImportReviewError("Self-test expected ready redacted local import review.")
        if (
            review["context_graph_construction_allowed_next"]
            or review["retrieval_bucket_mapping_allowed_next"]
        ):
            raise M2LocalImportReviewError("Self-test must not allow graph or retrieval mapping.")
        if private_marker in rendered or str(root) in rendered:
            raise M2LocalImportReviewError("Self-test review leaked private content or paths.")
        json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
        markdown_path = root / REVIEW_OUTPUT_ROOT / "review.md"
        write_json_review(review, resolve_review_output_path(json_path, root=root))
        write_markdown_review(review, resolve_review_output_path(markdown_path, root=root))
        written = json_path.read_text(encoding="utf-8") + markdown_path.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M2LocalImportReviewError(
                "Self-test review output leaked private content or paths."
            )


def _unsafe_value_errors(value: Any, *, label: str) -> list[str]:
    errors: list[str] = []
    for string_value in _iter_string_values(value):
        for url in URL_PATTERN.findall(string_value):
            errors.append(f"{label} contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(string_value):
            errors.append(f"{label} contains a secret/API-key-looking value.")
        if WINDOWS_PRIVATE_PATH_PATTERN.search(string_value) or POSIX_PRIVATE_PATH_PATTERN.search(
            string_value
        ):
            errors.append(f"{label} contains a private absolute path.")
        lowered = string_value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{label} contains forbidden marker {marker!r}.")
    return errors


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise M2LocalImportReviewError("Unsafe path traversal is not allowed.")
    for marker in (
        "logoutput.log",
        "player.log",
        "steamapps",
        "screenshot",
        "ocr",
        ".sav",
        "raw-payload",
        "payload-dump",
        "raw payload",
        "raw-log",
        "raw log",
        "decompiled",
    ):
        if marker in normalized:
            raise M2LocalImportReviewError("Path uses a forbidden runtime/private marker.")


def _resolve_under_root(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute() or WINDOWS_ABSOLUTE_PATH_PATTERN.match(str(raw)):
        return raw.resolve(strict=False)
    return (root / raw).resolve(strict=False)


def _blocker_for_error(error: str) -> str:
    lowered = error.lower()
    if "path" in lowered:
        return "private_path_or_unsafe_path"
    if "marker" in lowered or "payload" in lowered or "log" in lowered:
        return "unsafe_marker_detected"
    if "schema" in lowered or "json object" in lowered:
        return "malformed_summary"
    return "invalid_local_import_summary"


def _safe_int(value: Any) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


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


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def _compatible_payload(private_marker: str) -> dict[str, Any]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            _compatible_record(f"{private_marker}_A", private_marker),
            _compatible_record(f"{private_marker}_B", private_marker),
        ],
        "context_edges": [
            {
                "from_record_id": f"{private_marker}_A",
                "to_record_id": f"{private_marker}_B",
                "relation": "previous_visible",
            }
        ],
        "metadata": {"nested_marker": private_marker},
    }


def _compatible_record(record_id: str, private_marker: str) -> dict[str, Any]:
    return {
        "record_id": record_id,
        "line_id": private_marker,
        "conversation_id": private_marker,
        "speaker_id": private_marker,
        "speaker_label": private_marker,
        "context_placeholder": private_marker,
        "source_text": private_marker,
        "context_tags": [private_marker],
        "redacted_metadata": {"nested_marker": private_marker},
    }


if __name__ == "__main__":
    sys.exit(main())
