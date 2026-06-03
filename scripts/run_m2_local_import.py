from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_m2_local_import_final_approval_contract import (
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
        FUTURE_PROFILE_SCHEMA_VERSION,
    )
    from scripts.run_m2_explicit_local_import_context_edge_integrity_dry_run import (
        _context_edge_references_are_compatible,
        _context_edges_shape_is_compatible,
        _count_integrity_blockers,
        _envelope_is_compatible,
        _input_path_without_symlink_resolution,
        _records_shape_is_compatible,
        _top_level_record_ids,
    )
    from scripts.run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_m2_local_import_final_approval_contract import (
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
        FUTURE_PROFILE_SCHEMA_VERSION,
    )
    from run_m2_explicit_local_import_context_edge_integrity_dry_run import (
        _context_edge_references_are_compatible,
        _context_edges_shape_is_compatible,
        _count_integrity_blockers,
        _envelope_is_compatible,
        _input_path_without_symlink_resolution,
        _records_shape_is_compatible,
        _top_level_record_ids,
    )
    from run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "m2-local-import-summary.v1"
PRIVATE_DB_SCHEMA_VERSION = "m2-local-import-db.v1"
PRIVATE_OUTPUT_ROOT = ALLOWED_PRIVATE_OUTPUT_ROOTS[0]


class M2LocalImportError(RuntimeError):
    """Raised when an M2 local import request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Import one explicit workspace-private m2-local-private-export.v1 JSON export into "
            "an ignored private DB artifact. Stdout stays redacted."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Explicit JSON file under workspace/local-private/extraction-indexing/input/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Required private DB JSON output under "
            "workspace/local-private/extraction-indexing/import/db/."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temp-workspace smoke without real private inputs.",
    )
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 local import self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": "m2-local-import-self-test.v1",
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0

        if args.input is None or args.output is None:
            parser.error("--input and --output are required unless --self-test is used.")

        summary = run_m2_local_import(args.input, args.output, root=ROOT)
        if args.quiet:
            print("M2 local import passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (M2LocalImportError, OSError, PrivateInputAdapterDryRunError, ValueError) as exc:
        parser.error(str(exc))
    return 0


def run_m2_local_import(
    input_path: Path,
    output_path: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    resolved_input = resolve_input_path(input_path, root=root)
    resolved_output = resolve_output_path(output_path, root=root)
    summary = _base_summary()
    summary["input_exists"] = resolved_input.exists()

    if _input_path_without_symlink_resolution(input_path, root=root).is_symlink():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("symlink_input_rejected")
        return summary
    if not resolved_input.exists():
        summary["input_kind"] = "missing"
        summary["blocker_categories"].append("input_missing")
        return summary
    if resolved_input.is_dir():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("directory_input_rejected")
        return summary
    if not resolved_input.is_file():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("unsupported_input_kind")
        return summary

    summary["input_kind"] = "file"
    try:
        with resolved_input.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (UnicodeDecodeError, json.JSONDecodeError):
        summary["import_status"] = "decode_failed"
        summary["blocker_categories"].append("json_decode_failed")
        return summary

    summary["json_object_decoded"] = isinstance(payload, dict)
    if not isinstance(payload, dict):
        summary["blocker_categories"].append("top_level_json_object_required")
        return _finalize(summary)

    if payload.get("schema_version") == FUTURE_PROFILE_SCHEMA_VERSION:
        summary["profile_schema_version_matches"] = True
    records = payload.get("records")
    context_edges = payload.get("context_edges")
    if isinstance(records, list):
        summary["records_count"] = len(records)
    if isinstance(context_edges, list):
        summary["context_edges_count"] = len(context_edges)

    if not _envelope_is_compatible(payload, summary):
        return _finalize(summary)
    if not _records_shape_is_compatible(payload, summary):
        summary["blocker_categories"].append("record_shape_precondition_failed")
        return _finalize(summary)
    if not _context_edges_shape_is_compatible(payload, summary):
        summary["blocker_categories"].append("context_edge_shape_precondition_failed")
        return _finalize(summary)
    record_ids = _top_level_record_ids(payload, summary)
    if record_ids is None:
        return _finalize(summary)
    if not _context_edge_references_are_compatible(context_edges, record_ids, summary):
        return _finalize(summary)
    _count_integrity_blockers(context_edges, summary)
    if summary["self_edge_count"] or summary["duplicate_edge_count"]:
        if summary["self_edge_count"]:
            summary["blocker_categories"].append("self_edges_found")
        if summary["duplicate_edge_count"]:
            summary["blocker_categories"].append("duplicate_edges_found")
        return _finalize(summary)

    imported_db = _build_private_db(payload)
    _write_private_db(imported_db, resolved_output)
    summary.update(
        {
            "import_status": "imported",
            "private_db_output_written": True,
            "private_db_schema_version": PRIVATE_DB_SCHEMA_VERSION,
            "m2_import_locally_extracted_db_implemented": True,
            "m2_import_locally_extracted_db_done": True,
            "ready_for_line_index_contract": True,
        }
    )
    return _finalize(summary)


def resolve_output_path(output_path: Path, *, root: Path = ROOT) -> Path:
    try:
        resolved = resolve_private_output_path(output_path, root=root)
        output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
        resolved.relative_to(output_root)
    except (PrivateInputAdapterDryRunError, ValueError) as exc:
        raise M2LocalImportError(
            "Unsafe output path. Use a JSON path under "
            "workspace/local-private/extraction-indexing/import/db/."
        ) from exc
    if resolved.suffix.lower() != ".json":
        raise M2LocalImportError("Output path must use the .json suffix.")
    return resolved


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        private_marker = "PRIVATE_LOCAL_IMPORT_VALUE_SHOULD_NOT_APPEAR"
        private_file.write_text(json.dumps(_compatible_payload(private_marker)), encoding="utf-8")

        output_path = Path(PRIVATE_OUTPUT_ROOT) / "self-test-db.json"
        summary = run_m2_local_import(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            output_path,
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if (
            summary["import_status"] != "imported"
            or summary["records_count"] != 2
            or summary["context_edges_count"] != 1
            or not summary["private_db_output_written"]
        ):
            raise M2LocalImportError("Self-test import summary was incorrect.")
        if private_marker in rendered or str(root) in rendered:
            raise M2LocalImportError("Self-test summary leaked private content or paths.")

        written_path = root / output_path
        private_db = json.loads(written_path.read_text(encoding="utf-8"))
        written = json.dumps(private_db, sort_keys=True)
        if private_marker not in written:
            raise M2LocalImportError("Self-test private DB did not preserve private content.")
        if private_db["line_index_constructed"] or private_db["context_graph_constructed"]:
            raise M2LocalImportError("Self-test private DB must not build index or graph.")


def _build_private_db(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": PRIVATE_DB_SCHEMA_VERSION,
        "source_schema_version": FUTURE_PROFILE_SCHEMA_VERSION,
        "source_kind": payload["source_kind"],
        "imported_from_explicit_private_export": True,
        "records": payload["records"],
        "context_edges": payload["context_edges"],
        "metadata": payload["metadata"],
        "line_index_constructed": False,
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
        "automatic_game_install_scanning": False,
        "game_files_read": False,
        "bepinex_logs_read": False,
        "screenshots_read": False,
        "ocr_used": False,
        "save_files_read": False,
        "current_line_capture_used": False,
        "ui_text_reading_used": False,
        "unity_scanning_used": False,
        "hooks_used": False,
        "decompiled_code_used": False,
        "provider_called": False,
        "companion_contract_changed": False,
    }


def _write_private_db(private_db: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(private_db, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _compatible_payload(private_marker: str) -> dict[str, Any]:
    return {
        "schema_version": FUTURE_PROFILE_SCHEMA_VERSION,
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


def _finalize(summary: dict[str, Any]) -> dict[str, Any]:
    summary["blocker_categories"] = list(dict.fromkeys(summary["blocker_categories"]))
    if summary["blocker_categories"] and summary["import_status"] != "decode_failed":
        summary["import_status"] = "incompatible"
    return summary


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "input_exists": False,
        "input_kind": "missing",
        "json_object_decoded": False,
        "profile_schema_version_matches": False,
        "records_count": 0,
        "context_edges_count": 0,
        "import_status": "incompatible",
        "blocker_categories": [],
        "private_db_output_written": False,
        "private_db_schema_version": PRIVATE_DB_SCHEMA_VERSION,
        "m2_import_locally_extracted_db_implemented": False,
        "m2_import_locally_extracted_db_done": False,
        "self_edge_count": 0,
        "duplicate_edge_count": 0,
        "ready_for_line_index_contract": False,
        "private_paths_included": False,
        "filenames_included": False,
        "record_values_in_stdout": False,
        "edge_values_in_stdout": False,
        "metadata_values_in_stdout": False,
        "source_text_in_stdout": False,
        "hashes_computed": False,
        "content_hashing_used": False,
        "path_string_hashing_used": False,
        "filename_hashing_used": False,
        "line_index_constructed": False,
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
        "automatic_game_install_scanning": False,
        "recursive_discovery_used": False,
        "game_files_read": False,
        "bepinex_logs_read": False,
        "screenshots_read": False,
        "ocr_used": False,
        "save_files_read": False,
        "current_line_capture_used": False,
        "ui_text_reading_used": False,
        "unity_scanning_used": False,
        "hooks_used": False,
        "decompiled_code_used": False,
        "provider_called": False,
        "companion_contract_changed": False,
        "raw_payloads_included": False,
        "raw_logs_included": False,
        "runtime_evidence_included": False,
    }


if __name__ == "__main__":
    sys.exit(main())
