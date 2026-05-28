from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_private_input_adapter_dry_run import (
    DECISION_FALSE_FIELDS,
    DECISION_FIXTURE_PATH,
    DECISION_SCHEMA_VERSION,
    RECOMMENDED_HASH_NEXT_STEP,
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    PrivateInputDryRunReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_summary_errors,
    resolve_review_output_path,
    resolve_summary_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.run_private_input_adapter_dry_run import (
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    build_dry_run_summary,
    write_summary,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_CONTENT = "PRIVATE_CONTENT_SHOULD_NOT_LEAK"


class PrivateInputAdapterDryRunReviewTests(unittest.TestCase):
    def test_valid_dry_run_summary_reviews_successfully(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_valid_summary(root)
            private_input = root / PRIVATE_INPUT_ROOT / "selected.txt"
            private_input.unlink()

            payload = load_json(summary_path)
            review = build_review(payload, summary_path=summary_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["dry_run_valid"])
            self.assertTrue(review["input_was_under_allowed_root"])
            self.assertTrue(review["ready_for_hash_decision"])
            self.assertFalse(review["ready_for_private_index_decision"])
            self.assertEqual(RECOMMENDED_HASH_NEXT_STEP, review["recommended_next_step"])
            self.assertFalse(review["hashes_computed"])
            self.assertFalse(review["private_paths_included"])
            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)

    def test_malformed_summary_is_rejected_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_valid_summary(root)
            payload = load_json(summary_path)
            payload["schema_version"] = "wrong"

            review = build_review(payload, summary_path=summary_path, root=root)

            self.assertFalse(review["dry_run_valid"])
            self.assertFalse(review["ready_for_hash_decision"])
            self.assertIn("malformed_summary", review["blockers"])

    def test_summary_outside_private_output_root_rejected(self) -> None:
        with _fake_repo() as root:
            outside = root / "workspace/synthetic-slice/summary.json"
            outside.parent.mkdir(parents=True)
            outside.write_text("{}", encoding="utf-8")

            with self.assertRaises(PrivateInputDryRunReviewError):
                resolve_summary_path(outside, root=root)

    def test_review_output_path_outside_review_root_rejected(self) -> None:
        with _fake_repo() as root:
            for path in (
                Path(PRIVATE_OUTPUT_ROOT) / "review.json",
                Path("workspace/synthetic-slice/review.json"),
                Path("../workspace/local-private/extraction-indexing/review/review.json"),
            ):
                with self.subTest(path=path):
                    with self.assertRaises(PrivateInputDryRunReviewError):
                        resolve_review_output_path(path, root=root)

    def test_json_and_markdown_review_outputs_are_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_valid_summary(root)
            payload = load_json(summary_path)
            review = build_review(payload, summary_path=summary_path, root=root)
            json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
            markdown_path = root / REVIEW_OUTPUT_ROOT / "review.md"

            write_json_review(review, resolve_review_output_path(json_path, root=root))
            write_markdown_review(review, resolve_review_output_path(markdown_path, root=root))

            json_text = json_path.read_text(encoding="utf-8")
            markdown_text = markdown_path.read_text(encoding="utf-8")
            self.assertNotIn(PRIVATE_CONTENT, json_text)
            self.assertNotIn(PRIVATE_CONTENT, markdown_text)
            self.assertNotIn(str(root), json_text)
            self.assertNotIn(str(root), markdown_text)
            self.assertIn("ready_for_private_index_decision: no", markdown_text)

    def test_private_path_fields_rejected_by_default(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_valid_summary(root)
            payload = load_json(summary_path)
            payload["paths_redacted"] = False
            payload["input_path"] = str(root / PRIVATE_INPUT_ROOT / "selected.txt")

            review = build_review(payload, summary_path=summary_path, root=root)

            self.assertFalse(review["dry_run_valid"])
            self.assertIn("private_path_or_unsafe_path", review["blockers"])

    def test_raw_marker_values_rejected_without_copying_marker(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_valid_summary(root)
            payload = load_json(summary_path)
            payload["unsafe_note"] = "raw payload dump"

            review = build_review(payload, summary_path=summary_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertFalse(review["dry_run_valid"])
            self.assertIn("unsafe_marker_detected", review["blockers"])
            self.assertNotIn("raw payload dump", rendered)

    def test_hashes_computed_true_rejected(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_valid_summary(root)
            payload = load_json(summary_path)
            payload["hashes_computed"] = True

            review = build_review(payload, summary_path=summary_path, root=root)

            self.assertFalse(review["dry_run_valid"])
            self.assertFalse(review["ready_for_hash_decision"])
            self.assertIn("hashes_computed_not_allowed", review["blockers"])

    def test_summary_errors_cover_malformed_counts(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_valid_summary(root)
            payload = load_json(summary_path)
            payload["file_count"] = -1

            errors = collect_summary_errors(payload, summary_path=summary_path, root=root)

            self.assertNotEqual([], errors)

    def test_decision_fixture_shape_and_permissions(self) -> None:
        fixture = load_json(DECISION_FIXTURE_PATH)

        self.assertEqual(DECISION_SCHEMA_VERSION, fixture["schema_version"])
        self.assertEqual("5A.4", fixture["milestone"])
        self.assertTrue(fixture["dry_run_evidence_required"])
        self.assertEqual("decision_pending", fixture["hashes_allowed_next"])
        self.assertEqual(RECOMMENDED_HASH_NEXT_STEP, fixture["recommended_next_step"])
        for field in DECISION_FALSE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)
        self.assertEqual([], collect_decision_fixture_errors())

    def test_self_test_uses_temp_workspace_only(self) -> None:
        run_self_test()

    def test_cli_self_test_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_private_input_adapter_dry_run.py",
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
        self.assertNotIn(PRIVATE_CONTENT, completed.stdout)

    def test_check_all_registers_review_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/review_private_input_adapter_dry_run.py", text)
        self.assertIn("--self-test", text)


def _write_valid_summary(root: Path) -> Path:
    private_file = root / PRIVATE_INPUT_ROOT / "selected.txt"
    private_file.parent.mkdir(parents=True)
    private_file.write_text(PRIVATE_CONTENT, encoding="utf-8")
    summary = build_dry_run_summary(
        Path(PRIVATE_INPUT_ROOT) / "selected.txt",
        root=root,
        verbose=False,
    )
    summary_path = root / PRIVATE_OUTPUT_ROOT / "dry-run-summary.json"
    write_summary(summary, summary_path)
    return summary_path


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
