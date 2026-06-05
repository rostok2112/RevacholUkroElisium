from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.check_runtime_targeted_hook_candidate_research_report import (
    READY_NEXT_STEP as REPORT_READY_NEXT_STEP,
    REPORT_ROOT,
    default_report_template,
)
from scripts.review_runtime_targeted_hook_candidate_research_report import (
    DECISION_FIXTURE_PATH,
    READY_NEXT_STEP,
    REPEAT_NEXT_STEP,
    REVIEW_ROOT,
    RuntimeTargetedHookCandidateResearchReviewError,
    build_review,
    collect_decision_fixture_errors,
    ensure_safe_review_output_path,
)


ROOT = Path(__file__).resolve().parents[1]


class RuntimeTargetedHookCandidateResearchReviewTests(unittest.TestCase):
    def test_ready_report_advances_to_decision_contract(self) -> None:
        path = _write_report(_ready_report(), "unit-ready-report.json")
        try:
            review = build_review(path)
        finally:
            path.unlink(missing_ok=True)

        self.assertTrue(review["source_report_valid"])
        self.assertTrue(review["ready_for_hook_candidate_decision"])
        self.assertEqual(READY_NEXT_STEP, review["recommended_next_step"])
        self.assertFalse(review["hook_implementation_allowed_next"])
        self.assertFalse(review["real_text_capture_allowed_next"])

    def test_partial_fail_and_not_run_reports_repeat_local_report(self) -> None:
        for status in ("partial", "fail", "not_run"):
            with self.subTest(status=status):
                report = _ready_report()
                report["research_status"] = status
                report["recommended_next_step"] = REPORT_READY_NEXT_STEP
                if status == "not_run":
                    report["research_performed_locally"] = False
                    report["candidate_count"] = 0
                    report["candidate_categories_count"] = 0
                    report["recommended_next_step"] = (
                        "runtime_targeted_hook_candidate_research_local_report"
                    )
                path = _write_report(report, f"unit-{status}-report.json")
                try:
                    review = build_review(path)
                finally:
                    path.unlink(missing_ok=True)

                self.assertFalse(review["ready_for_hook_candidate_decision"])
                self.assertEqual(REPEAT_NEXT_STEP, review["recommended_next_step"])

    def test_unsafe_report_markers_become_redacted_blockers(self) -> None:
        report = _ready_report()
        report["evidence_summary"] = (
            "HarmonyPatch public void Candidate(string source_text) LogOutput.log "
            "C:\\Users\\local\\secret screenshot request payload Candidate.Controller"
        )
        path = _write_report(report, "unit-unsafe-report.json")
        try:
            review = build_review(path)
        finally:
            path.unlink(missing_ok=True)

        rendered = json.dumps(review, sort_keys=True)
        self.assertFalse(review["source_report_valid"])
        self.assertFalse(review["ready_for_hook_candidate_decision"])
        self.assertIn("unsafe_runtime_evidence_marker", review["blockers"])
        for marker in (
            "HarmonyPatch",
            "LogOutput.log",
            "Candidate.Controller",
            "C:\\Users",
            "request payload",
        ):
            self.assertNotIn(marker, rendered)

    def test_true_forbidden_flag_blocks_review(self) -> None:
        report = _ready_report()
        report["hook_implementation_used"] = True
        path = _write_report(report, "unit-forbidden-flag-report.json")
        try:
            review = build_review(path)
        finally:
            path.unlink(missing_ok=True)

        self.assertFalse(review["source_report_valid"])
        self.assertFalse(review["ready_for_hook_candidate_decision"])
        self.assertIn("forbidden_capability_enabled", review["blockers"])
        self.assertFalse(review["hook_implementation_allowed_next"])

    def test_review_output_path_bounds(self) -> None:
        safe_json = REVIEW_ROOT / "unit-review.json"
        self.assertEqual(safe_json, ensure_safe_review_output_path(safe_json, ".json"))

        with self.assertRaises(RuntimeTargetedHookCandidateResearchReviewError):
            ensure_safe_review_output_path(Path("docs/review.json"), ".json")
        with self.assertRaises(RuntimeTargetedHookCandidateResearchReviewError):
            ensure_safe_review_output_path(REVIEW_ROOT / "review.txt", ".json")

    def test_cli_writes_redacted_json_and_markdown(self) -> None:
        report_path = _write_report(_ready_report(), "unit-cli-ready-report.json")
        json_output = REVIEW_ROOT / "unit-cli-review.json"
        markdown_output = REVIEW_ROOT / "unit-cli-review.md"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_runtime_targeted_hook_candidate_research_report.py",
                "--report",
                str(report_path),
                "--output",
                str(json_output),
                "--markdown-output",
                str(markdown_output),
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(json_output.exists())
            self.assertTrue(markdown_output.exists())
            written = json_output.read_text(encoding="utf-8") + markdown_output.read_text(
                encoding="utf-8"
            )
            self.assertIn(READY_NEXT_STEP, written)
            for marker in ("HarmonyPatch", "LogOutput.log", "Candidate.Controller"):
                self.assertNotIn(marker, written)
        finally:
            report_path.unlink(missing_ok=True)
            json_output.unlink(missing_ok=True)
            markdown_output.unlink(missing_ok=True)

    def test_decision_fixture_validates(self) -> None:
        self.assertTrue(DECISION_FIXTURE_PATH.exists())
        self.assertEqual([], collect_decision_fixture_errors())

    def test_self_test_and_check_all_registration(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_runtime_targeted_hook_candidate_research_report.py",
                "--self-test",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

        check_all = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        self.assertIn(
            "scripts/review_runtime_targeted_hook_candidate_research_report.py", check_all
        )


def _ready_report() -> dict[str, object]:
    report = copy.deepcopy(default_report_template())
    report.update(
        {
            "research_status": "pass",
            "research_performed_locally": True,
            "candidate_count": 2,
            "candidate_categories_count": 1,
            "evidence_summary": "Local targeted research was summarized with aggregate counts.",
            "recommended_next_step": REPORT_READY_NEXT_STEP,
        }
    )
    return report


def _write_report(report: dict[str, object], name: str) -> Path:
    path = REPORT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


if __name__ == "__main__":
    unittest.main()
