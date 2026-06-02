from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_m2_explicit_local_import_schema_compatibility_contract import (
        ALLOWED_ENVELOPE_FIELDS,
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
        FUTURE_PROFILE_SCHEMA_VERSION,
    )
    from scripts.run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_m2_explicit_local_import_schema_compatibility_contract import (
        ALLOWED_ENVELOPE_FIELDS,
        ALLOWED_PRIVATE_OUTPUT_ROOTS,
        FUTURE_PROFILE_SCHEMA_VERSION,
    )
    from run_private_input_adapter_dry_run import (
        PRIVATE_INPUT_ROOT,
        PrivateInputAdapterDryRunError,
        resolve_input_path,
        resolve_output_path as resolve_private_output_path,
    )
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "m2-explicit-local-import-schema-compatibility-dry-run-summary.v1"
PRIVATE_OUTPUT_ROOT = ALLOWED_PRIVATE_OUTPUT_ROOTS[0]


class M2ExplicitLocalImportSchemaCompatibilityDryRunError(RuntimeError):
    """Raised when an M2 schema-compatibility dry-run request is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect only the top-level envelope of one explicit workspace-private JSON export. "
            "This M2 dry-run never traverses or emits nested values."
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
            "workspace/local-private/extraction-indexing/import/schema-compatibility/."
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
                print("M2 explicit local-import schema-compatibility dry-run self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": (
                                "m2-explicit-local-import-schema-compatibility-dry-run-self-test.v1"
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

        summary = build_m2_explicit_local_import_schema_compatibility_dry_run(
            args.input,
            root=ROOT,
        )
        if args.output:
            output_path = resolve_output_path(args.output, root=ROOT)
            summary["output_written"] = True
            write_summary(summary, output_path)

        if args.quiet:
            print("M2 explicit local-import schema-compatibility dry-run passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (
        M2ExplicitLocalImportSchemaCompatibilityDryRunError,
        OSError,
        PrivateInputAdapterDryRunError,
        ValueError,
    ) as exc:
        parser.error(str(exc))
    return 0


def build_m2_explicit_local_import_schema_compatibility_dry_run(
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
        summary["schema_status"] = "decode_failed"
        summary["blocker_categories"].append("json_decode_failed")
        return summary

    summary["json_object_decoded"] = isinstance(payload, dict)
    if not isinstance(payload, dict):
        summary["blocker_categories"].append("top_level_json_object_required")
        return summary

    expected_fields = set(ALLOWED_ENVELOPE_FIELDS)
    actual_fields = set(payload)
    summary["required_envelope_fields_present"] = expected_fields.issubset(actual_fields)
    if not summary["required_envelope_fields_present"]:
        summary["blocker_categories"].append("required_envelope_fields_missing")
    if actual_fields != expected_fields:
        summary["blocker_categories"].append("unexpected_top_level_envelope_fields")

    summary["profile_schema_version_matches"] = (
        payload.get("schema_version") == FUTURE_PROFILE_SCHEMA_VERSION
    )
    if not summary["profile_schema_version_matches"]:
        summary["blocker_categories"].append("profile_schema_version_mismatch")

    records = payload.get("records")
    context_edges = payload.get("context_edges")
    summary["required_envelope_types_match"] = (
        isinstance(payload.get("schema_version"), str)
        and isinstance(payload.get("source_kind"), str)
        and isinstance(records, list)
        and isinstance(context_edges, list)
        and isinstance(payload.get("metadata"), dict)
    )
    if not summary["required_envelope_types_match"]:
        summary["blocker_categories"].append("required_envelope_types_mismatch")

    if isinstance(records, list):
        summary["records_count"] = len(records)
    if isinstance(context_edges, list):
        summary["context_edges_count"] = len(context_edges)

    if not summary["blocker_categories"]:
        summary["schema_status"] = "compatible"
    return summary


def resolve_output_path(output_path: Path, *, root: Path = ROOT) -> Path:
    try:
        resolved = resolve_private_output_path(output_path, root=root)
        output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
        resolved.relative_to(output_root)
    except (PrivateInputAdapterDryRunError, ValueError) as exc:
        raise M2ExplicitLocalImportSchemaCompatibilityDryRunError(
            "Unsafe output path. Use a JSON path under "
            "workspace/local-private/extraction-indexing/import/schema-compatibility/."
        ) from exc

    if resolved.suffix.lower() != ".json":
        raise M2ExplicitLocalImportSchemaCompatibilityDryRunError(
            "Output path must use the .json suffix."
        )
    return resolved


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _input_path_without_symlink_resolution(input_path: Path, *, root: Path) -> Path:
    raw = input_path.expanduser()
    if raw.is_absolute():
        return raw
    return root / raw


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        private_marker = "PRIVATE_NESTED_CONTENT_SHOULD_NOT_APPEAR"
        private_file.write_text(
            json.dumps(
                {
                    "schema_version": FUTURE_PROFILE_SCHEMA_VERSION,
                    "source_kind": "private_export",
                    "records": [{"source_text": private_marker}],
                    "context_edges": [{"nested_marker": private_marker}],
                    "metadata": {"nested_marker": private_marker},
                }
            ),
            encoding="utf-8",
        )

        summary = build_m2_explicit_local_import_schema_compatibility_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if (
            summary["schema_status"] != "compatible"
            or summary["records_count"] != 1
            or summary["context_edges_count"] != 1
        ):
            raise M2ExplicitLocalImportSchemaCompatibilityDryRunError(
                "Self-test compatible envelope summary was incorrect."
            )
        if private_marker in rendered or str(root) in rendered:
            raise M2ExplicitLocalImportSchemaCompatibilityDryRunError(
                "Self-test summary leaked nested private content or paths."
            )

        output = resolve_output_path(
            Path(PRIVATE_OUTPUT_ROOT) / "self-test-summary.json",
            root=root,
        )
        write_summary(summary, output)
        written = output.read_text(encoding="utf-8")
        if private_marker in written or str(root) in written:
            raise M2ExplicitLocalImportSchemaCompatibilityDryRunError(
                "Self-test written summary leaked private data."
            )

        malformed = root / PRIVATE_INPUT_ROOT / "malformed.json"
        malformed.write_text("{", encoding="utf-8")
        blocked = build_m2_explicit_local_import_schema_compatibility_dry_run(
            Path(PRIVATE_INPUT_ROOT) / "malformed.json",
            root=root,
        )
        if blocked["schema_status"] != "decode_failed":
            raise M2ExplicitLocalImportSchemaCompatibilityDryRunError(
                "Self-test failed to redact a malformed JSON blocker."
            )


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "input_exists": False,
        "input_kind": "missing",
        "json_object_decoded": False,
        "profile_schema_version_matches": False,
        "required_envelope_fields_present": False,
        "required_envelope_types_match": False,
        "records_count": 0,
        "context_edges_count": 0,
        "schema_status": "incompatible",
        "blocker_categories": [],
        "dry_run": True,
        "envelope_only": True,
        "decode_size_cap_applied": False,
        "output_written": False,
        "private_paths_included": False,
        "filenames_included": False,
        "nested_values_traversed": False,
        "nested_values_included": False,
        "source_text_included": False,
        "metadata_contents_inspected": False,
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
