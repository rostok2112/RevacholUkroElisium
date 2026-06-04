from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.review_m2_local_import import build_review as build_local_import_review
    from scripts.run_m2_line_index import (
        LOCAL_IMPORT_REVIEW_ROOT,
        PRIVATE_DB_ROOT,
        PRIVATE_LINE_INDEX_ROOT,
        SUMMARY_OUTPUT_ROOT,
        SUMMARY_SCHEMA_VERSION,
        run_m2_line_index,
        write_summary,
    )
    from scripts.run_m2_local_import import (
        PRIVATE_INPUT_ROOT,
        run_m2_local_import,
        write_summary as write_import_summary,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from review_m2_local_import import build_review as build_local_import_review
    from run_m2_line_index import (
        LOCAL_IMPORT_REVIEW_ROOT,
        PRIVATE_DB_ROOT,
        PRIVATE_LINE_INDEX_ROOT,
        SUMMARY_OUTPUT_ROOT,
        SUMMARY_SCHEMA_VERSION,
        run_m2_line_index,
        write_summary,
    )
    from run_m2_local_import import (
        PRIVATE_INPUT_ROOT,
        run_m2_local_import,
        write_summary as write_import_summary,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


REVIEW_SCHEMA_VERSION = "m2-line-index-review.v1"
SELF_TEST_SCHEMA_VERSION = "m2-line-index-review-self-test.v1"
DECISION_SCHEMA_VERSION = "m2-line-index-review-decision.v1"
REVIEW_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/import/line-index-review/"
DECISION_FIXTURE_PATH = ROOT / "tests/fixtures/m2_line_index_review_decision.synthetic.json"
RECOMMENDED_CONTEXT_GRAPH_IMPLEMENTATION_STEP = "m2_context_graph_implementation"
RECOMMENDED_REPEAT_LINE_INDEX_STEP = "repeat_m2_line_index_implementation"
ALLOWED_INPUT_KINDS = {"file", "missing", "unsupported"}
ALLOWED_LINE_INDEX_STATUSES = {"built", "incompatible", "decode_failed"}
FALSE_SAFETY_FIELDS = (
    "private_paths_included",
    "filenames_included",
    "record_ids_in_stdout",
    "line_ids_in_stdout",
    "record_values_in_stdout",
    "source_text_in_stdout",
    "hashes_computed",
    "content_hashing_used",
    "path_string_hashing_used",
    "filename_hashing_used",
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
    "line_index_artifact_reopen_allowed_during_review",
    "private_db_reopen_allowed_during_review",
    "context_graph_construction_allowed_next",
    "retrieval_bucket_mapping_allowed_next",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "generated_review_commit_allowed",
    "generated_private_db_commit_allowed",
    "generated_line_index_commit_allowed",
    "generated_context_graph_commit_allowed",
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
    "line id",
    "source text",
    "context graph construction approved",
    "retrieval bucket mapping approved",
    "provider execution approved",
)


class M2LineIndexReviewError(RuntimeError):
    """Raised when M2 line-index review input or output is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a redacted M2 line-index summary.")
    parser.add_argument(
        "--summary", type=Path, help="Line-index summary JSON under line-index-summary/."
    )
    parser.add_argument(
        "--output", type=Path, help="Optional review JSON under line-index-review/."
    )
    parser.add_argument(
        "--markdown-output", type=Path, help="Optional review Markdown under line-index-review/."
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 line-index review self-test passed.")
            else:
                print(
                    json.dumps(
                        {"ok": True, "schema_version": SELF_TEST_SCHEMA_VERSION},
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
                "M2 line-index review passed."
                if review["summary_valid"]
                else "M2 line-index review failed."
            )
        else:
            print(json.dumps(review, indent=2, sort_keys=True))
        return 0 if review["summary_valid"] else 1
    except (OSError, ValueError, M2LineIndexReviewError) as exc:
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
        and summary.get("line_index_status") == "built"
        and summary.get("input_exists") is True
        and summary.get("input_kind") == "file"
        and summary.get("private_db_schema_version_matches") is True
        and summary.get("line_index_output_written") is True
        and summary.get("m2_line_index_done") is True
    )
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "summary_valid": not errors,
        "input_exists": isinstance(summary, dict) and summary.get("input_exists") is True,
        "input_kind": summary.get("input_kind", "invalid")
        if isinstance(summary, dict)
        else "invalid",
        "private_db_schema_version_matches": isinstance(summary, dict)
        and summary.get("private_db_schema_version_matches") is True,
        "records_count": _safe_int(summary.get("records_count"))
        if isinstance(summary, dict)
        else 0,
        "line_index_entry_count": _safe_int(summary.get("line_index_entry_count"))
        if isinstance(summary, dict)
        else 0,
        "line_index_output_written": isinstance(summary, dict)
        and summary.get("line_index_output_written") is True,
        "line_index_status": summary.get("line_index_status", "invalid")
        if isinstance(summary, dict)
        else "invalid",
        "ready_for_context_graph_implementation": ready,
        "context_graph_construction_allowed_next": ready,
        "retrieval_bucket_mapping_allowed_next": "context_graph_relation_mapping_only"
        if ready
        else False,
        "line_index_artifact_reopened_during_review": False,
        "private_db_reopened_during_review": False,
        "original_m2_import_done": ready,
        "original_m2_line_index_done": ready,
        "original_m2_context_graph_done": False,
        "private_paths_included": False,
        "filenames_included": False,
        "record_ids_included": False,
        "line_ids_included": False,
        "source_text_included": False,
        "hashes_computed": False,
        "raw_payloads_included": False,
        "logs_included": False,
        "runtime_evidence_included": False,
        "blockers": blockers,
        "recommended_next_step": RECOMMENDED_CONTEXT_GRAPH_IMPLEMENTATION_STEP
        if ready
        else RECOMMENDED_REPEAT_LINE_INDEX_STEP,
        "summary_path_redacted": True,
        "review_output_private_only": True,
    }


def collect_summary_errors(summary: Any, *, summary_path: Path, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        resolve_summary_input_path(summary_path, root=root)
    except M2LineIndexReviewError as exc:
        errors.append(str(exc))
    if not isinstance(summary, dict):
        return errors + ["M2 line-index summary must be a JSON object."]
    if summary.get("schema_version") != SUMMARY_SCHEMA_VERSION:
        errors.append(f"M2 line-index summary schema_version must be {SUMMARY_SCHEMA_VERSION!r}.")
    if summary.get("input_kind") not in ALLOWED_INPUT_KINDS:
        errors.append("M2 line-index summary input_kind is not recognized.")
    if summary.get("line_index_status") not in ALLOWED_LINE_INDEX_STATUSES:
        errors.append("M2 line-index summary line_index_status is not recognized.")
    for field in (
        "input_exists",
        "private_db_schema_version_matches",
        "line_index_output_written",
        "m2_line_index_done",
        "ready_for_context_graph_contract",
    ):
        if not isinstance(summary.get(field), bool):
            errors.append(f"M2 line-index summary {field} must be a boolean.")
    for field in ("records_count", "line_index_entry_count"):
        if not isinstance(summary.get(field), int) or summary.get(field) < 0:
            errors.append(f"M2 line-index summary {field} must be a non-negative integer.")
    blockers = summary.get("blocker_categories")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        errors.append("M2 line-index summary blocker_categories must be strings.")
    if summary.get("line_index_status") == "built":
        if summary.get("line_index_output_written") is not True:
            errors.append("Built M2 line-index summary must write private line-index output.")
        if summary.get("m2_line_index_done") is not True:
            errors.append("Built M2 line-index summary must mark line-index criterion done.")
        if summary.get("context_graph_constructed") is not False:
            errors.append("M2 line-index summary must not build a context graph.")
        if summary.get("retrieval_bucket_mapping_used") is not False:
            errors.append("M2 line-index summary must not map retrieval buckets.")
    for field in FALSE_SAFETY_FIELDS:
        if summary.get(field) is not False:
            errors.append(f"M2 line-index summary must keep {field}=false.")
    errors.extend(_unsafe_value_errors(summary, label="M2 line-index summary"))
    return _dedupe(errors)


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 line-index review decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 line-index review decision fixture must be a JSON object."]
    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"Decision fixture schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("roadmap_milestone") != "M2":
        errors.append("Decision fixture roadmap_milestone must be 'M2'.")
    if payload.get("line_index_review_evidence_required") is not True:
        errors.append("Decision fixture must require line-index review evidence.")
    if payload.get("context_graph_implementation_allowed_next") != "review_required":
        errors.append("Decision fixture must keep context-graph implementation review-gated.")
    if payload.get("recommended_next_step") != RECOMMENDED_CONTEXT_GRAPH_IMPLEMENTATION_STEP:
        errors.append("Decision fixture next step must be m2_context_graph_implementation.")
    for field in DECISION_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"Decision fixture must keep {field}=false.")
    errors.extend(_unsafe_value_errors(payload, label="Decision fixture"))
    return _dedupe(errors)


def resolve_summary_input_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    summary_root = (root / SUMMARY_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, summary_root):
        raise M2LineIndexReviewError(
            "Unsafe summary path. Use workspace/local-private/extraction-indexing/import/line-index-summary/."
        )
    if not resolved.exists() or not resolved.is_file():
        raise M2LineIndexReviewError("M2 line-index summary path must point to an existing file.")
    return resolved


def resolve_review_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    review_root = (root / REVIEW_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, review_root):
        raise M2LineIndexReviewError(
            "Unsafe review output path. Use workspace/local-private/extraction-indexing/import/line-index-review/."
        )
    if resolved.exists() and resolved.is_dir():
        raise M2LineIndexReviewError("Review output path must be a file path.")
    return resolved


def write_json_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M2 Line-Index Review",
        "",
        f"- summary_valid: {_yes_no(review['summary_valid'])}",
        f"- input_exists: {_yes_no(review['input_exists'])}",
        f"- input_kind: {review['input_kind']}",
        f"- records_count: {review['records_count']}",
        f"- line_index_entry_count: {review['line_index_entry_count']}",
        f"- line_index_output_written: {_yes_no(review['line_index_output_written'])}",
        f"- line_index_status: {review['line_index_status']}",
        f"- ready_for_context_graph_implementation: {_yes_no(review['ready_for_context_graph_implementation'])}",
        f"- context_graph_construction_allowed_next: {_yes_no(review['context_graph_construction_allowed_next'])}",
        f"- retrieval_bucket_mapping_allowed_next: {review['retrieval_bucket_mapping_allowed_next']}",
        "- line_index_artifact_reopened_during_review: no",
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
        raise M2LineIndexReviewError("; ".join(decision_errors))
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_marker = "PRIVATE_LINE_INDEX_REVIEW_VALUE_SHOULD_NOT_APPEAR"
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        private_file.write_text(json.dumps(_compatible_export(private_marker)), encoding="utf-8")
        db_path = Path(PRIVATE_DB_ROOT) / "imported-db.json"
        import_summary = run_m2_local_import(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json", db_path, root=root
        )
        import_summary_path = (
            root / "workspace/local-private/extraction-indexing/import/db-summary/summary.json"
        )
        write_import_summary(import_summary, import_summary_path)
        import_review = build_local_import_review(
            import_summary, summary_path=import_summary_path, root=root
        )
        import_review_path = root / LOCAL_IMPORT_REVIEW_ROOT / "review.json"
        import_review_path.parent.mkdir(parents=True, exist_ok=True)
        import_review_path.write_text(
            json.dumps(import_review, indent=2, sort_keys=True), encoding="utf-8"
        )
        line_index_path = Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json"
        summary = run_m2_line_index(
            db_path, Path(LOCAL_IMPORT_REVIEW_ROOT) / "review.json", line_index_path, root=root
        )
        summary_path = root / SUMMARY_OUTPUT_ROOT / "summary.json"
        write_summary(summary, summary_path)
        (root / line_index_path).unlink()
        (root / db_path).unlink()
        private_file.unlink()

        review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
        rendered = json.dumps(review, sort_keys=True)
        if not review["summary_valid"] or not review["ready_for_context_graph_implementation"]:
            raise M2LineIndexReviewError("Self-test expected ready redacted line-index review.")
        if private_marker in rendered or str(root) in rendered:
            raise M2LineIndexReviewError("Self-test review leaked private content or paths.")
        json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
        markdown_path = root / REVIEW_OUTPUT_ROOT / "review.md"
        write_json_review(review, resolve_review_output_path(json_path, root=root))
        write_markdown_review(review, resolve_review_output_path(markdown_path, root=root))
        written = json_path.read_text(encoding="utf-8") + markdown_path.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M2LineIndexReviewError("Self-test review output leaked private content or paths.")


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
        raise M2LineIndexReviewError("Unsafe path traversal is not allowed.")
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
            raise M2LineIndexReviewError("Path uses a forbidden runtime/private marker.")


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
    return "invalid_line_index_summary"


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


def _compatible_export(private_marker: str) -> dict[str, Any]:
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
