from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_dry_run_summary_hash import (
    DECISION_FALSE_FIELDS,
    HASH_REVIEW_OUTPUT_ROOT,
    RECOMMENDED_INDEX_CONTRACT_STEP,
    REVIEW_SCHEMA_VERSION,
    DryRunSummaryHashReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_hash_output_errors,
    resolve_hash_input_path,
    resolve_review_output_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.run_dry_run_summary_hash import HASH_OUTPUT_ROOT
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
HASH_FIXTURE = ROOT / "tests/fixtures/dry_run_summary_hash.synthetic.json"
DECISION_FIXTURE = ROOT / "tests/fixtures/dry_run_summary_hash_decision.synthetic.json"
PRIVATE_CONTENT = "PRIVATE_CONTENT_SHOULD_NOT_LEAK"


class DryRunSummaryHashReviewTests(unittest.TestCase):
    def test_valid_hash_output_reviews_successfully(self) -> None:
        with _fake_repo() as root:
            hash_path = _write_hash(root, _fixture_hash())

            review = build_review(load_json(hash_path), hash_path=hash_path, root=root)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["hash_output_valid"])
            self.assertTrue(review["digest_present"])
            self.assertTrue(review["ready_for_private_index_decision"])
            self.assertFalse(review["private_index_construction_allowed_next"])
            self.assertEqual(RECOMMENDED_INDEX_CONTRACT_STEP, review["recommended_next_step"])
            self.assertEqual([], review["blockers"])

    def test_malformed_hash_output_rejected(self) -> None:
        with _fake_repo() as root:
            hash_path = _write_hash(root, {"schema_version": "wrong"})

            review = build_review(load_json(hash_path), hash_path=hash_path, root=root)

            self.assertFalse(review["hash_output_valid"])
            self.assertFalse(review["ready_for_private_index_decision"])
            self.assertIn("malformed_hash_output", review["blockers"])

    def test_hash_output_outside_private_hash_root_rejected(self) -> None:
        with _fake_repo() as root:
            outside = root / "workspace/local-private/extraction-indexing/hash.json"
            outside.parent.mkdir(parents=True)
            outside.write_text(json.dumps(_fixture_hash()), encoding="utf-8")

            with self.assertRaises(DryRunSummaryHashReviewError):
                resolve_hash_input_path(outside, root=root)

    def test_review_output_path_outside_hash_review_root_rejected(self) -> None:
        with _fake_repo() as root:
            for output in (
                Path("workspace/local-private/extraction-indexing/review/review.json"),
                Path("workspace/synthetic-slice/review.json"),
                Path("../workspace/local-private/extraction-indexing/hash-review/review.json"),
            ):
                with self.subTest(output=output):
                    with self.assertRaises(DryRunSummaryHashReviewError):
                        resolve_review_output_path(output, root=root)

    def test_private_paths_are_redacted_by_default(self) -> None:
        with _fake_repo() as root:
            hash_path = _write_hash(root, _fixture_hash())
            review = build_review(load_json(hash_path), hash_path=hash_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertNotIn(str(root), rendered)
            self.assertFalse(review["private_paths_included"])
            self.assertTrue(review["hash_path_redacted"])

    def test_raw_text_log_payload_markers_are_rejected(self) -> None:
        with _fake_repo() as root:
            for field, value in (
                ("raw_payload", "payload dump"),
                ("raw_log", "LogOutput.log"),
                ("provider_payload", "raw payload"),
            ):
                with self.subTest(field=field):
                    payload = _fixture_hash()
                    payload[field] = value
                    hash_path = _write_hash(root, payload, name=f"{field}.json")

                    errors = collect_hash_output_errors(
                        load_json(hash_path), hash_path=hash_path, root=root
                    )

                    self.assertNotEqual([], errors)

    def test_true_forbidden_hashing_flags_are_rejected(self) -> None:
        with _fake_repo() as root:
            for field in (
                "file_content_hashing",
                "path_string_hashing",
                "filename_hashing",
                "raw_payload_hashing",
                "private_index_construction",
                "real_extraction",
            ):
                with self.subTest(field=field):
                    payload = _fixture_hash()
                    payload[field] = True
                    hash_path = _write_hash(root, payload, name=f"{field}.json")

                    review = build_review(load_json(hash_path), hash_path=hash_path, root=root)

                    self.assertFalse(review["hash_output_valid"])
                    self.assertFalse(review["ready_for_private_index_decision"])

    def test_redacted_json_and_markdown_reviews_do_not_copy_digest_or_private_content(self) -> None:
        with _fake_repo() as root:
            hash_payload = _fixture_hash()
            hash_path = _write_hash(root, hash_payload)
            review = build_review(load_json(hash_path), hash_path=hash_path, root=root)
            json_path = resolve_review_output_path(
                Path(HASH_REVIEW_OUTPUT_ROOT) / "review.json",
                root=root,
            )
            markdown_path = resolve_review_output_path(
                Path(HASH_REVIEW_OUTPUT_ROOT) / "review.md",
                root=root,
            )

            write_json_review(review, json_path)
            write_markdown_review(review, markdown_path)
            rendered_json = json_path.read_text(encoding="utf-8")
            rendered_md = markdown_path.read_text(encoding="utf-8")

            self.assertNotIn(hash_payload["digest"], rendered_json)
            self.assertNotIn(hash_payload["digest"], rendered_md)
            self.assertNotIn(PRIVATE_CONTENT, rendered_json)
            self.assertNotIn(PRIVATE_CONTENT, rendered_md)
            self.assertNotIn(str(root), rendered_json)
            self.assertNotIn(str(root), rendered_md)

    def test_decision_fixture_is_safe(self) -> None:
        self.assertEqual([], collect_decision_fixture_errors(DECISION_FIXTURE))
        payload = load_json(DECISION_FIXTURE)

        self.assertEqual("dry-run-summary-hash-decision.v1", payload["schema_version"])
        self.assertEqual("5A.8", payload["milestone"])
        self.assertTrue(payload["hash_evidence_required"])
        self.assertEqual("decision_pending", payload["private_index_contract_allowed_next"])
        for field in DECISION_FALSE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(payload[field], False)

    def test_decision_fixture_rejects_forbidden_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Path(tmp) / "decision.json"
            payload = load_json(DECISION_FIXTURE)
            for field in DECISION_FALSE_FIELDS:
                with self.subTest(field=field):
                    mutated = dict(payload)
                    mutated[field] = True
                    fixture.write_text(json.dumps(mutated), encoding="utf-8")

                    self.assertNotEqual([], collect_decision_fixture_errors(fixture))

    def test_self_test_uses_temp_workspace_only(self) -> None:
        run_self_test()

    def test_cli_self_test_quiet(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/review_dry_run_summary_hash.py", "--self-test", "--quiet"],
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

        self.assertIn("scripts/review_dry_run_summary_hash.py", text)
        self.assertIn("--self-test", text)


def _fixture_hash() -> dict[str, object]:
    return load_json(HASH_FIXTURE)


def _write_hash(root: Path, payload: dict[str, object], *, name: str = "hash.json") -> Path:
    path = root / HASH_OUTPUT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
