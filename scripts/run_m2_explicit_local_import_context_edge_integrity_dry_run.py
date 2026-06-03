from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_m2_explicit_local_import_context_edge_integrity_contract import (
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
    )
    from scripts.run_m2_explicit_local_import_context_edge_reference_dry_run import (
        _context_edges_shape_is_compatible,
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
    from check_m2_explicit_local_import_context_edge_integrity_contract import (
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
    )
    from run_m2_explicit_local_import_context_edge_reference_dry_run import (
        _context_edges_shape_is_compatible,
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


SUMMARY_SCHEMA_VERSION = "m2-explicit-local-import-context-edge-integrity-dry-run-summary.v1"
PRIVATE_OUTPUT_ROOT = ALLOWED_PRIVATE_OUTPUT_ROOTS[0]


class M2ExplicitLocalImportContextEdgeIntegrityDryRunError(RuntimeError):
    """Raised when an M2 context-edge integrity dry-run request is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Count aggregate context-edge self-edge and duplicate-tuple integrity blockers "
            "in one explicit workspace-private JSON export. This M2 dry-run never emits ids."
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
            "Optional JSON output under "
            "workspace/local-private/extraction-indexing/import/context-edge-integrity/."
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
                print("M2 explicit local-import context-edge integrity dry-run self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": (
                                "m2-explicit-local-import-context-edge-integrity-dry-run-"
                                "self-test.v1"
                            ),
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0

        if args.input is None:
            parser.error("--input is required unless --self-test is used.")

        summary = build_m2_explicit_local_import_context_edge_integrity_dry_run(
            args.input,
            root=ROOT,
        )
        if args.output:
            output_path = resolve_output_path(args.output, root=ROOT)
            summary["output_written"] = True
            write_summary(summary, output_path)

        if args.quiet:
            print("M2 explicit local-import context-edge integrity dry-run passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (
        M2ExplicitLocalImportContextEdgeIntegrityDryRunError,
        OSError,
        PrivateInputAdapterDryRunError,
        ValueError,
    ) as exc:
        parser.error(str(exc))
    return 0


def build_m2_explicit_local_import_context_edge_integrity_dry_run(
    input_path: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    resolved_input = resolve_input_path(input_path, root=root)
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
        summary["context_edge_integrity_status"] = "decode_failed"
        summary["blocker_categories"].append("json_decode_failed")
        return summary

    if not isinstance(payload, dict):
        summary["blocker_categories"].append("top_level_json_object_required")
        return summary

    context_edges = payload.get("context_edges")
    if isinstance(context_edges, list):
        summary["context_edges_count"] = len(context_edges)

    if not _envelope_is_compatible(payload, summary):
        return _finalize(summary)
    summary["envelope_compatible"] = True

    if not _records_shape_is_compatible(payload, summary):
        return _finalize(summary)
    summary["records_shape_reviewed"] = True

    if not _context_edges_shape_is_compatible(payload, summary):
        return _finalize(summary)
    summary["context_edges_shape_reviewed"] = True

    record_ids = _top_level_record_ids(payload, summary)
    if record_ids is None:
        return _finalize(summary)

    if not _context_edge_references_are_compatible(context_edges, record_ids, summary):
        return _finalize(summary)
    summary["context_edge_references_reviewed"] = True

    _count_integrity_blockers(context_edges, summary)
    summary["all_context_edges_integrity_compatible"] = (
        summary["self_edge_count"] == 0 and summary["duplicate_edge_count"] == 0
    )
    if summary["all_context_edges_integrity_compatible"]:
        summary["context_edge_integrity_status"] = "compatible"
    else:
        if summary["self_edge_count"]:
            summary["blocker_categories"].append("self_edges_found")
        if summary["duplicate_edge_count"]:
            summary["blocker_categories"].append("duplicate_edges_found")
    return _finalize(summary)


def resolve_output_path(output_path: Path, *, root: Path = ROOT) -> Path:
    try:
        resolved = resolve_private_output_path(output_path, root=root)
        output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
        resolved.relative_to(output_root)
    except (PrivateInputAdapterDryRunError, ValueError) as exc:
        raise M2ExplicitLocalImportContextEdgeIntegrityDryRunError(
            "Unsafe output path. Use a JSON path under "
            "workspace/local-private/extraction-indexing/import/context-edge-integrity/."
        ) from exc

    if resolved.suffix.lower() != ".json":
        raise M2ExplicitLocalImportContextEdgeIntegrityDryRunError(
            "Output path must use the .json suffix."
        )
    return resolved


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        private_marker = "PRIVATE_CONTEXT_EDGE_INTEGRITY_VALUE_SHOULD_NOT_APPEAR"
        private_file.write_text(
            json.dumps(_compatible_payload(private_marker)),
            encoding="utf-8",
        )

        summary = build_m2_explicit_local_import_context_edge_integrity_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if (
            summary["context_edge_integrity_status"] != "compatible"
            or summary["context_edges_count"] != 2
            or summary["self_edge_count"] != 0
            or summary["duplicate_edge_count"] != 0
        ):
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunError(
                "Self-test compatible context-edge integrity summary was incorrect."
            )
        if private_marker in rendered or str(root) in rendered:
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunError(
                "Self-test summary leaked private edge integrity content or paths."
            )

        output = resolve_output_path(
            Path(PRIVATE_OUTPUT_ROOT) / "self-test-summary.json",
            root=root,
        )
        write_summary(summary, output)
        written = output.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunError(
                "Self-test written summary leaked private data."
            )

        blocked_payload = _compatible_payload(private_marker)
        blocked_payload["context_edges"] = [
            {
                "from_record_id": f"{private_marker}_A",
                "to_record_id": f"{private_marker}_A",
                "relation": "previous_visible",
            },
            {
                "from_record_id": f"{private_marker}_A",
                "to_record_id": f"{private_marker}_B",
                "relation": "nearby_branch",
            },
            {
                "from_record_id": f"{private_marker}_A",
                "to_record_id": f"{private_marker}_B",
                "relation": "nearby_branch",
            },
        ]
        blocked_file = root / PRIVATE_INPUT_ROOT / "blocked.json"
        blocked_file.write_text(json.dumps(blocked_payload), encoding="utf-8")
        blocked = build_m2_explicit_local_import_context_edge_integrity_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "blocked.json",
            root=root,
        )
        if (
            blocked["context_edge_integrity_status"] != "incompatible"
            or blocked["self_edge_count"] != 1
            or blocked["duplicate_edge_count"] != 1
        ):
            raise M2ExplicitLocalImportContextEdgeIntegrityDryRunError(
                "Self-test failed to redact context-edge integrity blockers."
            )


def _context_edge_references_are_compatible(
    context_edges: list[Any],
    record_ids: set[str],
    summary: dict[str, Any],
) -> bool:
    compatible = True
    for edge in context_edges:
        if edge["from_record_id"] not in record_ids or edge["to_record_id"] not in record_ids:
            compatible = False
    if not compatible:
        summary["blocker_categories"].append("context_edge_reference_precondition_failed")
    return compatible


def _count_integrity_blockers(context_edges: list[Any], summary: dict[str, Any]) -> None:
    seen_edges: set[tuple[str, str, str]] = set()
    for edge in context_edges:
        if edge["from_record_id"] == edge["to_record_id"]:
            summary["self_edge_count"] += 1
        edge_tuple = (edge["from_record_id"], edge["to_record_id"], edge["relation"])
        if edge_tuple in seen_edges:
            summary["duplicate_edge_count"] += 1
        else:
            seen_edges.add(edge_tuple)


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
                "redacted_metadata": {"nested": private_marker},
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
                "redacted_metadata": {"nested": private_marker},
            },
        ],
        "context_edges": [
            {
                "from_record_id": f"{private_marker}_A",
                "to_record_id": f"{private_marker}_B",
                "relation": "previous_visible",
            },
            {
                "from_record_id": f"{private_marker}_B",
                "to_record_id": f"{private_marker}_A",
                "relation": "nearby_branch",
            },
        ],
        "metadata": {"nested": private_marker},
    }


def _finalize(summary: dict[str, Any]) -> dict[str, Any]:
    summary["blocker_categories"] = list(dict.fromkeys(summary["blocker_categories"]))
    if (
        summary["blocker_categories"]
        and summary["context_edge_integrity_status"] != "decode_failed"
    ):
        summary["context_edge_integrity_status"] = "incompatible"
    return summary


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "input_exists": False,
        "input_kind": "missing",
        "envelope_compatible": False,
        "records_shape_reviewed": False,
        "context_edges_shape_reviewed": False,
        "context_edge_references_reviewed": False,
        "context_edges_count": 0,
        "self_edge_count": 0,
        "duplicate_edge_count": 0,
        "all_context_edges_integrity_compatible": False,
        "context_edge_integrity_status": "incompatible",
        "blocker_categories": [],
        "dry_run": True,
        "context_edge_integrity_aggregate_only": True,
        "decode_size_cap_applied": False,
        "output_written": False,
        "private_paths_included": False,
        "filenames_included": False,
        "record_ids_included": False,
        "record_ids_logged": False,
        "record_ids_normalized": False,
        "record_ids_hashed": False,
        "edge_ids_included": False,
        "edge_ids_logged": False,
        "edge_ids_normalized": False,
        "edge_ids_hashed": False,
        "relation_values_included": False,
        "relation_values_logged": False,
        "relation_values_normalized": False,
        "duplicate_tuples_included": False,
        "duplicate_tuples_logged": False,
        "duplicate_tuples_normalized": False,
        "duplicate_tuples_hashed": False,
        "retrieval_bucket_mapping_used": False,
        "record_values_inspected": False,
        "record_values_included": False,
        "record_values_logged": False,
        "record_values_compared": False,
        "record_values_normalized": False,
        "context_tags_contents_traversed": False,
        "metadata_contents_traversed": False,
        "source_text_included": False,
        "hashes_computed": False,
        "real_db_imported": False,
        "line_index_constructed": False,
        "context_graph_constructed": False,
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
        "real_text_included": False,
        "raw_payloads_included": False,
        "raw_logs_included": False,
        "runtime_evidence_included": False,
    }


if __name__ == "__main__":
    sys.exit(main())
