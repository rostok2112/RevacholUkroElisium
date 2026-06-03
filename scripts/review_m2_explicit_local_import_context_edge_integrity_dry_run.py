from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

try:
    from scripts.run_m2_explicit_local_import_context_edge_integrity_dry_run import (
        PRIVATE_INPUT_ROOT,
        PRIVATE_OUTPUT_ROOT,
        SUMMARY_SCHEMA_VERSION,
        build_m2_explicit_local_import_context_edge_integrity_dry_run,
        write_summary,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from run_m2_explicit_local_import_context_edge_integrity_dry_run import (
        PRIVATE_INPUT_ROOT,
        PRIVATE_OUTPUT_ROOT,
        SUMMARY_SCHEMA_VERSION,
        build_m2_explicit_local_import_context_edge_integrity_dry_run,
        write_summary,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


REVIEW_SCHEMA_VERSION = "m2-explicit-local-import-context-edge-integrity-dry-run-review.v1"
SELF_TEST_SCHEMA_VERSION = (
    "m2-explicit-local-import-context-edge-integrity-dry-run-review-self-test.v1"
)
DECISION_SCHEMA_VERSION = (
    "m2-explicit-local-import-context-edge-integrity-dry-run-review-decision.v1"
)
REVIEW_OUTPUT_ROOT = (
    "workspace/local-private/extraction-indexing/import/context-edge-integrity-review/"
)
DECISION_FIXTURE_PATH = (
    ROOT / "tests/fixtures/"
    "m2_explicit_local_import_context_edge_integrity_dry_run_review_decision.synthetic.json"
)
RECOMMENDED_LOCAL_IMPORT_FINAL_APPROVAL_CONTRACT_STEP = "m2_local_import_final_approval_contract"
RECOMMENDED_REPEAT_DRY_RUN_STEP = "repeat_m2_explicit_local_import_context_edge_integrity_dry_run"

FALSE_SAFETY_FIELDS = (
    "private_paths_included",
    "filenames_included",
    "record_ids_included",
    "record_ids_logged",
    "record_ids_normalized",
    "record_ids_hashed",
    "edge_ids_included",
    "edge_ids_logged",
    "edge_ids_normalized",
    "edge_ids_hashed",
    "relation_values_included",
    "relation_values_logged",
    "relation_values_normalized",
    "duplicate_tuples_included",
    "duplicate_tuples_logged",
    "duplicate_tuples_normalized",
    "duplicate_tuples_hashed",
    "retrieval_bucket_mapping_used",
    "record_values_inspected",
    "record_values_included",
    "record_values_logged",
    "record_values_compared",
    "record_values_normalized",
    "context_tags_contents_traversed",
    "metadata_contents_traversed",
    "source_text_included",
    "hashes_computed",
    "real_db_imported",
    "line_index_constructed",
    "context_graph_constructed",
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
    "real_text_included",
    "raw_payloads_included",
    "raw_logs_included",
    "runtime_evidence_included",
)
DECISION_FALSE_FIELDS = (
    "m2_import_locally_extracted_db_done",
    "m2_line_index_done",
    "m2_context_graph_done",
    "private_export_reopen_allowed_during_review",
    "record_id_emission_allowed",
    "edge_id_emission_allowed",
    "relation_value_emission_allowed",
    "duplicate_tuple_emission_allowed",
    "id_normalization_allowed",
    "id_hashing_allowed",
    "relation_normalization_allowed",
    "retrieval_bucket_mapping_allowed",
    "record_traversal_allowed",
    "record_value_inspection_allowed",
    "context_tags_content_traversal_allowed",
    "redacted_metadata_content_traversal_allowed",
    "metadata_content_inspection_allowed",
    "source_text_emission_allowed",
    "content_hashing_allowed",
    "real_db_import_allowed_next",
    "line_index_construction_allowed_next",
    "context_graph_construction_allowed_next",
    "automatic_game_install_scanning_allowed",
    "recursive_discovery_allowed",
    "game_files_read_allowed",
    "bepinex_logs_read_allowed",
    "screenshots_allowed",
    "ocr_allowed",
    "save_files_read_allowed",
    "decompiled_code_allowed",
    "current_line_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "generated_review_commit_allowed",
)
ALLOWED_INPUT_KINDS = {"file", "missing", "unsupported"}
ALLOWED_INTEGRITY_STATUSES = {"compatible", "incompatible", "decode_failed"}
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
    "record id emission approved",
    "edge id emission approved",
    "relation value emission approved",
    "duplicate tuple emission approved",
    "id normalization approved",
    "id hashing approved",
    "retrieval bucket mapping approved",
    "record traversal approved",
    "record value inspection approved",
    "source text emission approved",
    "metadata content inspection approved",
    "db import approved",
    "line index construction approved",
    "context graph construction approved",
    "current-line capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "provider execution approved",
)


class M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(RuntimeError):
    """Raised when M2 context-edge integrity review input or output is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review a redacted M2 local-import context-edge integrity dry-run summary."
    )
    parser.add_argument(
        "--summary",
        type=Path,
        help="Context-edge integrity summary JSON under the ignored context-edge-integrity root.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional redacted JSON review under the ignored context-edge-integrity-review root.",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        help="Optional redacted Markdown review under the ignored review root.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace review smoke without real private inputs.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 local-import context-edge integrity dry-run review self-test passed.")
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
                    review,
                    resolve_review_output_path(args.markdown_output, root=ROOT),
                )
        if args.quiet:
            print(
                "M2 local-import context-edge integrity dry-run review passed."
                if review["summary_valid"]
                else "M2 local-import context-edge integrity dry-run review failed."
            )
        else:
            print(json.dumps(review, indent=2, sort_keys=True))
        return 0 if review["summary_valid"] else 1
    except (OSError, ValueError, M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError) as exc:
        parser.error(str(exc))
    return 0


def build_review(
    summary: dict[str, Any],
    *,
    summary_path: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    errors = collect_summary_errors(summary, summary_path=summary_path, root=root)
    blockers = _dedupe([_blocker_for_error(error) for error in errors])
    if not errors:
        blockers.extend(str(item) for item in summary.get("blocker_categories", []))
        blockers = _dedupe(blockers)
    ready = (
        not errors
        and not blockers
        and summary.get("context_edge_integrity_status") == "compatible"
        and summary.get("input_exists") is True
        and summary.get("input_kind") == "file"
        and summary.get("envelope_compatible") is True
        and summary.get("records_shape_reviewed") is True
        and summary.get("context_edges_shape_reviewed") is True
        and summary.get("context_edge_references_reviewed") is True
        and summary.get("self_edge_count") == 0
        and summary.get("duplicate_edge_count") == 0
        and summary.get("all_context_edges_integrity_compatible") is True
    )
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "summary_valid": not errors,
        "input_exists": summary.get("input_exists") is True,
        "input_kind": summary.get("input_kind", "invalid"),
        "envelope_compatible": summary.get("envelope_compatible") is True,
        "records_shape_reviewed": summary.get("records_shape_reviewed") is True,
        "context_edges_shape_reviewed": summary.get("context_edges_shape_reviewed") is True,
        "context_edge_references_reviewed": (
            summary.get("context_edge_references_reviewed") is True
        ),
        "context_edges_count": _safe_int(summary.get("context_edges_count")),
        "self_edge_count": _safe_int(summary.get("self_edge_count")),
        "duplicate_edge_count": _safe_int(summary.get("duplicate_edge_count")),
        "all_context_edges_integrity_compatible": (
            summary.get("all_context_edges_integrity_compatible") is True
        ),
        "context_edge_integrity_status": (
            summary.get("context_edge_integrity_status")
            if summary.get("context_edge_integrity_status") in ALLOWED_INTEGRITY_STATUSES
            else "invalid"
        ),
        "ready_for_local_import_final_approval_contract_decision": ready,
        "retrieval_bucket_mapping_allowed_next": False,
        "real_db_import_allowed_next": False,
        "line_index_construction_allowed_next": False,
        "context_graph_construction_allowed_next": False,
        "original_m2_import_done": False,
        "original_m2_line_index_done": False,
        "original_m2_context_graph_done": False,
        "private_export_reopened_during_review": False,
        "record_ids_included": False,
        "edge_ids_included": False,
        "relation_values_included": False,
        "duplicate_tuples_included": False,
        "record_values_inspected": False,
        "context_tags_contents_traversed": False,
        "metadata_contents_traversed": False,
        "hashes_computed": False,
        "real_db_imported": False,
        "line_index_constructed": False,
        "context_graph_constructed": False,
        "private_paths_included": False,
        "filenames_included": False,
        "raw_payloads_included": False,
        "logs_included": False,
        "runtime_evidence_included": False,
        "blockers": blockers,
        "recommended_next_step": (
            RECOMMENDED_LOCAL_IMPORT_FINAL_APPROVAL_CONTRACT_STEP
            if ready
            else RECOMMENDED_REPEAT_DRY_RUN_STEP
        ),
        "summary_path_redacted": True,
        "review_output_private_only": True,
    }


def collect_summary_errors(
    summary: Any,
    *,
    summary_path: Path,
    root: Path = ROOT,
) -> list[str]:
    errors: list[str] = []
    try:
        resolve_summary_input_path(summary_path, root=root)
    except M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError as exc:
        errors.append(str(exc))
    if not isinstance(summary, dict):
        return errors + ["M2 context-edge integrity dry-run summary must be a JSON object."]
    if summary.get("schema_version") != SUMMARY_SCHEMA_VERSION:
        errors.append(
            f"M2 context-edge integrity summary schema_version must be {SUMMARY_SCHEMA_VERSION!r}."
        )
    if summary.get("input_kind") not in ALLOWED_INPUT_KINDS:
        errors.append("M2 context-edge integrity summary input_kind is not recognized.")
    for field in (
        "input_exists",
        "envelope_compatible",
        "records_shape_reviewed",
        "context_edges_shape_reviewed",
        "context_edge_references_reviewed",
        "all_context_edges_integrity_compatible",
        "output_written",
    ):
        if not isinstance(summary.get(field), bool):
            errors.append(f"M2 context-edge integrity summary {field} must be a boolean.")
    for field in ("context_edges_count", "self_edge_count", "duplicate_edge_count"):
        if not isinstance(summary.get(field), int) or summary.get(field) < 0:
            errors.append(
                f"M2 context-edge integrity summary {field} must be a non-negative integer."
            )
    if summary.get("context_edge_integrity_status") not in ALLOWED_INTEGRITY_STATUSES:
        errors.append("M2 context-edge integrity summary status is not recognized.")
    if (
        summary.get("dry_run") is not True
        or summary.get("context_edge_integrity_aggregate_only") is not True
    ):
        errors.append(
            "M2 context-edge integrity summary must remain aggregate-only dry-run evidence."
        )
    if summary.get("decode_size_cap_applied") is not False:
        errors.append(
            "M2 context-edge integrity summary must preserve decode_size_cap_applied=false."
        )
    blockers = summary.get("blocker_categories")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        errors.append("M2 context-edge integrity summary blocker_categories must be strings.")
    errors.extend(_count_consistency_errors(summary))
    for field in FALSE_SAFETY_FIELDS:
        if summary.get(field) is not False:
            errors.append(f"M2 context-edge integrity summary must keep {field}=false.")
    errors.extend(_unsafe_value_errors(summary, label="M2 context-edge integrity summary"))
    return _dedupe(errors)


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 context-edge integrity review decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M2 context-edge integrity review decision fixture must be a JSON object."]
    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"Decision fixture schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("roadmap_milestone") != "M2":
        errors.append("Decision fixture roadmap_milestone must be 'M2'.")
    if payload.get("context_edge_integrity_review_evidence_required") is not True:
        errors.append("Decision fixture must require context-edge integrity review evidence.")
    if payload.get("local_import_final_approval_contract_allowed_next") != "decision_pending":
        errors.append("Decision fixture final approval contract must remain pending.")
    if (
        payload.get("recommended_next_step")
        != RECOMMENDED_LOCAL_IMPORT_FINAL_APPROVAL_CONTRACT_STEP
    ):
        errors.append(
            "Decision fixture recommended_next_step must be "
            f"{RECOMMENDED_LOCAL_IMPORT_FINAL_APPROVAL_CONTRACT_STEP!r}."
        )
    for field in DECISION_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"Decision fixture must keep {field}=false.")
    errors.extend(_unsafe_value_errors(payload, label="Decision fixture"))
    return _dedupe(errors)


def resolve_summary_input_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    summary_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, summary_root):
        raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
            "Unsafe summary path. Use "
            "workspace/local-private/extraction-indexing/import/context-edge-integrity/."
        )
    if not resolved.exists() or not resolved.is_file():
        raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
            "M2 context-edge integrity summary path must point to an existing file."
        )
    return resolved


def resolve_review_output_path(path: Path, *, root: Path = ROOT) -> Path:
    _reject_unsafe_path_text(path)
    resolved = _resolve_under_root(path, root=root)
    review_root = (root / REVIEW_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, review_root):
        raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
            "Unsafe review output path. Use "
            "workspace/local-private/extraction-indexing/import/context-edge-integrity-review/."
        )
    if resolved.exists() and resolved.is_dir():
        raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
            "Review output path must be a file path."
        )
    return resolved


def write_json_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_review(review: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# M2 Local-Import Context-Edge Integrity Dry-Run Review",
        "",
        f"- summary_valid: {_yes_no(review['summary_valid'])}",
        f"- input_exists: {_yes_no(review['input_exists'])}",
        f"- input_kind: {review['input_kind']}",
        f"- envelope_compatible: {_yes_no(review['envelope_compatible'])}",
        f"- records_shape_reviewed: {_yes_no(review['records_shape_reviewed'])}",
        f"- context_edges_shape_reviewed: {_yes_no(review['context_edges_shape_reviewed'])}",
        (
            "- context_edge_references_reviewed: "
            f"{_yes_no(review['context_edge_references_reviewed'])}"
        ),
        f"- context_edges_count: {review['context_edges_count']}",
        f"- self_edge_count: {review['self_edge_count']}",
        f"- duplicate_edge_count: {review['duplicate_edge_count']}",
        (
            "- all_context_edges_integrity_compatible: "
            f"{_yes_no(review['all_context_edges_integrity_compatible'])}"
        ),
        f"- context_edge_integrity_status: {review['context_edge_integrity_status']}",
        (
            "- ready_for_local_import_final_approval_contract_decision: "
            f"{_yes_no(review['ready_for_local_import_final_approval_contract_decision'])}"
        ),
        "- retrieval_bucket_mapping_allowed_next: no",
        "- real_db_import_allowed_next: no",
        "- line_index_construction_allowed_next: no",
        "- context_graph_construction_allowed_next: no",
        "- original_m2_import_done: no",
        "- original_m2_line_index_done: no",
        "- original_m2_context_graph_done: no",
        "- private_export_reopened_during_review: no",
        "- record_ids_included: no",
        "- edge_ids_included: no",
        "- relation_values_included: no",
        "- duplicate_tuples_included: no",
        "- private_paths_included: no",
        f"- recommended_next_step: {review['recommended_next_step']}",
    ]
    if review["blockers"]:
        lines.extend(["", "## Blockers"])
        lines.extend(f"- {blocker}" for blocker in review["blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_self_test() -> None:
    decision_errors = collect_decision_fixture_errors()
    if decision_errors:
        raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError("; ".join(decision_errors))
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        private_marker = "PRIVATE_CONTEXT_EDGE_INTEGRITY_REVIEW_VALUE_SHOULD_NOT_APPEAR"
        private_file.write_text(json.dumps(_compatible_payload(private_marker)), encoding="utf-8")
        summary = build_m2_explicit_local_import_context_edge_integrity_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            root=root,
        )
        summary_path = root / PRIVATE_OUTPUT_ROOT / "summary.json"
        write_summary(summary, summary_path)
        private_file.unlink()

        review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
        rendered = json.dumps(review, sort_keys=True)
        if (
            not review["summary_valid"]
            or not review["ready_for_local_import_final_approval_contract_decision"]
        ):
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
                "Self-test expected ready redacted context-edge integrity review."
            )
        if (
            review["retrieval_bucket_mapping_allowed_next"]
            or review["real_db_import_allowed_next"]
            or review["line_index_construction_allowed_next"]
            or review["context_graph_construction_allowed_next"]
        ):
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
                "Self-test must not allow import, index, graph, or retrieval mapping."
            )
        if private_marker in rendered or str(root) in rendered:
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
                "Self-test review leaked private content or paths."
            )
        json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
        markdown_path = root / REVIEW_OUTPUT_ROOT / "review.md"
        write_json_review(review, resolve_review_output_path(json_path, root=root))
        write_markdown_review(review, resolve_review_output_path(markdown_path, root=root))
        written = json_path.read_text(encoding="utf-8") + markdown_path.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
                "Self-test review output leaked private content or paths."
            )


def _count_consistency_errors(summary: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    edge_count = summary.get("context_edges_count")
    self_edges = summary.get("self_edge_count")
    duplicate_edges = summary.get("duplicate_edge_count")
    if all(isinstance(value, int) and value >= 0 for value in (edge_count, self_edges)):
        if self_edges > edge_count:
            errors.append("M2 context-edge integrity summary self-edge count exceeds edge count.")
    if all(isinstance(value, int) and value >= 0 for value in (edge_count, duplicate_edges)):
        if duplicate_edges > max(edge_count - 1, 0):
            errors.append("M2 context-edge integrity summary duplicate count exceeds edge count.")
    if summary.get("context_edge_integrity_status") == "compatible":
        if summary.get("all_context_edges_integrity_compatible") is not True:
            errors.append(
                "M2 context-edge integrity compatible summary must set integrity compatible."
            )
        if summary.get("envelope_compatible") is not True:
            errors.append("M2 context-edge integrity compatible summary needs envelope evidence.")
        if summary.get("records_shape_reviewed") is not True:
            errors.append(
                "M2 context-edge integrity compatible summary needs record-shape evidence."
            )
        if summary.get("context_edges_shape_reviewed") is not True:
            errors.append("M2 context-edge integrity compatible summary needs edge-shape evidence.")
        if summary.get("context_edge_references_reviewed") is not True:
            errors.append(
                "M2 context-edge integrity compatible summary needs edge-reference evidence."
            )
        if self_edges != 0 or duplicate_edges != 0:
            errors.append("M2 context-edge integrity compatible summary must have no blockers.")
    if summary.get("all_context_edges_integrity_compatible") is True and (
        self_edges != 0 or duplicate_edges != 0
    ):
        errors.append("M2 context-edge integrity true compatibility conflicts with counts.")
    return errors


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
        raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
            "Unsafe path traversal is not allowed."
        )
    for marker in (
        "logoutput.log",
        "player.log",
        "steamapps",
        "screenshot",
        "ocr",
        ".sav",
        "raw-payload",
        "raw payload",
        "raw-log",
        "raw log",
        "decompiled",
    ):
        if marker in normalized:
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError(
                "Path uses a forbidden runtime/private marker."
            )


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
    if "count" in lowered:
        return "inconsistent_context_edge_integrity_counts"
    if "schema_version" in lowered or "json object" in lowered:
        return "malformed_summary"
    return "invalid_context_edge_integrity_summary"


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
            {
                "record_id": f"{private_marker}_A",
                "line_id": private_marker,
                "conversation_id": private_marker,
                "speaker_id": private_marker,
                "speaker_label": private_marker,
                "context_placeholder": private_marker,
                "source_text": private_marker,
                "context_tags": [private_marker],
                "redacted_metadata": {"nested_marker": private_marker},
            },
            {
                "record_id": f"{private_marker}_B",
                "line_id": private_marker,
                "conversation_id": private_marker,
                "speaker_id": private_marker,
                "speaker_label": private_marker,
                "context_placeholder": private_marker,
                "source_text": private_marker,
                "context_tags": [private_marker],
                "redacted_metadata": {"nested_marker": private_marker},
            },
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


if __name__ == "__main__":
    sys.exit(main())
