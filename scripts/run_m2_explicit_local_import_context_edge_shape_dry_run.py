from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_m2_explicit_local_import_context_edge_shape_contract import (
        ALLOWED_CONTEXT_EDGE_FIELDS,
        ALLOWED_CONTEXT_EDGE_TYPES,
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
        ALLOWED_RELATION_VALUES,
        FUTURE_PROFILE_SCHEMA_VERSION,
    )
    from scripts.check_m2_explicit_local_import_schema_compatibility_contract import (
        ALLOWED_ENVELOPE_FIELDS,
    )
    from scripts.run_m2_explicit_local_import_record_shape_dry_run import (
        _record_shape_is_compatible,
    )
    from scripts.run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_m2_explicit_local_import_context_edge_shape_contract import (
        ALLOWED_CONTEXT_EDGE_FIELDS,
        ALLOWED_CONTEXT_EDGE_TYPES,
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
        ALLOWED_RELATION_VALUES,
        FUTURE_PROFILE_SCHEMA_VERSION,
    )
    from check_m2_explicit_local_import_schema_compatibility_contract import (
        ALLOWED_ENVELOPE_FIELDS,
    )
    from run_m2_explicit_local_import_record_shape_dry_run import (
        _record_shape_is_compatible,
    )
    from run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "m2-explicit-local-import-context-edge-shape-dry-run-summary.v1"
PRIVATE_OUTPUT_ROOT = ALLOWED_PRIVATE_OUTPUT_ROOTS[0]


class M2ExplicitLocalImportContextEdgeShapeDryRunError(RuntimeError):
    """Raised when an M2 context-edge shape dry-run request is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect context-edge keys, immediate value types, and relation vocabulary in one "
            "explicit workspace-private JSON export. This M2 dry-run never emits edge values."
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
            "workspace/local-private/extraction-indexing/import/context-edge-shape/."
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
                print("M2 explicit local-import context-edge shape dry-run self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": (
                                "m2-explicit-local-import-context-edge-shape-dry-run-self-test.v1"
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

        summary = build_m2_explicit_local_import_context_edge_shape_dry_run(
            args.input,
            root=ROOT,
        )
        if args.output:
            output_path = resolve_output_path(args.output, root=ROOT)
            summary["output_written"] = True
            write_summary(summary, output_path)

        if args.quiet:
            print("M2 explicit local-import context-edge shape dry-run passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (
        M2ExplicitLocalImportContextEdgeShapeDryRunError,
        OSError,
        PrivateInputAdapterDryRunError,
        ValueError,
    ) as exc:
        parser.error(str(exc))
    return 0


def build_m2_explicit_local_import_context_edge_shape_dry_run(
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
        summary["context_edge_shape_status"] = "decode_failed"
        summary["blocker_categories"].append("json_decode_failed")
        return summary

    if not isinstance(payload, dict):
        summary["blocker_categories"].append("top_level_json_object_required")
        return summary

    context_edges = payload.get("context_edges")
    summary["context_edges_array_present"] = isinstance(context_edges, list)
    if isinstance(context_edges, list):
        summary["context_edges_count"] = len(context_edges)

    if not _envelope_is_compatible(payload, summary):
        return _finalize(summary)
    summary["envelope_compatible"] = True

    if not _records_shape_is_compatible(payload, summary):
        return _finalize(summary)
    summary["records_shape_reviewed"] = True

    for edge in context_edges:
        summary["context_edges_inspected_count"] += 1
        if _context_edge_shape_is_compatible(edge, summary):
            summary["compatible_context_edge_count"] += 1
        else:
            summary["incompatible_context_edge_count"] += 1

    summary["all_context_edge_shapes_compatible"] = summary["incompatible_context_edge_count"] == 0
    if summary["all_context_edge_shapes_compatible"]:
        summary["context_edge_shape_status"] = "compatible"
    return _finalize(summary)


def resolve_output_path(output_path: Path, *, root: Path = ROOT) -> Path:
    try:
        resolved = resolve_private_output_path(output_path, root=root)
        output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
        resolved.relative_to(output_root)
    except (PrivateInputAdapterDryRunError, ValueError) as exc:
        raise M2ExplicitLocalImportContextEdgeShapeDryRunError(
            "Unsafe output path. Use a JSON path under "
            "workspace/local-private/extraction-indexing/import/context-edge-shape/."
        ) from exc

    if resolved.suffix.lower() != ".json":
        raise M2ExplicitLocalImportContextEdgeShapeDryRunError(
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
        private_marker = "PRIVATE_CONTEXT_EDGE_VALUE_SHOULD_NOT_APPEAR"
        private_file.write_text(
            json.dumps(_compatible_payload(private_marker)),
            encoding="utf-8",
        )

        summary = build_m2_explicit_local_import_context_edge_shape_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if (
            summary["context_edge_shape_status"] != "compatible"
            or summary["context_edges_count"] != 3
            or summary["context_edges_inspected_count"] != 3
        ):
            raise M2ExplicitLocalImportContextEdgeShapeDryRunError(
                "Self-test compatible context-edge summary was incorrect."
            )
        if private_marker in rendered or str(root) in rendered:
            raise M2ExplicitLocalImportContextEdgeShapeDryRunError(
                "Self-test summary leaked private edge content or paths."
            )

        output = resolve_output_path(
            Path(PRIVATE_OUTPUT_ROOT) / "self-test-summary.json",
            root=root,
        )
        write_summary(summary, output)
        written = output.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M2ExplicitLocalImportContextEdgeShapeDryRunError(
                "Self-test written summary leaked private data."
            )

        incompatible = _compatible_payload(private_marker)
        incompatible["context_edges"] = [
            {
                "from_record_id": private_marker,
                "to_record_id": private_marker,
                "relation": "not_approved",
            }
        ]
        blocked_file = root / PRIVATE_INPUT_ROOT / "incompatible.json"
        blocked_file.write_text(json.dumps(incompatible), encoding="utf-8")
        blocked = build_m2_explicit_local_import_context_edge_shape_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "incompatible.json",
            root=root,
        )
        if blocked["context_edge_shape_status"] != "incompatible":
            raise M2ExplicitLocalImportContextEdgeShapeDryRunError(
                "Self-test failed to redact an incompatible context-edge shape."
            )


def _envelope_is_compatible(payload: dict[str, Any], summary: dict[str, Any]) -> bool:
    compatible = True
    if set(payload) != set(ALLOWED_ENVELOPE_FIELDS):
        summary["blocker_categories"].append("envelope_fields_mismatch")
        compatible = False
    if payload.get("schema_version") != FUTURE_PROFILE_SCHEMA_VERSION:
        summary["blocker_categories"].append("profile_schema_version_mismatch")
        compatible = False
    if not isinstance(payload.get("source_kind"), str):
        summary["blocker_categories"].append("source_kind_type_mismatch")
        compatible = False
    if not isinstance(payload.get("records"), list):
        summary["blocker_categories"].append("records_array_required")
        compatible = False
    if not isinstance(payload.get("context_edges"), list):
        summary["blocker_categories"].append("context_edges_array_required")
        compatible = False
    if not isinstance(payload.get("metadata"), dict):
        summary["blocker_categories"].append("metadata_object_required")
        compatible = False
    return compatible


def _records_shape_is_compatible(payload: dict[str, Any], summary: dict[str, Any]) -> bool:
    records = payload.get("records")
    if not isinstance(records, list):
        return False
    record_summary = {"blocker_categories": []}
    compatible = True
    for record in records:
        if not _record_shape_is_compatible(record, record_summary):
            compatible = False
    if not compatible:
        summary["blocker_categories"].append("record_shape_precondition_failed")
    return compatible


def _context_edge_shape_is_compatible(edge: Any, summary: dict[str, Any]) -> bool:
    if not isinstance(edge, dict):
        summary["blocker_categories"].append("context_edge_object_required")
        return False
    compatible = True
    if set(edge) != set(ALLOWED_CONTEXT_EDGE_FIELDS):
        summary["blocker_categories"].append("context_edge_fields_mismatch")
        compatible = False
    for field, expected_type in ALLOWED_CONTEXT_EDGE_TYPES.items():
        if field not in edge or not _matches_type(edge[field], expected_type):
            summary["blocker_categories"].append("context_edge_types_mismatch")
            compatible = False
            break
    if isinstance(edge.get("relation"), str) and edge["relation"] not in ALLOWED_RELATION_VALUES:
        summary["blocker_categories"].append("context_edge_relation_not_allowed")
        compatible = False
    return compatible


def _matches_type(value: Any, expected_type: str) -> bool:
    return {"string": isinstance(value, str)}[expected_type]


def _input_path_without_symlink_resolution(input_path: Path, *, root: Path) -> Path:
    raw = input_path.expanduser()
    if raw.is_absolute():
        return raw
    return root / raw


def _compatible_payload(private_marker: str) -> dict[str, Any]:
    return {
        "schema_version": FUTURE_PROFILE_SCHEMA_VERSION,
        "source_kind": "private_export",
        "records": [
            {
                "record_id": private_marker,
                "line_id": private_marker,
                "conversation_id": private_marker,
                "speaker_id": private_marker,
                "speaker_label": private_marker,
                "context_placeholder": private_marker,
                "source_text": private_marker,
                "context_tags": [private_marker],
                "redacted_metadata": {"nested": private_marker},
            }
        ],
        "context_edges": [
            {
                "from_record_id": private_marker,
                "to_record_id": private_marker,
                "relation": "previous_visible",
            },
            {
                "from_record_id": private_marker,
                "to_record_id": private_marker,
                "relation": "nearby_branch",
            },
            {
                "from_record_id": private_marker,
                "to_record_id": private_marker,
                "relation": "player_option",
            },
        ],
        "metadata": {"nested": private_marker},
    }


def _finalize(summary: dict[str, Any]) -> dict[str, Any]:
    summary["blocker_categories"] = list(dict.fromkeys(summary["blocker_categories"]))
    return summary


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "input_exists": False,
        "input_kind": "missing",
        "envelope_compatible": False,
        "records_shape_reviewed": False,
        "context_edges_array_present": False,
        "context_edges_count": 0,
        "context_edges_inspected_count": 0,
        "compatible_context_edge_count": 0,
        "incompatible_context_edge_count": 0,
        "all_context_edge_shapes_compatible": False,
        "context_edge_shape_status": "incompatible",
        "blocker_categories": [],
        "dry_run": True,
        "context_edge_shape_only": True,
        "decode_size_cap_applied": False,
        "output_written": False,
        "private_paths_included": False,
        "filenames_included": False,
        "context_edge_values_inspected": False,
        "context_edge_values_included": False,
        "context_edge_values_logged": False,
        "context_edge_values_normalized": False,
        "context_edge_values_compared": False,
        "context_edge_reference_validation_used": False,
        "self_edge_check_used": False,
        "duplicate_edge_check_used": False,
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
