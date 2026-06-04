from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m2_line_index import build_review as build_line_index_review
from scripts.review_m2_local_import import build_review as build_local_import_review
from scripts.run_m2_context_graph import (
    CONTEXT_GRAPH_SCHEMA_VERSION,
    LINE_INDEX_REVIEW_ROOT,
    PRIVATE_CONTEXT_GRAPH_ROOT,
    SUMMARY_SCHEMA_VERSION,
    M2ContextGraphError,
    build_m2_context_graph,
    resolve_context_graph_output_path,
    resolve_line_index_input_path,
    resolve_line_index_review_input_path,
    resolve_private_db_input_path,
    run_m2_context_graph,
    run_self_test,
)
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
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKER = "PRIVATE_CONTEXT_GRAPH_VALUE_SHOULD_NOT_LEAK"


class M2ContextGraphTests(unittest.TestCase):
    def test_builds_private_context_graph_from_private_db_line_index_and_review(self) -> None:
        with _fake_repo() as root:
            db_path, line_index_path, review_path = _prepare_private_inputs(root)
            output_path = Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "graph.json"

            summary = run_m2_context_graph(
                db_path, line_index_path, review_path, output_path, root=root
            )
            rendered = json.dumps(summary, sort_keys=True)
            graph = load_json(root / output_path)

            self.assertEqual(SUMMARY_SCHEMA_VERSION, summary["schema_version"])
            self.assertEqual("built", summary["context_graph_status"])
            self.assertTrue(summary["db_schema_version_matches"])
            self.assertTrue(summary["line_index_schema_version_matches"])
            self.assertEqual(2, summary["node_count"])
            self.assertEqual(1, summary["edge_count"])
            self.assertTrue(summary["context_graph_output_written"])
            self.assertTrue(summary["m2_context_graph_done"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn(str(root), rendered)

            self.assertEqual(CONTEXT_GRAPH_SCHEMA_VERSION, graph["schema_version"])
            self.assertEqual(2, len(graph["nodes"]))
            self.assertEqual(1, len(graph["edges"]))
            self.assertEqual("visible_history", graph["edges"][0]["retrieval_bucket"])
            self.assertEqual("none", graph["metadata"]["default_spoiler_budget"])
            self.assertNotIn('"source_text":', json.dumps(graph, sort_keys=True))
            self.assertIn(PRIVATE_MARKER, json.dumps(graph, sort_keys=True))
            self.assertTrue(graph["context_graph_constructed"])
            self.assertTrue(graph["retrieval_bucket_mapping_used"])
            self.assertFalse(graph["arbitrary_future_branch_traversal_used"])

    def test_requires_ready_line_index_review(self) -> None:
        with _fake_repo() as root:
            db_path, line_index_path, review_path = _prepare_private_inputs(root)
            review = load_json(root / review_path)
            review["ready_for_context_graph_implementation"] = False
            review["context_graph_construction_allowed_next"] = False
            (root / review_path).write_text(json.dumps(review), encoding="utf-8")

            summary = run_m2_context_graph(
                db_path,
                line_index_path,
                review_path,
                Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "blocked.json",
                root=root,
            )

            self.assertEqual("incompatible", summary["context_graph_status"])
            self.assertIn("line_index_review_not_ready", summary["blocker_categories"])
            self.assertFalse(summary["context_graph_output_written"])

    def test_rejects_bad_shapes_and_unresolved_edges_without_private_leak(self) -> None:
        with _fake_repo() as root:
            db_path, line_index_path, review_path = _prepare_private_inputs(root)
            private_db = load_json(root / db_path)
            private_db["context_edges"][0]["to_record_id"] = "missing"
            (root / db_path).write_text(json.dumps(private_db), encoding="utf-8")

            summary = run_m2_context_graph(
                db_path,
                line_index_path,
                review_path,
                Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "bad.json",
                root=root,
            )
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual("incompatible", summary["context_graph_status"])
            self.assertIn("context_edge_reference_mismatch", summary["blocker_categories"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertFalse(summary["context_graph_output_written"])

    def test_relation_mapping_for_allowed_buckets(self) -> None:
        private_db = _private_db_payload()
        private_db["context_edges"] = [
            {
                "from_record_id": f"{PRIVATE_MARKER}_A",
                "to_record_id": f"{PRIVATE_MARKER}_B",
                "relation": "previous_visible",
            },
            {
                "from_record_id": f"{PRIVATE_MARKER}_A",
                "to_record_id": f"{PRIVATE_MARKER}_B",
                "relation": "nearby_branch",
            },
            {
                "from_record_id": f"{PRIVATE_MARKER}_A",
                "to_record_id": f"{PRIVATE_MARKER}_B",
                "relation": "player_option",
            },
        ]
        graph = build_m2_context_graph(private_db, _line_index_payload())

        self.assertEqual(
            {"visible_history", "nearby_tree", "player_options"},
            {edge["retrieval_bucket"] for edge in graph["edges"]},
        )

    def test_decode_failures_do_not_write_output(self) -> None:
        with _fake_repo() as root:
            _db_path, line_index_path, review_path = _prepare_private_inputs(root)
            malformed = root / PRIVATE_DB_ROOT / "malformed.json"
            malformed.write_text("{", encoding="utf-8")

            summary = run_m2_context_graph(
                Path(PRIVATE_DB_ROOT) / "malformed.json",
                line_index_path,
                review_path,
                Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "malformed-graph.json",
                root=root,
            )

            self.assertEqual("decode_failed", summary["context_graph_status"])
            self.assertFalse(summary["context_graph_output_written"])

    def test_rejects_unsafe_paths_and_symlinks(self) -> None:
        with _fake_repo() as root:
            db_path, line_index_path, review_path = _prepare_private_inputs(root)
            self.assertEqual(root / db_path, resolve_private_db_input_path(db_path, root=root))
            self.assertEqual(
                root / line_index_path, resolve_line_index_input_path(line_index_path, root=root)
            )
            self.assertEqual(
                root / review_path, resolve_line_index_review_input_path(review_path, root=root)
            )
            valid_output = resolve_context_graph_output_path(
                Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "graph.json",
                root=root,
            )
            self.assertEqual(("context-graph", "graph.json"), valid_output.parts[-2:])

            for path in (
                Path("docs/db.json"),
                Path(PRIVATE_DB_ROOT) / "../db.json",
                Path(PRIVATE_DB_ROOT) / "raw-log-db.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M2ContextGraphError):
                        resolve_private_db_input_path(path, root=root)
            for path in (
                Path("docs/graph.json"),
                Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "../graph.json",
                Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "graph.txt",
                Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "payload-dump-graph.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M2ContextGraphError):
                        resolve_context_graph_output_path(path, root=root)

            target = root / PRIVATE_LINE_INDEX_ROOT / "target.json"
            target.write_text(json.dumps(_line_index_payload()), encoding="utf-8")
            link = root / PRIVATE_LINE_INDEX_ROOT / "link.json"
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(M2ContextGraphError):
                resolve_line_index_input_path(
                    Path(PRIVATE_LINE_INDEX_ROOT) / "link.json", root=root
                )

    def test_quiet_cli_and_self_test(self) -> None:
        run_self_test()
        completed = subprocess.run(
            [sys.executable, "scripts/run_m2_context_graph.py", "--self-test", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn(PRIVATE_MARKER, completed.stdout)

    def test_check_all_registers_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_m2_context_graph.py", text)
        self.assertIn("--self-test", text)


def _prepare_private_inputs(root: Path) -> tuple[Path, Path, Path]:
    private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
    private_file.parent.mkdir(parents=True, exist_ok=True)
    private_file.write_text(json.dumps(_private_export()), encoding="utf-8")
    db_path = Path(PRIVATE_DB_ROOT) / "imported-db.json"
    import_summary = run_m2_local_import(
        Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
        db_path,
        root=root,
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
        db_path,
        Path(LOCAL_IMPORT_REVIEW_ROOT) / "review.json",
        line_index_path,
        root=root,
    )
    line_index_summary_path = root / LINE_INDEX_SUMMARY_ROOT / "summary.json"
    write_line_index_summary(line_index_summary, line_index_summary_path)
    line_index_review = build_line_index_review(
        line_index_summary,
        summary_path=line_index_summary_path,
        root=root,
    )
    line_index_review_path = root / LINE_INDEX_REVIEW_ROOT / "review.json"
    line_index_review_path.parent.mkdir(parents=True, exist_ok=True)
    line_index_review_path.write_text(
        json.dumps(line_index_review, indent=2, sort_keys=True), encoding="utf-8"
    )
    return db_path, line_index_path, Path(LINE_INDEX_REVIEW_ROOT) / "review.json"


def _private_export() -> dict[str, object]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            _record(f"{PRIVATE_MARKER}_B"),
            _record(f"{PRIVATE_MARKER}_A"),
        ],
        "context_edges": [
            {
                "from_record_id": f"{PRIVATE_MARKER}_A",
                "to_record_id": f"{PRIVATE_MARKER}_B",
                "relation": "previous_visible",
            }
        ],
        "metadata": {"nested_marker": PRIVATE_MARKER},
    }


def _private_db_payload() -> dict[str, object]:
    return {
        "schema_version": "m2-local-import-db.v1",
        "source_schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [_record(f"{PRIVATE_MARKER}_A"), _record(f"{PRIVATE_MARKER}_B")],
        "context_edges": [],
        "metadata": {"nested_marker": PRIVATE_MARKER},
        "line_index_constructed": False,
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
    }


def _line_index_payload() -> dict[str, object]:
    return {
        "schema_version": "m2-line-index.v1",
        "source_schema_version": "m2-local-import-db.v1",
        "source_kind": "private_export",
        "entries": [
            {
                "record_id": f"{PRIVATE_MARKER}_A",
                "line_id": f"{PRIVATE_MARKER}_line_A",
                "conversation_id": PRIVATE_MARKER,
                "speaker_id": PRIVATE_MARKER,
                "context_placeholder": PRIVATE_MARKER,
                "source_text": PRIVATE_MARKER,
                "context_tags": [PRIVATE_MARKER],
                "redacted_metadata": {"nested_marker": PRIVATE_MARKER},
            },
            {
                "record_id": f"{PRIVATE_MARKER}_B",
                "line_id": f"{PRIVATE_MARKER}_line_B",
                "conversation_id": PRIVATE_MARKER,
                "speaker_id": PRIVATE_MARKER,
                "context_placeholder": PRIVATE_MARKER,
                "source_text": PRIVATE_MARKER,
                "context_tags": [PRIVATE_MARKER],
                "redacted_metadata": {"nested_marker": PRIVATE_MARKER},
            },
        ],
        "metadata": {"nested_marker": PRIVATE_MARKER},
        "line_index_constructed": True,
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
    }


def _record(record_id: str) -> dict[str, object]:
    suffix = record_id.rsplit("_", maxsplit=1)[-1]
    return {
        "record_id": record_id,
        "line_id": f"{PRIVATE_MARKER}_line_{suffix}",
        "conversation_id": PRIVATE_MARKER,
        "speaker_id": PRIVATE_MARKER,
        "speaker_label": PRIVATE_MARKER,
        "context_placeholder": PRIVATE_MARKER,
        "source_text": PRIVATE_MARKER,
        "context_tags": [PRIVATE_MARKER],
        "redacted_metadata": {"nested_marker": PRIVATE_MARKER},
    }


class _fake_repo:
    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "fake-repo"
        self.root.mkdir()
        return self.root

    def __exit__(self, *_exc: object) -> None:
        self._tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
