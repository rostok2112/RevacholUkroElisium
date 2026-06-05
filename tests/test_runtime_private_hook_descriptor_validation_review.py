from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import unittest

from scripts.review_runtime_private_hook_descriptor_local_validation import (
    DECISION_FIXTURE_PATH,
    READY_NEXT_STEP,
    REPEAT_NEXT_STEP,
    REVIEW_ROOT,
    REVIEW_SCHEMA_VERSION,
    RuntimePrivateHookDescriptorValidationReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_summary_errors,
    ensure_safe_review_output_path,
    ensure_safe_summary_path,
    main,
    run_self_test,
)
from scripts.run_runtime_private_hook_descriptor_local_validation import (
    VALIDATION_ROOT,
    canonical_json,
)
from scripts.schema_validator import load_json
from scripts.synthetic_slice import ROOT


SUMMARY_FIXTURE = (
    ROOT / "tests/fixtures/runtime_private_hook_descriptor_local_validation_summary.synthetic.json"
)
CHECK_ALL = ROOT / "scripts/check_all.py"
PRIVATE_MARKERS = (
    "PrivateCandidate",
    "BuildRuntimeLineCandidate",
    "LogOutput.log",
    "provider payload",
    "runtime-private-descriptor.json",
)


class RuntimePrivateHookDescriptorValidationReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        VALIDATION_ROOT.mkdir(parents=True, exist_ok=True)
        REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
        self.summary_path = VALIDATION_ROOT / "test-summary.json"

    def tearDown(self) -> None:
        self.summary_path.unlink(missing_ok=True)
        (REVIEW_ROOT / "test-review.json").unlink(missing_ok=True)
        (REVIEW_ROOT / "test-review.md").unlink(missing_ok=True)

    def test_ready_review_advances_to_hook_implementation_contract(self) -> None:
        self.write_summary(_ready_summary())

        review = build_review(self.summary_path)

        self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
        self.assertTrue(review["ready_for_hook_implementation_contract"])
        self.assertEqual(READY_NEXT_STEP, review["recommended_next_step"])
        self.assert_review_redacted(review)

    def test_incompatible_and_decode_failed_summaries_repeat_validation(self) -> None:
        for status in ("incompatible", "decode_failed"):
            summary = _ready_summary()
            summary.update(
                {
                    "validation_status": status,
                    "descriptor_compatible": False,
                    "blocker_categories": ["summary_status_not_compatible"],
                    "recommended_next_step": REPEAT_NEXT_STEP,
                }
            )
            self.write_summary(summary)

            review = build_review(self.summary_path)

            self.assertFalse(review["ready_for_hook_implementation_contract"])
            self.assertEqual(REPEAT_NEXT_STEP, review["recommended_next_step"])
            self.assert_review_redacted(review)

    def test_malformed_summary_is_blocked(self) -> None:
        self.summary_path.write_text("{", encoding="utf-8")

        with self.assertRaises(RuntimePrivateHookDescriptorValidationReviewError):
            build_review(self.summary_path)

    def test_summary_true_forbidden_flag_is_blocked(self) -> None:
        summary = _ready_summary()
        summary["provider_execution_allowed_next"] = True
        self.write_summary(summary)

        review = build_review(self.summary_path)

        self.assertFalse(review["ready_for_hook_implementation_contract"])
        self.assertIn("forbidden_capability_enabled", review["blockers"])

    def test_unsafe_markers_are_rejected(self) -> None:
        summary = _ready_summary()
        summary["blocker_categories"] = ["PrivateCandidate Controller LogOutput.log"]
        self.assertNotEqual([], collect_summary_errors(summary))

    def test_unsafe_input_and_output_paths_are_rejected(self) -> None:
        with self.assertRaises(RuntimePrivateHookDescriptorValidationReviewError):
            ensure_safe_summary_path(Path("docs/summary.json"))
        with self.assertRaises(RuntimePrivateHookDescriptorValidationReviewError):
            ensure_safe_review_output_path(Path("docs/review.json"), ".json")
        with self.assertRaises(RuntimePrivateHookDescriptorValidationReviewError):
            ensure_safe_review_output_path(
                Path(
                    "workspace/local-private/runtime-capture/hook-descriptors/"
                    "validation-review/../bad.json"
                ),
                ".json",
            )

    def test_review_json_and_markdown_are_redacted(self) -> None:
        self.write_summary(_ready_summary())
        json_path = REVIEW_ROOT / "test-review.json"
        markdown_path = REVIEW_ROOT / "test-review.md"
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            result = main(
                [
                    "--summary",
                    str(self.summary_path),
                    "--output",
                    str(json_path),
                    "--markdown-output",
                    str(markdown_path),
                ]
            )

        self.assertEqual(0, result)
        self.assert_review_redacted(json.loads(stdout.getvalue()))
        self.assert_review_redacted(load_json(json_path))
        markdown = markdown_path.read_text(encoding="utf-8")
        for marker in PRIVATE_MARKERS:
            self.assertNotIn(marker, markdown)
        self.assertIn(READY_NEXT_STEP, markdown)

    def test_quiet_cli(self) -> None:
        self.write_summary(_ready_summary())
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            result = main(["--summary", str(self.summary_path), "--quiet"])

        self.assertEqual(0, result)
        self.assertIn("ready", stdout.getvalue())
        for marker in PRIVATE_MARKERS:
            self.assertNotIn(marker, stdout.getvalue())

    def test_decision_fixture_is_safe(self) -> None:
        self.assertEqual([], collect_decision_fixture_errors())
        fixture = load_json(DECISION_FIXTURE_PATH)

        self.assertEqual(READY_NEXT_STEP, fixture["recommended_next_step"])
        self.assertFalse(fixture["descriptor_reopened_during_review"])

    def test_self_test(self) -> None:
        run_self_test()

    def test_check_all_registration(self) -> None:
        text = CHECK_ALL.read_text(encoding="utf-8")

        self.assertIn("scripts/review_runtime_private_hook_descriptor_local_validation.py", text)

    def write_summary(self, summary: dict[str, object]) -> None:
        self.summary_path.write_text(canonical_json(summary), encoding="utf-8")

    def assert_review_redacted(self, review: dict[str, object]) -> None:
        rendered = json.dumps(review, sort_keys=True)
        for marker in (*PRIVATE_MARKERS, str(VALIDATION_ROOT), str(REVIEW_ROOT)):
            self.assertNotIn(marker, rendered)
        for field in (
            "descriptor_path_included",
            "descriptor_filename_included",
            "candidate_identifiers_included",
            "method_names_included",
            "method_signatures_included",
            "source_text_included",
            "payload_dumps_included",
            "raw_logs_included",
            "screenshots_included",
            "provider_data_included",
            "private_paths_included",
            "hook_implementation_allowed_next",
            "real_text_capture_allowed_next",
        ):
            self.assertFalse(review[field])


def _ready_summary() -> dict[str, object]:
    return copy.deepcopy(load_json(SUMMARY_FIXTURE))


if __name__ == "__main__":
    unittest.main()
