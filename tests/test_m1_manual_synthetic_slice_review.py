from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m1_manual_synthetic_slice import (
    FALSE_SAFETY_FIELDS,
    PRIVATE_REPORT_ROOT,
    PRIVATE_REVIEW_ROOT,
    RECOMMENDED_NEXT_STEP,
    REPORT_SCHEMA_VERSION,
    REVIEW_SCHEMA_VERSION,
    M1ManualSyntheticSliceReviewError,
    build_review,
    collect_report_errors,
    resolve_report_path,
    resolve_review_output_path,
    run_self_test,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/m1_manual_synthetic_slice_review_report.synthetic.json"


class M1ManualSyntheticSliceReviewTests(unittest.TestCase):
    def test_fixture_review_passes_and_is_redacted(self) -> None:
        report = load_json(FIXTURE_PATH)
        review = build_review(report)
        rendered = json.dumps(review, sort_keys=True)

        self.assertEqual(REPORT_SCHEMA_VERSION, report["schema_version"])
        self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
        self.assertTrue(review["report_valid"])
        self.assertTrue(review["manual_verification_complete"])
        self.assertTrue(review["user_reviews_synthetic_slice_and_overlay_mock"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, review["recommended_next_step"])
        self.assertNotIn("C:\\", rendered)
        self.assertNotIn("raw payload", rendered.lower())

    def test_rejects_missing_review_fields(self) -> None:
        report = load_json(FIXTURE_PATH)
        for field in (
            "owner_chat_attestation_recorded",
            "fake_game_event_reviewed",
            "context_packet_reviewed",
            "translation_orchestrator_mock_reviewed",
            "overlay_mock_reviewed",
            "synthetic_flow_understandable",
            "m1_strict_completion_approved",
        ):
            with self.subTest(field=field):
                mutated = copy.deepcopy(report)
                mutated[field] = False
                self.assertNotEqual([], collect_report_errors(mutated))

    def test_rejects_true_safety_flags_and_unsafe_markers(self) -> None:
        report = load_json(FIXTURE_PATH)
        for field in FALSE_SAFETY_FIELDS:
            with self.subTest(field=field):
                mutated = copy.deepcopy(report)
                mutated[field] = True
                self.assertNotEqual([], collect_report_errors(mutated))

        for marker in (
            "C:\\Users\\local\\secret",
            "raw payload dump",
            "LogOutput.log",
            "https://example.invalid",
            "api_key=secret",
        ):
            with self.subTest(marker=marker):
                mutated = copy.deepcopy(report)
                mutated["unsafe_note"] = marker
                self.assertNotEqual([], collect_report_errors(mutated))

    def test_path_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            report = root / PRIVATE_REPORT_ROOT / "report.json"
            output = root / PRIVATE_REVIEW_ROOT / "review.json"
            self.assertEqual(report.resolve(strict=False), resolve_report_path(report, root=root))
            self.assertEqual(
                output.resolve(strict=False), resolve_review_output_path(output, root=root)
            )
            for path in (
                Path("docs/report.json"),
                Path(PRIVATE_REPORT_ROOT) / "../report.json",
                Path(PRIVATE_REPORT_ROOT) / "raw-log.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M1ManualSyntheticSliceReviewError):
                        resolve_report_path(path, root=root)

    def test_self_test_and_cli_quiet(self) -> None:
        self.assertTrue(run_self_test()["ok"])
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_m1_manual_synthetic_slice.py",
                "--self-test",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stdout)
        self.assertIn("passed", completed.stdout)

    def test_check_all_registration(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        self.assertIn("scripts/review_m1_manual_synthetic_slice.py", text)


if __name__ == "__main__":
    unittest.main()
