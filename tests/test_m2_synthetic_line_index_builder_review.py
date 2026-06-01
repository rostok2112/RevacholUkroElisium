from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m2_synthetic_line_index_builder_dry_run import (
    DECISION_FALSE_FIELDS,
    DECISION_FIXTURE_PATH,
    RECOMMENDED_CONTEXT_GRAPH_CONTRACT_STEP,
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    M2SyntheticLineIndexBuilderReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_index_errors,
    resolve_index_input_path,
    resolve_review_output_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.run_m2_synthetic_line_index_builder_dry_run import (
    PRIVATE_OUTPUT_ROOT,
    SOURCE_FIXTURE,
    build_m2_synthetic_line_index,
    write_m2_synthetic_line_index,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2SyntheticLineIndexBuilderReviewTests(unittest.TestCase):
    def test_valid_index_reviews_successfully(self) -> None:
        with _fake_repo() as root:
            index_path = _write_valid_index(root)

            review = build_review(load_json(index_path), index_path=index_path, root=root)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["index_valid"])
            self.assertEqual(3, review["record_count"])
            self.assertTrue(review["ready_for_context_graph_contract_decision"])
            self.assertFalse(review["context_graph_construction_allowed_next"])
            self.assertFalse(review["original_m2_line_index_done"])
            self.assertEqual(
                RECOMMENDED_CONTEXT_GRAPH_CONTRACT_STEP, review["recommended_next_step"]
            )
            self.assertEqual([], review["blockers"])

    def test_tampered_index_is_rejected_without_copying_details(self) -> None:
        with _fake_repo() as root:
            index_path = _write_valid_index(root)
            payload = load_json(index_path)
            payload["entries"][0]["speaker_id"] = "synthetic.m2.speaker.wrong"

            review = build_review(payload, index_path=index_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertFalse(review["index_valid"])
            self.assertFalse(review["ready_for_context_graph_contract_decision"])
            self.assertIn("invalid_synthetic_line_index", review["blockers"])
            self.assertNotIn("synthetic.m2.speaker.wrong", rendered)

    def test_malformed_index_is_rejected(self) -> None:
        with _fake_repo() as root:
            index_path = _write_valid_index(root)

            review = build_review({"schema_version": "wrong"}, index_path=index_path, root=root)

            self.assertFalse(review["index_valid"])
            self.assertFalse(review["ready_for_context_graph_contract_decision"])

    def test_index_outside_private_root_rejected(self) -> None:
        with _fake_repo() as root:
            outside = root / "workspace/synthetic-slice/index.json"
            outside.parent.mkdir(parents=True)
            outside.write_text("{}", encoding="utf-8")

            with self.assertRaises(M2SyntheticLineIndexBuilderReviewError):
                resolve_index_input_path(outside, root=root)

    def test_review_output_outside_review_root_rejected(self) -> None:
        with _fake_repo() as root:
            for path in (
                Path(PRIVATE_OUTPUT_ROOT) / "review.json",
                Path("workspace/synthetic-slice/review.json"),
                Path("../workspace/local-private/extraction-indexing/import/line-index-review/x"),
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M2SyntheticLineIndexBuilderReviewError):
                        resolve_review_output_path(path, root=root)

    def test_json_and_markdown_reviews_are_redacted(self) -> None:
        with _fake_repo() as root:
            index_path = _write_valid_index(root)
            review = build_review(load_json(index_path), index_path=index_path, root=root)
            json_path = resolve_review_output_path(
                Path(REVIEW_OUTPUT_ROOT) / "review.json", root=root
            )
            md_path = resolve_review_output_path(Path(REVIEW_OUTPUT_ROOT) / "review.md", root=root)

            write_json_review(review, json_path)
            write_markdown_review(review, md_path)
            rendered = json_path.read_text(encoding="utf-8") + md_path.read_text(encoding="utf-8")

            for forbidden in (
                "synthetic_office_entry",
                "synthetic.m2.line.001",
                "The paper umbrella requested",
                str(root),
            ):
                with self.subTest(forbidden=forbidden):
                    self.assertNotIn(forbidden, rendered)
            self.assertIn("context_graph_construction_allowed_next: no", rendered)

    def test_raw_markers_are_rejected(self) -> None:
        with _fake_repo() as root:
            index_path = _write_valid_index(root)
            payload = load_json(index_path)
            payload["entries"][0]["context_placeholder"] = "raw payload dump"

            errors = collect_index_errors(payload, index_path=index_path, root=root)

            self.assertNotEqual([], errors)

    def test_decision_fixture_is_safe(self) -> None:
        payload = load_json(DECISION_FIXTURE_PATH)

        self.assertEqual([], collect_decision_fixture_errors())
        self.assertEqual("M2", payload["roadmap_milestone"])
        self.assertEqual(RECOMMENDED_CONTEXT_GRAPH_CONTRACT_STEP, payload["recommended_next_step"])
        for field in DECISION_FALSE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(payload[field], False)

    def test_decision_fixture_rejects_forbidden_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "decision.json"
            payload = load_json(DECISION_FIXTURE_PATH)
            for field in DECISION_FALSE_FIELDS:
                with self.subTest(field=field):
                    mutated = copy.deepcopy(payload)
                    mutated[field] = True
                    path.write_text(json.dumps(mutated), encoding="utf-8")
                    self.assertNotEqual([], collect_decision_fixture_errors(path))

    def test_self_test_uses_temp_workspace_only(self) -> None:
        run_self_test()

    def test_cli_self_test_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_m2_synthetic_line_index_builder_dry_run.py",
                "--self-test",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn("synthetic_office_entry", completed.stdout)

    def test_check_all_registers_review_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/review_m2_synthetic_line_index_builder_dry_run.py", text)
        self.assertIn("--self-test", text)


def _write_valid_index(root: Path) -> Path:
    index = build_m2_synthetic_line_index(load_json(SOURCE_FIXTURE))
    path = root / PRIVATE_OUTPUT_ROOT / "index.json"
    write_m2_synthetic_line_index(index, path)
    return path


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
