from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_m2_synthetic_context_graph_builder_dry_run import (
    EXPECTED_GRAPH_FIXTURE,
    IMPORT_SOURCE_FIXTURE,
    LINE_INDEX_FIXTURE,
    PRIVATE_OUTPUT_ROOT,
    RELATION_TO_BUCKET,
    M2SyntheticContextGraphBuilderDryRunError,
    assert_valid_m2_synthetic_context_graph,
    build_m2_synthetic_context_graph,
    build_summary,
    resolve_output_path,
    write_m2_synthetic_context_graph,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2SyntheticContextGraphBuilderDryRunTests(unittest.TestCase):
    def test_generated_graph_matches_contract_fixture(self) -> None:
        source = load_json(IMPORT_SOURCE_FIXTURE)
        line_index = load_json(LINE_INDEX_FIXTURE)

        generated = build_m2_synthetic_context_graph(source, line_index)

        self.assertEqual(load_json(EXPECTED_GRAPH_FIXTURE), generated)
        assert_valid_m2_synthetic_context_graph(generated, source, line_index)

    def test_source_and_line_index_order_do_not_change_output(self) -> None:
        source = load_json(IMPORT_SOURCE_FIXTURE)
        line_index = load_json(LINE_INDEX_FIXTURE)
        reordered_source = copy.deepcopy(source)
        reordered_index = copy.deepcopy(line_index)
        reordered_source["context_edges"].reverse()
        reordered_index["entries"].reverse()

        self.assertEqual(
            build_m2_synthetic_context_graph(source, line_index),
            build_m2_synthetic_context_graph(reordered_source, reordered_index),
        )

    def test_output_is_metadata_only_and_spoiler_conservative(self) -> None:
        source = load_json(IMPORT_SOURCE_FIXTURE)
        graph = build_m2_synthetic_context_graph(source, load_json(LINE_INDEX_FIXTURE))
        summary = build_summary(graph, output_written=False)
        rendered = json.dumps(graph, sort_keys=True).lower()

        self.assertEqual("none", graph["default_spoiler_budget"])
        self.assertEqual(
            {
                "previous_visible": "visible_history",
                "nearby_branch": "nearby_tree",
                "player_option": "player_options",
            },
            RELATION_TO_BUCKET,
        )
        for forbidden in (
            "the paper umbrella requested",
            '"source_text":',
            '"filename":',
            '"paths_included": true',
            '"hashes_included": true',
            "raw payload",
            "logoutput.log",
            '"arbitrary_future_branch_traversal": true',
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)
        self.assertFalse(summary["graph_constructed"])
        self.assertFalse(summary["private_input_read"])

    def test_tampered_graph_is_rejected(self) -> None:
        source = load_json(IMPORT_SOURCE_FIXTURE)
        line_index = load_json(LINE_INDEX_FIXTURE)
        graph = build_m2_synthetic_context_graph(source, line_index)
        graph["edges"][0]["retrieval_bucket"] = "visible_history"

        with self.assertRaises(M2SyntheticContextGraphBuilderDryRunError):
            assert_valid_m2_synthetic_context_graph(graph, source, line_index)

    def test_invalid_explicit_import_is_rejected_by_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "invalid.json"
            source_path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_m2_synthetic_context_graph_builder_dry_run.py",
                    "--import-source",
                    str(source_path),
                    "--quiet",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn(str(source_path), completed.stderr)

    def test_output_path_allows_only_private_context_graph_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            allowed = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "graph.json", root=root)
            self.assertEqual(root / PRIVATE_OUTPUT_ROOT / "graph.json", allowed)

            for unsafe in (
                Path("docs/graph.json"),
                Path("workspace/local-private/extraction-indexing/import/graph.json"),
                Path(
                    "../workspace/local-private/extraction-indexing/import/context-graph/graph.json"
                ),
            ):
                with self.subTest(unsafe=unsafe):
                    with self.assertRaises(M2SyntheticContextGraphBuilderDryRunError):
                        resolve_output_path(unsafe, root=root)

    def test_write_uses_private_temp_output_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_path = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "graph.json", root=root)
            write_m2_synthetic_context_graph(
                build_m2_synthetic_context_graph(
                    load_json(IMPORT_SOURCE_FIXTURE),
                    load_json(LINE_INDEX_FIXTURE),
                ),
                output_path,
            )

            written = output_path.read_text(encoding="utf-8")
            self.assertNotIn("The paper umbrella requested", written)
            self.assertNotIn('"source_text":', written)

    def test_cli_check_fixture_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_m2_synthetic_context_graph_builder_dry_run.py",
                "--check-fixture",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn("paper umbrella", completed.stdout.lower())

    def test_check_all_registers_builder_smoke(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_m2_synthetic_context_graph_builder_dry_run.py", text)
        self.assertIn("--check-fixture", text)


if __name__ == "__main__":
    unittest.main()
