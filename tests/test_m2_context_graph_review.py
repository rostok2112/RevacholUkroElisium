from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.review_m2_context_graph import (
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    M2ContextGraphReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_summary_errors,
    resolve_review_output_path,
    resolve_summary_input_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.run_m2_context_graph import (
    PRIVATE_CONTEXT_GRAPH_ROOT,
    SUMMARY_OUTPUT_ROOT,
    SUMMARY_SCHEMA_VERSION,
    run_m2_context_graph,
    write_summary,
)
from scripts.schema_validator import load_json
from tests.test_m2_context_graph import PRIVATE_MARKER, _fake_repo, _prepare_private_inputs


ROOT = Path(__file__).resolve().parents[1]


class M2ContextGraphReviewTests(unittest.TestCase):
    def test_ready_review_reads_summary_only(self) -> None:
        with _fake_repo() as root:
            summary_path, graph_path, db_path, line_index_path = _write_ready_summary(root)
            (root / graph_path).unlink()
            (root / db_path).unlink()
            (root / line_index_path).unlink()

            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["summary_valid"])
            self.assertTrue(review["ready_for_m2_closeout_review_gate"])
            self.assertTrue(review["m2_closeout_allowed_next"])
            self.assertTrue(review["original_m2_import_done"])
            self.assertTrue(review["original_m2_line_index_done"])
            self.assertTrue(review["original_m2_context_graph_done"])
            self.assertEqual("m2_closeout_review_gate", review["recommended_next_step"])
            self.assertFalse(review["context_graph_artifact_reopened_during_review"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn(str(root), rendered)

    def test_blocked_summary_recommends_repeat(self) -> None:
        with _fake_repo() as root:
            summary_path = root / SUMMARY_OUTPUT_ROOT / "blocked.json"
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            payload = _ready_summary_payload()
            payload["context_graph_status"] = "incompatible"
            payload["context_graph_output_written"] = False
            payload["m2_context_graph_done"] = False
            payload["blocker_categories"] = ["context_edge_reference_mismatch"]
            write_summary(payload, summary_path)

            review = build_review(payload, summary_path=summary_path, root=root)

            self.assertTrue(review["summary_valid"])
            self.assertFalse(review["ready_for_m2_closeout_review_gate"])
            self.assertEqual(
                "repeat_m2_context_graph_implementation", review["recommended_next_step"]
            )
            self.assertIn("context_edge_reference_mismatch", review["blockers"])

    def test_malformed_summary_and_unsafe_markers_rejected(self) -> None:
        with _fake_repo() as root:
            summary_path = root / SUMMARY_OUTPUT_ROOT / "bad.json"
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            payload = _ready_summary_payload()
            payload["private_paths_included"] = True
            payload["blocker_categories"] = ["raw payload"]
            write_summary(payload, summary_path)

            errors = collect_summary_errors(payload, summary_path=summary_path, root=root)

            self.assertTrue(any("private_paths_included" in error for error in errors))
            self.assertTrue(any("raw payload" in error for error in errors))

    def test_path_bounds_and_review_outputs_are_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path, _graph_path, _db_path, _line_index_path = _write_ready_summary(root)
            self.assertEqual(summary_path, resolve_summary_input_path(summary_path, root=root))
            with self.assertRaises(M2ContextGraphReviewError):
                resolve_summary_input_path(Path("docs/summary.json"), root=root)
            with self.assertRaises(M2ContextGraphReviewError):
                resolve_review_output_path(Path("docs/review.json"), root=root)

            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
            md_path = root / REVIEW_OUTPUT_ROOT / "review.md"
            write_json_review(review, resolve_review_output_path(json_path, root=root))
            write_markdown_review(review, resolve_review_output_path(md_path, root=root))
            written = json_path.read_text(encoding="utf-8") + md_path.read_text(encoding="utf-8")

            self.assertNotIn(PRIVATE_MARKER, written)
            self.assertNotIn(str(root), written)
            self.assertNotIn("previous_visible", written)

    def test_decision_fixture_self_test_and_check_all_registration(self) -> None:
        self.assertEqual([], collect_decision_fixture_errors())
        run_self_test()
        check_all = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/review_m2_context_graph.py", check_all)
        self.assertIn("--self-test", check_all)

    def test_quiet_cli(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/review_m2_context_graph.py", "--self-test", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn(PRIVATE_MARKER, completed.stdout)


def _write_ready_summary(root: Path) -> tuple[Path, Path, Path, Path]:
    db_path, line_index_path, review_path = _prepare_private_inputs(root)
    graph_path = Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "graph.json"
    summary = run_m2_context_graph(db_path, line_index_path, review_path, graph_path, root=root)
    summary_path = root / SUMMARY_OUTPUT_ROOT / "summary.json"
    write_summary(summary, summary_path)
    return summary_path, graph_path, db_path, line_index_path


def _ready_summary_payload() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "db_input_exists": True,
        "line_index_input_exists": True,
        "db_schema_version_matches": True,
        "line_index_schema_version_matches": True,
        "node_count": 2,
        "edge_count": 1,
        "context_graph_output_written": True,
        "context_graph_status": "built",
        "blocker_categories": [],
        "m2_context_graph_done": True,
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


if __name__ == "__main__":
    unittest.main()
