from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_m2_explicit_local_import_record_shape_contract import (
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
        ALLOWED_RECORD_FIELDS,
        ALLOWED_RECORD_TYPES,
        FUTURE_PROFILE_SCHEMA_VERSION,
    )
    from scripts.check_m2_explicit_local_import_schema_compatibility_contract import (
        ALLOWED_ENVELOPE_FIELDS,
    )
    from scripts.run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_m2_explicit_local_import_record_shape_contract import (
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
        ALLOWED_RECORD_FIELDS,
        ALLOWED_RECORD_TYPES,
        FUTURE_PROFILE_SCHEMA_VERSION,
    )
    from check_m2_explicit_local_import_schema_compatibility_contract import (
        ALLOWED_ENVELOPE_FIELDS,
    )
    from run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "m2-explicit-local-import-record-shape-dry-run-summary.v1"
PRIVATE_OUTPUT_ROOT = ALLOWED_PRIVATE_OUTPUT_ROOTS[0]


class M2ExplicitLocalImportRecordShapeDryRunError(RuntimeError):
    """Raised when an M2 record-shape dry-run request is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect record keys and immediate value types in one explicit workspace-private "
            "JSON export. This M2 dry-run never emits or traverses private record values."
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
            "workspace/local-private/extraction-indexing/import/record-shape/."
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
                print("M2 explicit local-import record-shape dry-run self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": (
                                "m2-explicit-local-import-record-shape-dry-run-self-test.v1"
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

        summary = build_m2_explicit_local_import_record_shape_dry_run(args.input, root=ROOT)
        if args.output:
            output_path = resolve_output_path(args.output, root=ROOT)
            summary["output_written"] = True
            write_summary(summary, output_path)

        if args.quiet:
            print("M2 explicit local-import record-shape dry-run passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (
        M2ExplicitLocalImportRecordShapeDryRunError,
        OSError,
        PrivateInputAdapterDryRunError,
        ValueError,
    ) as exc:
        parser.error(str(exc))
    return 0


def build_m2_explicit_local_import_record_shape_dry_run(
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
        summary["record_shape_status"] = "decode_failed"
        summary["blocker_categories"].append("json_decode_failed")
        return summary

    if not isinstance(payload, dict):
        summary["blocker_categories"].append("top_level_json_object_required")
        return summary

    records = payload.get("records")
    summary["records_array_present"] = isinstance(records, list)
    if isinstance(records, list):
        summary["records_count"] = len(records)

    if not _envelope_is_compatible(payload, summary):
        return summary

    summary["envelope_compatible"] = True
    for record in records:
        summary["records_inspected_count"] += 1
        if _record_shape_is_compatible(record, summary):
            summary["compatible_record_count"] += 1
        else:
            summary["incompatible_record_count"] += 1

    summary["all_record_shapes_compatible"] = summary["incompatible_record_count"] == 0
    if summary["all_record_shapes_compatible"]:
        summary["record_shape_status"] = "compatible"
    summary["blocker_categories"] = _dedupe(summary["blocker_categories"])
    return summary


def resolve_output_path(output_path: Path, *, root: Path = ROOT) -> Path:
    try:
        resolved = resolve_private_output_path(output_path, root=root)
        output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
        resolved.relative_to(output_root)
    except (PrivateInputAdapterDryRunError, ValueError) as exc:
        raise M2ExplicitLocalImportRecordShapeDryRunError(
            "Unsafe output path. Use a JSON path under "
            "workspace/local-private/extraction-indexing/import/record-shape/."
        ) from exc

    if resolved.suffix.lower() != ".json":
        raise M2ExplicitLocalImportRecordShapeDryRunError("Output path must use the .json suffix.")
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
        private_marker = "PRIVATE_RECORD_VALUE_SHOULD_NOT_APPEAR"
        private_file.write_text(
            json.dumps(_compatible_payload(private_marker)),
            encoding="utf-8",
        )

        summary = build_m2_explicit_local_import_record_shape_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if (
            summary["record_shape_status"] != "compatible"
            or summary["records_count"] != 1
            or summary["records_inspected_count"] != 1
        ):
            raise M2ExplicitLocalImportRecordShapeDryRunError(
                "Self-test compatible record-shape summary was incorrect."
            )
        if private_marker in rendered or str(root) in rendered:
            raise M2ExplicitLocalImportRecordShapeDryRunError(
                "Self-test summary leaked private content or paths."
            )

        output = resolve_output_path(
            Path(PRIVATE_OUTPUT_ROOT) / "self-test-summary.json",
            root=root,
        )
        write_summary(summary, output)
        written = output.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M2ExplicitLocalImportRecordShapeDryRunError(
                "Self-test written summary leaked private data."
            )

        incompatible = _compatible_payload(private_marker)
        incompatible["records"] = [{"record_id": private_marker}]
        blocked_file = root / PRIVATE_INPUT_ROOT / "incompatible.json"
        blocked_file.write_text(json.dumps(incompatible), encoding="utf-8")
        blocked = build_m2_explicit_local_import_record_shape_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "incompatible.json",
            root=root,
        )
        if blocked["record_shape_status"] != "incompatible":
            raise M2ExplicitLocalImportRecordShapeDryRunError(
                "Self-test failed to redact an incompatible record shape."
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
    summary["blocker_categories"] = _dedupe(summary["blocker_categories"])
    return compatible


def _record_shape_is_compatible(record: Any, summary: dict[str, Any]) -> bool:
    if not isinstance(record, dict):
        summary["blocker_categories"].append("record_object_required")
        return False
    compatible = True
    if set(record) != set(ALLOWED_RECORD_FIELDS):
        summary["blocker_categories"].append("record_fields_mismatch")
        compatible = False
    for field, expected_type in ALLOWED_RECORD_TYPES.items():
        if field not in record or not _matches_type(record[field], expected_type):
            summary["blocker_categories"].append("record_types_mismatch")
            compatible = False
            break
    return compatible


def _matches_type(value: Any, expected_type: str) -> bool:
    return {
        "string": isinstance(value, str),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }[expected_type]


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
        "context_edges": [{"nested": private_marker}],
        "metadata": {"nested": private_marker},
    }


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "input_exists": False,
        "input_kind": "missing",
        "envelope_compatible": False,
        "records_array_present": False,
        "records_count": 0,
        "records_inspected_count": 0,
        "compatible_record_count": 0,
        "incompatible_record_count": 0,
        "all_record_shapes_compatible": False,
        "record_shape_status": "incompatible",
        "blocker_categories": [],
        "dry_run": True,
        "record_shape_only": True,
        "decode_size_cap_applied": False,
        "output_written": False,
        "private_paths_included": False,
        "filenames_included": False,
        "record_values_inspected": False,
        "record_values_included": False,
        "record_values_logged": False,
        "record_values_compared": False,
        "record_values_normalized": False,
        "context_tags_contents_traversed": False,
        "metadata_contents_traversed": False,
        "context_edges_traversed": False,
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
