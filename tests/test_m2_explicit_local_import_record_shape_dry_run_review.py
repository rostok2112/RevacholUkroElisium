from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m2_explicit_local_import_record_shape_dry_run import (
    DECISION_FALSE_FIELDS,
    DECISION_FIXTURE_PATH,
    RECOMMENDED_CONTEXT_EDGE_CONTRACT_STEP,
    RECOMMENDED_REPEAT_DRY_RUN_STEP,
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    M2ExplicitLocalImportRecordShapeDryRunReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_summary_errors,
    resolve_review_output_path,
    resolve_summary_input_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.run_m2_explicit_local_import_record_shape_dry_run import (
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    build_m2_explicit_local_import_record_shape_dry_run,
    write_summary,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_CONTENT = "PRIVATE_RECORD_VALUE_SHOULD_NOT_LEAK"


class M2ExplicitLocalImportRecordShapeDryRunReviewTests(unittest.TestCase):
    def test_compatible_summary_reviews_after_private_export_is_removed(self) -> None:
        with _fake_repo() as root:
            summary_path, private_file = _write_compatible_summary(root)
            private_file.unlink()

            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["summary_valid"])
            self.assertEqual("compatible", review["record_shape_status"])
            self.assertEqual(1, review["records_count"])
            self.assertEqual(1, review["records_inspected_count"])
            self.assertEqual(1, review["compatible_record_count"])
            self.assertEqual(0, review["incompatible_record_count"])
            self.assertTrue(review["ready_for_context_edge_shape_contract_decision"])
            self.assertFalse(review["context_edge_inspection_allowed_next"])
            self.assertFalse(review["private_export_reopened_during_review"])
            self.assertEqual(
                RECOMMENDED_CONTEXT_EDGE_CONTRACT_STEP,
                review["recommended_next_step"],
            )
            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)

    def test_incompatible_and_decode_failed_summaries_are_reviewable_but_blocked(self) -> None:
        with _fake_repo() as root:
            for label, contents, expected_status in (
                (
                    "incompatible",
                    json.dumps(
                        {
                            "schema_version": "m2-local-private-export.v1",
                            "source_kind": "private_export",
                            "records": [{"record_id": PRIVATE_CONTENT}],
                            "context_edges": [],
                            "metadata": {},
                        }
                    ),
                    "incompatible",
                ),
                ("decode-failed", "{", "decode_failed"),
            ):
                with self.subTest(label=label):
                    summary_path = _write_summary_for_private_contents(root, label, contents)
                    review = build_review(
                        load_json(summary_path),
                        summary_path=summary_path,
                        root=root,
                    )
                    self.assertTrue(review["summary_valid"])
                    self.assertEqual(expected_status, review["record_shape_status"])
                    self.assertFalse(review["ready_for_context_edge_shape_contract_decision"])
                    self.assertNotEqual([], review["blockers"])
                    self.assertEqual(
                        RECOMMENDED_REPEAT_DRY_RUN_STEP,
                        review["recommended_next_step"],
                    )

    def test_malformed_summary_and_count_inconsistencies_are_rejected_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path, _private_file = _write_compatible_summary(root)
            cases = (
                ("schema_version", "wrong"),
                ("records_inspected_count", 99),
                ("compatible_record_count", 0),
                ("incompatible_record_count", 1),
            )
            for field, value in cases:
                with self.subTest(field=field):
                    payload = load_json(summary_path)
                    payload[field] = value
                    review = build_review(payload, summary_path=summary_path, root=root)
                    self.assertFalse(review["summary_valid"])
                    self.assertFalse(review["ready_for_context_edge_shape_contract_decision"])
                    self.assertNotEqual([], review["blockers"])
                    self.assertNotIn(PRIVATE_CONTENT, json.dumps(review, sort_keys=True))

    def test_summary_and_output_path_bounds_are_enforced(self) -> None:
        with _fake_repo() as root:
            outside = root / "workspace/synthetic-slice/summary.json"
            outside.parent.mkdir(parents=True)
            outside.write_text("{}", encoding="utf-8")
            with self.assertRaises(M2ExplicitLocalImportRecordShapeDryRunReviewError):
                resolve_summary_input_path(outside, root=root)

            for path in (
                Path(PRIVATE_OUTPUT_ROOT) / "review.json",
                Path("workspace/synthetic-slice/review.json"),
                Path(REVIEW_OUTPUT_ROOT) / "../review.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M2ExplicitLocalImportRecordShapeDryRunReviewError):
                        resolve_review_output_path(path, root=root)

    def test_json_and_markdown_reviews_are_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path, private_file = _write_compatible_summary(root)
            private_file.unlink()
            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            json_path = resolve_review_output_path(
                Path(REVIEW_OUTPUT_ROOT) / "review.json", root=root
            )
            markdown_path = resolve_review_output_path(
                Path(REVIEW_OUTPUT_ROOT) / "review.md",
                root=root,
            )

            write_json_review(review, json_path)
            write_markdown_review(review, markdown_path)
            rendered = json_path.read_text(encoding="utf-8") + markdown_path.read_text(
                encoding="utf-8"
            )

            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)
            self.assertNotIn("selected-export.json", rendered)
            self.assertIn("context_edge_inspection_allowed_next: no", rendered)

    def test_unsafe_marker_and_true_safety_flag_are_rejected(self) -> None:
        with _fake_repo() as root:
            summary_path, _private_file = _write_compatible_summary(root)
            for field, value in (
                ("unsafe_note", "raw payload dump"),
                ("record_values_inspected", True),
                ("context_edges_traversed", True),
                ("hashes_computed", True),
                ("record_shape_status", "unknown"),
            ):
                with self.subTest(field=field):
                    payload = load_json(summary_path)
                    payload[field] = value
                    errors = collect_summary_errors(payload, summary_path=summary_path, root=root)
                    self.assertNotEqual([], errors)

    def test_decision_fixture_is_safe(self) -> None:
        payload = load_json(DECISION_FIXTURE_PATH)

        self.assertEqual([], collect_decision_fixture_errors())
        self.assertEqual("M2", payload["roadmap_milestone"])
        self.assertEqual(RECOMMENDED_CONTEXT_EDGE_CONTRACT_STEP, payload["recommended_next_step"])
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

    def test_self_test_and_quiet_cli_use_temp_workspace_only(self) -> None:
        run_self_test()
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_record_shape_dry_run.py",
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

        self.assertIn(
            "scripts/review_m2_explicit_local_import_record_shape_dry_run.py",
            text,
        )
        self.assertIn("--self-test", text)


def _write_compatible_summary(root: Path) -> tuple[Path, Path]:
    private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
    private_file.parent.mkdir(parents=True)
    private_file.write_text(json.dumps(_compatible_payload()), encoding="utf-8")
    summary = build_m2_explicit_local_import_record_shape_dry_run(
        Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
        root=root,
    )
    summary_path = root / PRIVATE_OUTPUT_ROOT / "summary.json"
    write_summary(summary, summary_path)
    return summary_path, private_file


def _write_summary_for_private_contents(root: Path, label: str, contents: str) -> Path:
    private_file = root / PRIVATE_INPUT_ROOT / f"{label}.json"
    private_file.parent.mkdir(parents=True, exist_ok=True)
    private_file.write_text(contents, encoding="utf-8")
    summary = build_m2_explicit_local_import_record_shape_dry_run(
        Path(PRIVATE_INPUT_ROOT) / f"{label}.json",
        root=root,
    )
    summary_path = root / PRIVATE_OUTPUT_ROOT / f"{label}-summary.json"
    write_summary(summary, summary_path)
    return summary_path


def _compatible_payload() -> dict[str, object]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            {
                "record_id": PRIVATE_CONTENT,
                "line_id": PRIVATE_CONTENT,
                "conversation_id": PRIVATE_CONTENT,
                "speaker_id": PRIVATE_CONTENT,
                "speaker_label": PRIVATE_CONTENT,
                "context_placeholder": PRIVATE_CONTENT,
                "source_text": PRIVATE_CONTENT,
                "context_tags": [PRIVATE_CONTENT],
                "redacted_metadata": {"nested": PRIVATE_CONTENT},
            }
        ],
        "context_edges": [{"nested": PRIVATE_CONTENT}],
        "metadata": {"nested": PRIVATE_CONTENT},
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
