from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.check_m2_context_graph_contract import (
        ALLOWED_RELATION_TO_BUCKET_MAPPINGS,
        CONTEXT_GRAPH_SCHEMA_VERSION,
        LINE_INDEX_SCHEMA_VERSION,
        PRIVATE_DB_SCHEMA_VERSION,
    )
    from scripts.review_m2_line_index import (
        REVIEW_SCHEMA_VERSION as LINE_INDEX_REVIEW_SCHEMA_VERSION,
        build_review as build_line_index_review,
    )
    from scripts.review_m2_local_import import build_review as build_local_import_review
    from scripts.run_m2_line_index import (
        LOCAL_IMPORT_REVIEW_ROOT,
        PRIVATE_DB_ROOT,
        PRIVATE_LINE_INDEX_ROOT,
        SUMMARY_OUTPUT_ROOT as LINE_INDEX_SUMMARY_ROOT,
        run_m2_line_index,
        write_summary as write_line_index_summary,
    )
    from scripts.run_m2_local_import import (
        PRIVATE_INPUT_ROOT,
        run_m2_local_import,
        write_summary as write_import_summary,
    )
    from scripts.run_private_input_adapter_dry_run import (
        PrivateInputAdapterDryRunError,
        resolve_output_path as resolve_private_output_path,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_m2_context_graph_contract import (
        ALLOWED_RELATION_TO_BUCKET_MAPPINGS,
        CONTEXT_GRAPH_SCHEMA_VERSION,
        LINE_INDEX_SCHEMA_VERSION,
        PRIVATE_DB_SCHEMA_VERSION,
    )
    from review_m2_line_index import (
        REVIEW_SCHEMA_VERSION as LINE_INDEX_REVIEW_SCHEMA_VERSION,
        build_review as build_line_index_review,
    )
    from review_m2_local_import import build_review as build_local_import_review
    from run_m2_line_index import (
        LOCAL_IMPORT_REVIEW_ROOT,
        PRIVATE_DB_ROOT,
        PRIVATE_LINE_INDEX_ROOT,
        SUMMARY_OUTPUT_ROOT as LINE_INDEX_SUMMARY_ROOT,
        run_m2_line_index,
        write_summary as write_line_index_summary,
    )
    from run_m2_local_import import (
        PRIVATE_INPUT_ROOT,
        run_m2_local_import,
        write_summary as write_import_summary,
    )
    from run_private_input_adapter_dry_run import (
        PrivateInputAdapterDryRunError,
        resolve_output_path as resolve_private_output_path,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


SUMMARY_SCHEMA_VERSION = "m2-context-graph-summary.v1"
PRIVATE_CONTEXT_GRAPH_ROOT = "workspace/local-private/extraction-indexing/import/context-graph/"
SUMMARY_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/import/context-graph-summary/"
LINE_INDEX_REVIEW_ROOT = "workspace/local-private/extraction-indexing/import/line-index-review/"
RELATION_TO_BUCKET = dict(
    item.split(":", maxsplit=1) for item in ALLOWED_RELATION_TO_BUCKET_MAPPINGS
)


class M2ContextGraphError(RuntimeError):
    """Raised when an M2 context-graph request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build one ignored private M2 context-graph artifact from one explicit private DB, "
            "one private line-index artifact, and one redacted line-index review."
        )
    )
    parser.add_argument("--db", type=Path, help="Private DB JSON under import/db/.")
    parser.add_argument(
        "--line-index", type=Path, help="Private line-index JSON under import/line-index/."
    )
    parser.add_argument(
        "--line-index-review",
        type=Path,
        help="Line-index review JSON under import/line-index-review/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Required private graph JSON output under import/context-graph/.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        help="Optional redacted summary JSON under import/context-graph-summary/.",
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("M2 context-graph self-test passed.")
            else:
                print(
                    json.dumps(
                        {
                            "ok": True,
                            "schema_version": "m2-context-graph-self-test.v1",
                            "real_private_inputs_required": False,
                        },
                        indent=2,
                        sort_keys=True,
                    )
                )
            return 0
        if (
            args.db is None
            or args.line_index is None
            or args.line_index_review is None
            or args.output is None
        ):
            parser.error(
                "--db, --line-index, --line-index-review, and --output are required unless --self-test."
            )

        summary = run_m2_context_graph(
            args.db,
            args.line_index,
            args.line_index_review,
            args.output,
            root=ROOT,
        )
        if args.summary_output:
            write_summary(
                summary,
                resolve_context_graph_summary_output_path(args.summary_output, root=ROOT),
            )
        if args.quiet:
            print("M2 context-graph passed.")
        else:
            print(json.dumps(summary, indent=2, sort_keys=True))
    except (M2ContextGraphError, OSError, PrivateInputAdapterDryRunError, ValueError) as exc:
        parser.error(str(exc))
    return 0


def run_m2_context_graph(
    db_path: Path,
    line_index_path: Path,
    line_index_review_path: Path,
    output_path: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    resolved_db = resolve_private_db_input_path(db_path, root=root)
    resolved_line_index = resolve_line_index_input_path(line_index_path, root=root)
    resolved_review = resolve_line_index_review_input_path(line_index_review_path, root=root)
    resolved_output = resolve_context_graph_output_path(output_path, root=root)
    summary = _base_summary()
    summary["db_input_exists"] = resolved_db.exists()
    summary["line_index_input_exists"] = resolved_line_index.exists()

    review = load_json(resolved_review)
    if not _line_index_review_is_ready(review):
        summary["blocker_categories"].append("line_index_review_not_ready")
        return _finalize(summary)
    if (
        _raw_path(db_path, root=root).is_symlink()
        or _raw_path(line_index_path, root=root).is_symlink()
    ):
        summary["blocker_categories"].append("symlink_input_rejected")
        return _finalize(summary)
    if not resolved_db.exists() or not resolved_line_index.exists():
        summary["blocker_categories"].append("input_missing")
        return _finalize(summary)
    if resolved_db.is_dir() or resolved_line_index.is_dir():
        summary["blocker_categories"].append("directory_input_rejected")
        return _finalize(summary)

    try:
        private_db = load_json(resolved_db)
        line_index = load_json(resolved_line_index)
    except Exception:
        summary["context_graph_status"] = "decode_failed"
        summary["blocker_categories"].append("json_decode_failed")
        return summary

    if (
        isinstance(private_db, dict)
        and private_db.get("schema_version") == PRIVATE_DB_SCHEMA_VERSION
    ):
        summary["db_schema_version_matches"] = True
    if (
        isinstance(line_index, dict)
        and line_index.get("schema_version") == LINE_INDEX_SCHEMA_VERSION
    ):
        summary["line_index_schema_version_matches"] = True
    if not _inputs_are_compatible(private_db, line_index, summary):
        return _finalize(summary)

    graph = build_m2_context_graph(private_db, line_index)
    write_context_graph(graph, resolved_output)
    summary.update(
        {
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "context_graph_output_written": True,
            "context_graph_status": "built",
            "m2_context_graph_done": True,
        }
    )
    return _finalize(summary)


def build_m2_context_graph(
    private_db: dict[str, Any], line_index: dict[str, Any]
) -> dict[str, Any]:
    nodes = [
        {
            "record_id": entry["record_id"],
            "line_id": entry["line_id"],
            "conversation_id": entry["conversation_id"],
            "speaker_id": entry["speaker_id"],
            "context_placeholder": entry["context_placeholder"],
            "context_tags": list(entry["context_tags"]),
            "redacted_metadata": entry["redacted_metadata"],
        }
        for entry in line_index["entries"]
    ]
    nodes.sort(key=lambda node: (node["line_id"], node["record_id"]))
    edges = [
        {
            "from_record_id": edge["from_record_id"],
            "to_record_id": edge["to_record_id"],
            "relation": edge["relation"],
            "retrieval_bucket": RELATION_TO_BUCKET[edge["relation"]],
        }
        for edge in private_db["context_edges"]
    ]
    edges.sort(key=lambda edge: (edge["from_record_id"], edge["to_record_id"], edge["relation"]))
    return {
        "schema_version": CONTEXT_GRAPH_SCHEMA_VERSION,
        "source_db_schema_version": PRIVATE_DB_SCHEMA_VERSION,
        "source_line_index_schema_version": LINE_INDEX_SCHEMA_VERSION,
        "source_kind": private_db["source_kind"],
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "default_spoiler_budget": "none",
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "context_graph_constructed": True,
        "retrieval_bucket_mapping_used": True,
        "source_text_duplicated_in_graph": False,
        "arbitrary_future_branch_traversal_used": False,
        "automatic_game_install_scanning": False,
        "provider_called": False,
        "companion_contract_changed": False,
    }


def resolve_private_db_input_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_private_path(path, root=root, allowed_root=PRIVATE_DB_ROOT, label="input DB")


def resolve_line_index_input_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_private_path(
        path,
        root=root,
        allowed_root=PRIVATE_LINE_INDEX_ROOT,
        label="line-index input",
    )


def resolve_line_index_review_input_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_private_path(
        path,
        root=root,
        allowed_root=LINE_INDEX_REVIEW_ROOT,
        label="line-index review",
    )


def resolve_context_graph_output_path(path: Path, *, root: Path = ROOT) -> Path:
    resolved = _resolve_private_path(
        path,
        root=root,
        allowed_root=PRIVATE_CONTEXT_GRAPH_ROOT,
        label="context-graph output",
        must_exist=False,
    )
    if resolved.suffix.lower() != ".json":
        raise M2ContextGraphError("Context-graph output path must use the .json suffix.")
    return resolved


def resolve_context_graph_summary_output_path(path: Path, *, root: Path = ROOT) -> Path:
    resolved = _resolve_private_path(
        path,
        root=root,
        allowed_root=SUMMARY_OUTPUT_ROOT,
        label="context-graph summary output",
        must_exist=False,
    )
    if resolved.suffix.lower() != ".json":
        raise M2ContextGraphError("Context-graph summary output path must use the .json suffix.")
    return resolved


def write_context_graph(graph: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(summary: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir) / "fake-repo"
        private_marker = "PRIVATE_CONTEXT_GRAPH_VALUE_SHOULD_NOT_APPEAR"
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
        line_index_summary = run_m2_line_index(
            db_path, Path(LOCAL_IMPORT_REVIEW_ROOT) / "review.json", line_index_path, root=root
        )
        line_index_summary_path = root / LINE_INDEX_SUMMARY_ROOT / "summary.json"
        write_line_index_summary(line_index_summary, line_index_summary_path)
        line_index_review = build_line_index_review(
            line_index_summary, summary_path=line_index_summary_path, root=root
        )
        line_index_review_path = root / LINE_INDEX_REVIEW_ROOT / "review.json"
        line_index_review_path.parent.mkdir(parents=True, exist_ok=True)
        line_index_review_path.write_text(
            json.dumps(line_index_review, indent=2, sort_keys=True), encoding="utf-8"
        )

        output_path = Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "graph.json"
        summary = run_m2_context_graph(
            db_path,
            line_index_path,
            Path(LINE_INDEX_REVIEW_ROOT) / "review.json",
            output_path,
            root=root,
        )
        rendered = json.dumps(summary, sort_keys=True)
        if (
            summary["context_graph_status"] != "built"
            or summary["node_count"] != 2
            or summary["edge_count"] != 1
        ):
            raise M2ContextGraphError("Self-test context graph summary was incorrect.")
        if private_marker in rendered or str(root) in rendered:
            raise M2ContextGraphError("Self-test summary leaked private content or paths.")
        graph = load_json(root / output_path)
        written = json.dumps(graph, sort_keys=True)
        if private_marker not in written:
            raise M2ContextGraphError("Self-test graph did not preserve private ids.")
        if '"source_text":' in written:
            raise M2ContextGraphError("Self-test graph duplicated source text.")


def _inputs_are_compatible(private_db: Any, line_index: Any, summary: dict[str, Any]) -> bool:
    compatible = True
    if not isinstance(private_db, dict):
        summary["blocker_categories"].append("private_db_json_object_required")
        compatible = False
    if not isinstance(line_index, dict):
        summary["blocker_categories"].append("line_index_json_object_required")
        compatible = False
    if not compatible:
        return False
    if private_db.get("schema_version") != PRIVATE_DB_SCHEMA_VERSION:
        summary["blocker_categories"].append("private_db_schema_version_mismatch")
        compatible = False
    if line_index.get("schema_version") != LINE_INDEX_SCHEMA_VERSION:
        summary["blocker_categories"].append("line_index_schema_version_mismatch")
        compatible = False
    if not isinstance(private_db.get("context_edges"), list):
        summary["blocker_categories"].append("context_edges_array_required")
        compatible = False
    if not isinstance(line_index.get("entries"), list):
        summary["blocker_categories"].append("line_index_entries_array_required")
        compatible = False
    if not compatible:
        return False
    record_ids = {
        entry.get("record_id") for entry in line_index["entries"] if isinstance(entry, dict)
    }
    for entry in line_index["entries"]:
        if not _entry_is_compatible(entry):
            summary["blocker_categories"].append("line_index_entry_shape_mismatch")
            compatible = False
            break
    for edge in private_db["context_edges"]:
        if not _edge_is_compatible(edge):
            summary["blocker_categories"].append("context_edge_shape_mismatch")
            compatible = False
            break
        if edge["from_record_id"] not in record_ids or edge["to_record_id"] not in record_ids:
            summary["blocker_categories"].append("context_edge_reference_mismatch")
            compatible = False
            break
    if line_index.get("context_graph_constructed") is not False:
        summary["blocker_categories"].append("source_context_graph_already_constructed")
        compatible = False
    return compatible


def _entry_is_compatible(entry: Any) -> bool:
    if not isinstance(entry, dict):
        return False
    expected = {
        "record_id": str,
        "line_id": str,
        "conversation_id": str,
        "speaker_id": str,
        "context_placeholder": str,
        "context_tags": list,
        "redacted_metadata": dict,
    }
    return all(
        field in entry and isinstance(entry[field], kind) for field, kind in expected.items()
    )


def _edge_is_compatible(edge: Any) -> bool:
    return (
        isinstance(edge, dict)
        and isinstance(edge.get("from_record_id"), str)
        and isinstance(edge.get("to_record_id"), str)
        and edge.get("relation") in RELATION_TO_BUCKET
    )


def _line_index_review_is_ready(review: Any) -> bool:
    return (
        isinstance(review, dict)
        and review.get("schema_version") == LINE_INDEX_REVIEW_SCHEMA_VERSION
        and review.get("summary_valid") is True
        and review.get("ready_for_context_graph_implementation") is True
        and review.get("context_graph_construction_allowed_next") is True
        and review.get("retrieval_bucket_mapping_allowed_next")
        == "context_graph_relation_mapping_only"
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
        raise M2ContextGraphError(f"Unsafe {label} path. Use {allowed_root}.") from exc
    if must_exist and not resolved.exists():
        raise M2ContextGraphError(f"M2 {label} path must point to an existing file.")
    if must_exist and not resolved.is_file():
        raise M2ContextGraphError(f"M2 {label} path must point to a file.")
    if _raw_path(path, root=root).is_symlink():
        raise M2ContextGraphError(f"M2 {label} path must not be a symlink.")
    return resolved


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise M2ContextGraphError("Unsafe path traversal is not allowed.")
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
            raise M2ContextGraphError("Path uses a forbidden runtime/private marker.")


def _raw_path(path: Path, *, root: Path) -> Path:
    raw = path.expanduser()
    if raw.is_absolute():
        return raw
    return root / raw


def _finalize(summary: dict[str, Any]) -> dict[str, Any]:
    summary["blocker_categories"] = list(dict.fromkeys(summary["blocker_categories"]))
    if summary["blocker_categories"] and summary["context_graph_status"] != "decode_failed":
        summary["context_graph_status"] = "incompatible"
    return summary


def _base_summary() -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "db_input_exists": False,
        "line_index_input_exists": False,
        "db_schema_version_matches": False,
        "line_index_schema_version_matches": False,
        "node_count": 0,
        "edge_count": 0,
        "context_graph_output_written": False,
        "context_graph_status": "incompatible",
        "blocker_categories": [],
        "m2_context_graph_done": False,
        "private_paths_included": False,
        "filenames_included": False,
        "record_ids_in_stdout": False,
        "line_ids_in_stdout": False,
        "relation_values_in_stdout": False,
        "source_text_in_stdout": False,
        "source_text_duplicated_in_graph": False,
        "hashes_computed": False,
        "content_hashing_used": False,
        "path_string_hashing_used": False,
        "filename_hashing_used": False,
        "id_hashing_used": False,
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
