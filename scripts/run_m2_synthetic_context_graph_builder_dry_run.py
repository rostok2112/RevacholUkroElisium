from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.m2_synthetic_import_validator import load_and_validate_m2_synthetic_import
    from scripts.run_m2_synthetic_line_index_builder_dry_run import (
        INDEX_SCHEMA_VERSION,
        assert_valid_m2_synthetic_line_index,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from m2_synthetic_import_validator import load_and_validate_m2_synthetic_import
    from run_m2_synthetic_line_index_builder_dry_run import (
        INDEX_SCHEMA_VERSION,
        assert_valid_m2_synthetic_line_index,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


GRAPH_SCHEMA_VERSION = "m2-synthetic-context-graph.v1"
SUMMARY_SCHEMA_VERSION = "m2-synthetic-context-graph-builder-dry-run-summary.v1"
IMPORT_SOURCE_FIXTURE = ROOT / "tests/fixtures/m2_synthetic_import_db.synthetic.json"
LINE_INDEX_FIXTURE = ROOT / "tests/fixtures/m2_synthetic_line_index.synthetic.json"
EXPECTED_GRAPH_FIXTURE = ROOT / "tests/fixtures/m2_synthetic_context_graph.synthetic.json"
PRIVATE_OUTPUT_ROOT = "workspace/local-private/extraction-indexing/import/context-graph/"

RELATION_TO_BUCKET = {
    "previous_visible": "visible_history",
    "nearby_branch": "nearby_tree",
    "player_option": "player_options",
}
FALSE_SAFETY_FIELDS = (
    "real_game_text_included",
    "source_text_included",
    "file_contents_included",
    "paths_included",
    "filenames_included",
    "hashes_included",
    "raw_payloads_included",
    "logs_included",
    "runtime_evidence_included",
    "private_input_read",
    "graph_constructed",
    "arbitrary_future_branch_traversal",
    "automatic_game_install_scanning",
    "game_files_read",
    "bepinex_logs_read",
    "screenshots_read",
    "ocr_used",
    "save_files_read",
    "decompiled_code_used",
    "current_line_capture_used",
    "ui_text_reading_used",
    "unity_scanning_used",
    "hooks_used",
    "provider_called",
    "companion_contract_changed",
    "generated_graph_committed",
)


class M2SyntheticContextGraphBuilderDryRunError(RuntimeError):
    """Raised when the synthetic context-graph dry-run request is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a metadata-only M2 context graph from invented synthetic fixtures."
    )
    parser.add_argument(
        "--import-source",
        type=Path,
        default=IMPORT_SOURCE_FIXTURE,
        help="Explicit synthetic import JSON. Defaults to the committed invented fixture.",
    )
    parser.add_argument(
        "--line-index",
        type=Path,
        default=LINE_INDEX_FIXTURE,
        help="Explicit synthetic line-index JSON. Defaults to the committed metadata fixture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional output under "
            "workspace/local-private/extraction-indexing/import/context-graph/."
        ),
    )
    parser.add_argument(
        "--check-fixture",
        action="store_true",
        help="Compare generated metadata with the committed synthetic context-graph fixture.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    try:
        source = load_and_validate_m2_synthetic_import(args.import_source)
        line_index = load_json(args.line_index)
        assert_valid_m2_synthetic_line_index(line_index, source)
        graph = build_m2_synthetic_context_graph(source, line_index)
        assert_valid_m2_synthetic_context_graph(graph, source, line_index)
        if args.check_fixture and graph != load_json(EXPECTED_GRAPH_FIXTURE):
            raise M2SyntheticContextGraphBuilderDryRunError(
                "Generated M2 synthetic context graph does not match the committed fixture."
            )

        output_path = resolve_output_path(args.output) if args.output else None
        if output_path:
            write_m2_synthetic_context_graph(graph, output_path)

        if args.quiet:
            print("M2 synthetic context-graph builder dry-run passed.")
        else:
            print(json.dumps(build_summary(graph, output_written=bool(output_path)), indent=2))
        return 0
    except (OSError, ValueError, M2SyntheticContextGraphBuilderDryRunError) as exc:
        parser.error(str(exc))
    return 0


def build_m2_synthetic_context_graph(
    source: dict[str, Any],
    line_index: dict[str, Any],
) -> dict[str, Any]:
    nodes = sorted(line_index["entries"], key=lambda node: node["line_id"])
    edges = sorted(
        (
            {
                "from_line_id": edge["from_record_id"],
                "to_line_id": edge["to_record_id"],
                "relation": edge["relation"],
                "retrieval_bucket": RELATION_TO_BUCKET[edge["relation"]],
            }
            for edge in source["context_edges"]
        ),
        key=_edge_sort_key,
    )
    return {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "source_import_schema_version": source["schema_version"],
        "source_line_index_schema_version": INDEX_SCHEMA_VERSION,
        "source_kind": "synthetic_fixture",
        "generated_from_synthetic_fixture": True,
        "default_spoiler_budget": "none",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "fixture_only": True,
            "contract_only": True,
            "m2_import_locally_extracted_db_done": False,
            "m2_line_index_done": False,
            "m2_context_graph_done": False,
            "recommended_next_step": "m2_synthetic_context_graph_builder_dry_run",
        },
        "safety_flags": {field: False for field in FALSE_SAFETY_FIELDS},
    }


def assert_valid_m2_synthetic_context_graph(
    graph: dict[str, Any],
    source: dict[str, Any],
    line_index: dict[str, Any],
) -> None:
    errors: list[str] = []
    if graph.get("schema_version") != GRAPH_SCHEMA_VERSION:
        errors.append(f"schema_version must be {GRAPH_SCHEMA_VERSION!r}.")
    if graph.get("source_import_schema_version") != source.get("schema_version"):
        errors.append("source_import_schema_version must match the synthetic import.")
    if graph.get("source_line_index_schema_version") != INDEX_SCHEMA_VERSION:
        errors.append(f"source_line_index_schema_version must be {INDEX_SCHEMA_VERSION!r}.")
    if graph.get("source_kind") != "synthetic_fixture":
        errors.append("source_kind must be 'synthetic_fixture'.")
    if graph.get("generated_from_synthetic_fixture") is not True:
        errors.append("generated_from_synthetic_fixture must remain true.")
    if graph.get("default_spoiler_budget") != "none":
        errors.append("default_spoiler_budget must remain 'none'.")
    if graph != build_m2_synthetic_context_graph(source, line_index):
        errors.append("context graph must match the deterministic metadata-only source projection.")
    if errors:
        raise M2SyntheticContextGraphBuilderDryRunError("; ".join(errors))


def build_summary(graph: dict[str, Any], *, output_written: bool) -> dict[str, Any]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "graph_schema_version": graph["schema_version"],
        "node_count": graph["node_count"],
        "edge_count": graph["edge_count"],
        "generated_from_synthetic_fixture": True,
        "default_spoiler_budget": "none",
        "output_written": output_written,
        "graph_construction_mode": "dry_run",
        "graph_constructed": False,
        "real_game_text_included": False,
        "source_text_included": False,
        "arbitrary_future_branch_traversal": False,
        "paths_included": False,
        "filenames_included": False,
        "hashes_included": False,
        "raw_payloads_included": False,
        "logs_included": False,
        "runtime_evidence_included": False,
        "private_input_read": False,
        "game_files_read": False,
        "automatic_game_install_scanning": False,
    }


def resolve_output_path(output: Path, *, root: Path = ROOT) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (root / raw).resolve(strict=False)
    )
    output_root = (root / PRIVATE_OUTPUT_ROOT).resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise M2SyntheticContextGraphBuilderDryRunError(
            "Unsafe output path. Use "
            "workspace/local-private/extraction-indexing/import/context-graph/."
        )
    if resolved.exists() and resolved.is_dir():
        raise M2SyntheticContextGraphBuilderDryRunError("Output path must point to a JSON file.")
    return resolved


def write_m2_synthetic_context_graph(graph: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _edge_sort_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (str(edge.get("from_line_id")), str(edge.get("to_line_id")), str(edge.get("relation")))


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
