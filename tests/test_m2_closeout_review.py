from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.review_m2_closeout import (
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    M2CloseoutReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_closeout_errors,
    resolve_closeout_output_path,
    resolve_review_input_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.review_m2_context_graph import (
    REVIEW_OUTPUT_ROOT as CONTEXT_GRAPH_REVIEW_ROOT,
    build_review as build_context_graph_review,
)
from scripts.review_m2_line_index import (
    REVIEW_OUTPUT_ROOT as LINE_INDEX_REVIEW_ROOT,
    build_review as build_line_index_review,
)
from scripts.review_m2_local_import import (
    REVIEW_OUTPUT_ROOT as LOCAL_IMPORT_REVIEW_ROOT,
    build_review as build_local_import_review,
)
from scripts.run_m2_context_graph import (
    LINE_INDEX_REVIEW_ROOT as CONTEXT_GRAPH_LINE_INDEX_REVIEW_ROOT,
    PRIVATE_CONTEXT_GRAPH_ROOT,
    SUMMARY_OUTPUT_ROOT as CONTEXT_GRAPH_SUMMARY_ROOT,
    run_m2_context_graph,
    write_summary as write_context_graph_summary,
)
from scripts.run_m2_line_index import (
    LOCAL_IMPORT_REVIEW_ROOT as LINE_INDEX_LOCAL_IMPORT_REVIEW_ROOT,
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
from tests.test_m2_context_graph import PRIVATE_MARKER, _fake_repo, _private_export


ROOT = Path(__file__).resolve().parents[1]


class M2CloseoutReviewTests(unittest.TestCase):
    def test_ready_closeout_marks_original_m2_complete(self) -> None:
        with _fake_repo() as root:
            local_path, line_path, graph_path, private_artifacts = _write_ready_reviews(root)
            for artifact in private_artifacts:
                artifact.unlink()

            review = build_review(
                load_json(local_path),
                load_json(line_path),
                load_json(graph_path),
                local_import_review_path=local_path,
                line_index_review_path=line_path,
                context_graph_review_path=graph_path,
                root=root,
            )
            rendered = json.dumps(review, sort_keys=True)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["closeout_evidence_valid"])
            self.assertTrue(review["original_m2_import_done"])
            self.assertTrue(review["original_m2_line_index_done"])
            self.assertTrue(review["original_m2_context_graph_done"])
            self.assertTrue(review["original_m2_complete"])
            self.assertEqual("m3_bepinex_bridge_planning", review["recommended_next_step"])
            self.assertFalse(review["private_artifacts_reopened_during_closeout_review"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn(str(root), rendered)

    def test_blocked_evidence_does_not_close_m2(self) -> None:
        with _fake_repo() as root:
            local_path, line_path, graph_path, _private_artifacts = _write_ready_reviews(root)
            graph = load_json(graph_path)
            graph["ready_for_m2_closeout_review_gate"] = False
            graph["original_m2_context_graph_done"] = False
            graph["blockers"] = ["context_graph_review_not_ready"]
            write_json_review(graph, graph_path)

            review = build_review(
                load_json(local_path),
                load_json(line_path),
                load_json(graph_path),
                local_import_review_path=local_path,
                line_index_review_path=line_path,
                context_graph_review_path=graph_path,
                root=root,
            )

            self.assertFalse(review["original_m2_complete"])
            self.assertEqual("repeat_m2_context_graph_review_gate", review["recommended_next_step"])
            self.assertIn("m2_closeout_evidence_not_ready", review["blockers"])

    def test_rejects_unsafe_markers_and_true_safety_flags(self) -> None:
        with _fake_repo() as root:
            local_path, line_path, graph_path, _private_artifacts = _write_ready_reviews(root)
            local = load_json(local_path)
            local["private_paths_included"] = True
            local["blockers"] = ["raw payload"]

            errors = collect_closeout_errors(
                local,
                load_json(line_path),
                load_json(graph_path),
                local_import_review_path=local_path,
                line_index_review_path=line_path,
                context_graph_review_path=graph_path,
                root=root,
            )

            self.assertTrue(any("private_paths_included" in error for error in errors))
            self.assertTrue(any("raw payload" in error for error in errors))

    def test_path_bounds_and_outputs_are_redacted(self) -> None:
        with _fake_repo() as root:
            local_path, line_path, graph_path, _private_artifacts = _write_ready_reviews(root)
            self.assertEqual(
                local_path,
                resolve_review_input_path(
                    local_path,
                    root=root,
                    allowed_root=LOCAL_IMPORT_REVIEW_ROOT,
                    label="local import review",
                ),
            )
            with self.assertRaises(M2CloseoutReviewError):
                resolve_review_input_path(
                    Path("docs/review.json"),
                    root=root,
                    allowed_root=LOCAL_IMPORT_REVIEW_ROOT,
                    label="local import review",
                )
            with self.assertRaises(M2CloseoutReviewError):
                resolve_closeout_output_path(Path("docs/review.json"), root=root)

            review = build_review(
                load_json(local_path),
                load_json(line_path),
                load_json(graph_path),
                local_import_review_path=local_path,
                line_index_review_path=line_path,
                context_graph_review_path=graph_path,
                root=root,
            )
            json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
            md_path = root / REVIEW_OUTPUT_ROOT / "review.md"
            write_json_review(review, resolve_closeout_output_path(json_path, root=root))
            write_markdown_review(review, resolve_closeout_output_path(md_path, root=root))
            written = json_path.read_text(encoding="utf-8") + md_path.read_text(encoding="utf-8")

            self.assertNotIn(PRIVATE_MARKER, written)
            self.assertNotIn(str(root), written)
            self.assertNotIn("previous_visible", written)

    def test_decision_fixture_self_test_docs_and_check_all(self) -> None:
        self.assertEqual([], collect_decision_fixture_errors())
        run_self_test()
        check_all = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        docs = (ROOT / "docs/m2-closeout-review-gate.md").read_text(encoding="utf-8")

        self.assertIn("scripts/review_m2_closeout.py", check_all)
        self.assertIn("scripts/review_m2_closeout.py", docs)
        self.assertIn("tests/fixtures/m2_closeout_review_decision.synthetic.json", docs)

    def test_quiet_cli(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/review_m2_closeout.py", "--self-test", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn(PRIVATE_MARKER, completed.stdout)


def _write_ready_reviews(root: Path) -> tuple[Path, Path, Path, tuple[Path, ...]]:
    private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
    private_file.parent.mkdir(parents=True, exist_ok=True)
    private_file.write_text(json.dumps(_private_export()), encoding="utf-8")

    db_path = Path(PRIVATE_DB_ROOT) / "imported-db.json"
    import_summary = run_m2_local_import(
        Path(PRIVATE_INPUT_ROOT) / "selected-export.json", db_path, root=root
    )
    import_summary_path = (
        root / "workspace/local-private/extraction-indexing/import/db-summary/summary.json"
    )
    write_import_summary(import_summary, import_summary_path)
    local_review = build_local_import_review(
        import_summary, summary_path=import_summary_path, root=root
    )
    local_review_path = root / LOCAL_IMPORT_REVIEW_ROOT / "review.json"
    write_json_review(local_review, local_review_path)

    line_index_path = Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json"
    line_summary = run_m2_line_index(
        db_path,
        Path(LINE_INDEX_LOCAL_IMPORT_REVIEW_ROOT) / "review.json",
        line_index_path,
        root=root,
    )
    line_summary_path = root / LINE_INDEX_SUMMARY_ROOT / "summary.json"
    write_line_index_summary(line_summary, line_summary_path)
    line_review = build_line_index_review(line_summary, summary_path=line_summary_path, root=root)
    line_review_path = root / LINE_INDEX_REVIEW_ROOT / "review.json"
    write_json_review(line_review, line_review_path)

    graph_path = Path(PRIVATE_CONTEXT_GRAPH_ROOT) / "graph.json"
    graph_summary = run_m2_context_graph(
        db_path,
        line_index_path,
        Path(CONTEXT_GRAPH_LINE_INDEX_REVIEW_ROOT) / "review.json",
        graph_path,
        root=root,
    )
    graph_summary_path = root / CONTEXT_GRAPH_SUMMARY_ROOT / "summary.json"
    write_context_graph_summary(graph_summary, graph_summary_path)
    graph_review = build_context_graph_review(
        graph_summary, summary_path=graph_summary_path, root=root
    )
    graph_review_path = root / CONTEXT_GRAPH_REVIEW_ROOT / "review.json"
    write_json_review(graph_review, graph_review_path)
    return (
        local_review_path,
        line_review_path,
        graph_review_path,
        (root / graph_path, root / line_index_path, root / db_path, private_file),
    )


if __name__ == "__main__":
    unittest.main()
