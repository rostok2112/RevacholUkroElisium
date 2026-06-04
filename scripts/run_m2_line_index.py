from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_m2_line_index_contract import (
        LINE_INDEX_SCHEMA_VERSION,
        PRIVATE_DB_SCHEMA_VERSION,
    )
    from scripts.review_m2_local_import import (
        REVIEW_SCHEMA_VERSION as LOCAL_IMPORT_REVIEW_SCHEMA_VERSION,
        build_review,
    )
    from scripts.run_m2_local_import import (
        PRIVATE_INPUT_ROOT,
        run_m2_local_import,
        write_summary,
    )
    from scripts.run_private_input_adapter_dry_run import (
        PrivateInputAdapterDryRunError,
        resolve_output_path as resolve_private_output_path,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_m2_line_index_contract import (
        LINE_INDEX_SCHEMA_VERSION,
        PRIVATE_DB_SCHEMA_VERSION,
    )
    from review_m2_local_import import (
        REVIEW_SCHEMA_VERSION as LOCAL_IMPORT_REVIEW_SCHEMA_VERSION,
        build_review,
    )
    from run_m2_local_import import (
        PRIVATE_INPUT_ROOT,
        run_m2_local_import,
        write_summary,
    )
    from run_private_input_adapter_dry_run import (
        PrivateInputAdapterDryRunError,
        resolve_output_path as resolve_private_output_path,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "m2-line-index-summary.v1"
PRIVATE_DB_ROOT = "workspace/local-private/extraction-indexing/import/db/"
LOCAL_IMPORT_REVIEW_ROOT = "workspace/local-private/extraction-indexing/import/db-review/"
PRIVATE_LINE_INDEX_ROOT = "workspace/local-private/extraction-indexing/import/line-index/"


class M2LineIndexError(RuntimeError):
    """Raised when an M2 line-index request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build one ignored private M2 line-index artifact from one explicit private imported "
            "DB artifact. Stdout stays redacted."
        )
    )
    parser.add_argument("--input", type=Path, help="Private imported DB JSON under import/db/.")
    parser.add_argument(
        "--import-review",
        type=Path,
        help="Redacted local-import review JSON under import/db-review/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Required private line-index JSON output under import/line-index/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 line-index self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": "m2-line-index-self-test.v1",
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0
        if args.input is None or args.import_review is None or args.output is None:
            parser.error("--input, --import-review, and --output are required unless --self-test.")

        summary = run_m2_line_index(args.input, args.import_review, args.output, root=ROOT)
        if args.quiet:
            print("M2 line-index passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (M2LineIndexError, OSError, PrivateInputAdapterDryRunError, ValueError) as exc:
        parser.error(str(exc))
    return 0


def run_m2_line_index(
    input_path: Path,
    import_review_path: Path,
    output_path: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    resolved_input = resolve_private_db_input_path(input_path, root=root)
    resolved_review = resolve_import_review_input_path(import_review_path, root=root)
    resolved_output = resolve_line_index_output_path(output_path, root=root)
    summary = _base_summary()
    summary["input_exists"] = resolved_input.exists()

    review = load_json(resolved_review)
    if not _review_is_ready(review):
        summary["blocker_categories"].append("local_import_review_not_ready")
        return _finalize(summary)

    if _raw_path(input_path, root=root).is_symlink():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("symlink_input_rejected")
        return _finalize(summary)
    if not resolved_input.exists():
        summary["input_kind"] = "missing"
        summary["blocker_categories"].append("input_missing")
        return _finalize(summary)
    if resolved_input.is_dir():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("directory_input_rejected")
        return _finalize(summary)
    if not resolved_input.is_file():
        summary["input_kind"] = "unsupported"
        summary["blocker_categories"].append("unsupported_input_kind")
        return _finalize(summary)

    summary["input_kind"] = "file"
    try:
        private_db = load_json(resolved_input)
    except Exception:
        summary["line_index_status"] = "decode_failed"
        summary["blocker_categories"].append("json_decode_failed")
        return summary

    if not isinstance(private_db, dict):
        summary["blocker_categories"].append("private_db_json_object_required")
        return _finalize(summary)
    if private_db.get("schema_version") == PRIVATE_DB_SCHEMA_VERSION:
        summary["private_db_schema_version_matches"] = True
    records = private_db.get("records")
    if isinstance(records, list):
        summary["records_count"] = len(records)

    if not _private_db_is_compatible(private_db, summary):
        return _finalize(summary)

    line_index = build_m2_line_index(private_db)
    write_line_index(line_index, resolved_output)
    summary.update(
        {
            "line_index_entry_count": len(line_index["entries"]),
            "line_index_output_written": True,
            "line_index_status": "built",
            "m2_line_index_done": True,
            "ready_for_context_graph_contract": True,
        }
    )
    return _finalize(summary)


def build_m2_line_index(private_db: dict[str, Any]) -> dict[str, Any]:
    entries = [
        {
            "record_id": record["record_id"],
            "line_id": record["line_id"],
            "conversation_id": record["conversation_id"],
            "speaker_id": record["speaker_id"],
            "context_placeholder": record["context_placeholder"],
            "source_text": record["source_text"],
            "context_tags": list(record["context_tags"]),
            "redacted_metadata": record["redacted_metadata"],
        }
        for record in private_db["records"]
    ]
    entries.sort(key=lambda entry: (entry["line_id"], entry["record_id"]))
    return {
        "schema_version": LINE_INDEX_SCHEMA_VERSION,
        "source_schema_version": PRIVATE_DB_SCHEMA_VERSION,
        "source_kind": private_db["source_kind"],
        "entries": entries,
        "metadata": private_db["metadata"],
        "line_index_constructed": True,
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
        "automatic_game_install_scanning": False,
        "provider_called": False,
        "companion_contract_changed": False,
    }


def resolve_private_db_input_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_private_path(
        path,
        root=root,
        allowed_root=PRIVATE_DB_ROOT,
        label="input DB",
        must_exist=False,
    )


def resolve_import_review_input_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_private_path(
        path,
        root=root,
        allowed_root=LOCAL_IMPORT_REVIEW_ROOT,
        label="local import review",
    )


def resolve_line_index_output_path(path: Path, *, root: Path = ROOT) -> Path:
    resolved = _resolve_private_path(
        path,
        root=root,
        allowed_root=PRIVATE_LINE_INDEX_ROOT,
        label="line-index output",
        must_exist=False,
    )
    if resolved.suffix.lower() != ".json":
        raise M2LineIndexError("Line-index output path must use the .json suffix.")
    return resolved


def write_line_index(line_index: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(line_index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_marker = "PRIVATE_LINE_INDEX_VALUE_SHOULD_NOT_APPEAR"
        private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
        private_file.parent.mkdir(parents=True)
        private_file.write_text(json.dumps(_compatible_export(private_marker)), encoding="utf-8")

        db_path = Path(PRIVATE_DB_ROOT) / "imported-db.json"
        import_summary = run_m2_local_import(
            Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
            db_path,
            root=root,
        )
        summary_path = (
            root / "workspace/local-private/extraction-indexing/import/db-summary/summary.json"
        )
        write_summary(import_summary, summary_path)
        review = build_review(import_summary, summary_path=summary_path, root=root)
        review_path = root / LOCAL_IMPORT_REVIEW_ROOT / "review.json"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")

        output_path = Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json"
        summary = run_m2_line_index(
            db_path,
            Path(LOCAL_IMPORT_REVIEW_ROOT) / "review.json",
            output_path,
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if (
            summary["line_index_status"] != "built"
            or summary["records_count"] != 2
            or summary["line_index_entry_count"] != 2
            or not summary["line_index_output_written"]
        ):
            raise M2LineIndexError("Self-test line-index summary was incorrect.")
        if private_marker in rendered or str(root) in rendered:
            raise M2LineIndexError("Self-test summary leaked private line-index content or paths.")
        line_index = load_json(root / output_path)
        written = json.dumps(line_index, sort_keys=True)
        if private_marker not in written:
            raise M2LineIndexError("Self-test line-index did not preserve private content.")
        if line_index["context_graph_constructed"] or line_index["retrieval_bucket_mapping_used"]:
            raise M2LineIndexError(
                "Self-test line-index must not build graph or retrieval mapping."
            )


def _private_db_is_compatible(private_db: dict[str, Any], summary: dict[str, Any]) -> bool:
    compatible = True
    if private_db.get("schema_version") != PRIVATE_DB_SCHEMA_VERSION:
        summary["blocker_categories"].append("private_db_schema_version_mismatch")
        compatible = False
    if not isinstance(private_db.get("source_schema_version"), str):
        summary["blocker_categories"].append("source_schema_version_required")
        compatible = False
    if not isinstance(private_db.get("source_kind"), str):
        summary["blocker_categories"].append("source_kind_type_mismatch")
        compatible = False
    records = private_db.get("records")
    if not isinstance(records, list):
        summary["blocker_categories"].append("records_array_required")
        compatible = False
    else:
        for record in records:
            if not _record_is_compatible(record):
                summary["blocker_categories"].append("record_shape_mismatch")
                compatible = False
                break
    if private_db.get("line_index_constructed") is not False:
        summary["blocker_categories"].append("source_line_index_already_constructed")
        compatible = False
    if private_db.get("context_graph_constructed") is not False:
        summary["blocker_categories"].append("context_graph_already_constructed")
        compatible = False
    return compatible


def _record_is_compatible(record: Any) -> bool:
    if not isinstance(record, dict):
        return False
    expected = {
        "record_id": str,
        "line_id": str,
        "conversation_id": str,
        "speaker_id": str,
        "speaker_label": str,
        "context_placeholder": str,
        "source_text": str,
        "context_tags": list,
        "redacted_metadata": dict,
    }
    return all(
        field in record and isinstance(record[field], kind) for field, kind in expected.items()
    )


def _review_is_ready(review: Any) -> bool:
    return (
        isinstance(review, dict)
        and review.get("schema_version") == LOCAL_IMPORT_REVIEW_SCHEMA_VERSION
        and review.get("summary_valid") is True
        and review.get("ready_for_line_index_implementation") is True
        and review.get("line_index_construction_allowed_next") is True
        and review.get("context_graph_construction_allowed_next") is False
        and review.get("retrieval_bucket_mapping_allowed_next") is False
        and review.get("blockers") == []
    )


def _resolve_private_path(
    path: Path,
    *,
    root: Path,
    allowed_root: str,
    label: str,
    must_exist: bool = True,
) -> Path:
    _reject_unsafe_path_text(path)
    try:
        resolved = resolve_private_output_path(path, root=root)
        base = (root / allowed_root).resolve(strict=False)
        resolved.relative_to(base)
    except (PrivateInputAdapterDryRunError, ValueError) as exc:
        raise M2LineIndexError(f"Unsafe {label} path. Use {allowed_root}.") from exc
    if must_exist and not resolved.exists():
        raise M2LineIndexError(f"M2 {label} path must point to an existing file.")
    if must_exist and not resolved.is_file():
        raise M2LineIndexError(f"M2 {label} path must point to a file.")
    if _raw_path(path, root=root).is_symlink():
        raise M2LineIndexError(f"M2 {label} path must not be a symlink.")
    return resolved


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise M2LineIndexError("Unsafe path traversal is not allowed.")
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
            raise M2LineIndexError("Path uses a forbidden runtime/private marker.")


def _raw_path(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute():
        return raw
    return root / raw


def _finalize(summary: dict[str, Any]) -> dict[str, Any]:
    summary["blocker_categories"] = list(dict.fromkeys(summary["blocker_categories"]))
    if summary["blocker_categories"] and summary["line_index_status"] != "decode_failed":
        summary["line_index_status"] = "incompatible"
    return summary


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "input_exists": False,
        "input_kind": "missing",
        "private_db_schema_version_matches": False,
        "records_count": 0,
        "line_index_entry_count": 0,
        "line_index_output_written": False,
        "line_index_status": "incompatible",
        "blocker_categories": [],
        "m2_line_index_done": False,
        "ready_for_context_graph_contract": False,
        "private_paths_included": False,
        "filenames_included": False,
        "record_ids_in_stdout": False,
        "line_ids_in_stdout": False,
        "record_values_in_stdout": False,
        "source_text_in_stdout": False,
        "hashes_computed": False,
        "content_hashing_used": False,
        "path_string_hashing_used": False,
        "filename_hashing_used": False,
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


def _compatible_export(private_marker: str) -> dict[str, Any]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            _compatible_record(f"{private_marker}_B", private_marker),
            _compatible_record(f"{private_marker}_A", private_marker),
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
    suffix = record_id.rsplit("_", maxsplit=1)[-1]
    return {
        "record_id": record_id,
        "line_id": f"{private_marker}_line_{suffix}",
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
