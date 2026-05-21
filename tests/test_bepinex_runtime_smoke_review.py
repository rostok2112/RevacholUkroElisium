from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.check_bepinex_runtime_smoke_report import (
    REPORT_ROOT,
    canonical_json,
    default_report_template,
)
from scripts.review_bepinex_runtime_smoke_report import (
    REVIEW_ROOT,
    BepInExRuntimeSmokeReviewError,
    build_runtime_smoke_review,
    ensure_safe_review_output_path,
)


ROOT = Path(__file__).resolve().parents[1]
CHECK_ALL = ROOT / "scripts/check_all.py"


class BepInExRuntimeSmokeReviewTests(unittest.TestCase):
    def test_valid_pass_report_reviews_as_ready(self) -> None:
        path = _write_report(_ready_report(), "unit-ready-report.json")
        try:
            review = build_runtime_smoke_review(path)
        finally:
            _delete(path)

        self.assertTrue(review["ready_for_next_phase"])
        self.assertEqual([], review["blockers"])
        self.assertEqual("pass", review["source_report_status"])
        self.assertTrue(review["evidence_summary_redacted"])
        self.assertFalse(review["logs_read"])
        self.assertFalse(review["game_files_read"])
        self.assertFalse(review["companion_called"])
        self.assertFalse(review["provider_called"])

    def test_partial_fail_and_not_run_reports_are_not_ready(self) -> None:
        for status in ("partial", "fail", "not_run"):
            with self.subTest(status=status):
                report = _ready_report()
                report["smoke_status"] = status
                path = _write_report(report, f"unit-{status}-report.json")
                try:
                    review = build_runtime_smoke_review(path)
                finally:
                    _delete(path)

                self.assertFalse(review["ready_for_next_phase"])
                self.assertIn(f"report_status_not_pass:{status}", review["blockers"])

    def test_missing_plugin_loaded_blocks_readiness(self) -> None:
        report = _ready_report()
        report["plugin_loaded_observed"] = False

        review = _review_for(report, "unit-missing-plugin-report.json")

        self.assertFalse(review["ready_for_next_phase"])
        self.assertIn("plugin_loaded_not_observed", review["blockers"])

    def test_missing_health_check_blocks_readiness(self) -> None:
        report = _ready_report()
        report["health_check_observed"] = False

        review = _review_for(report, "unit-missing-health-report.json")

        self.assertFalse(review["ready_for_next_phase"])
        self.assertIn("health_check_not_observed", review["blockers"])

    def test_missing_companion_observation_blocks_readiness(self) -> None:
        report = _ready_report()
        report["companion_available_observed"] = False
        report["companion_unavailable_observed"] = False

        review = _review_for(report, "unit-missing-companion-report.json")

        self.assertFalse(review["ready_for_next_phase"])
        self.assertIn("companion_availability_not_observed", review["blockers"])

    def test_unavailable_case_without_continuation_blocks_readiness(self) -> None:
        report = _ready_report()
        report["companion_available_observed"] = False
        report["companion_unavailable_observed"] = True
        report["game_continued_when_companion_unavailable"] = False

        review = _review_for(report, "unit-unavailable-no-continuation-report.json")

        self.assertFalse(review["ready_for_next_phase"])
        self.assertIn("game_continued_when_companion_unavailable_not_observed", review["blockers"])

    def test_synthetic_send_not_run_with_safe_reason_is_ready(self) -> None:
        report = _ready_report()
        report["synthetic_send_enabled"] = False
        report["synthetic_send_observed"] = False
        report["synthetic_send_not_run_reason"] = "Synthetic send intentionally disabled."

        review = _review_for(report, "unit-send-not-run-report.json")

        self.assertTrue(review["ready_for_next_phase"])

    def test_synthetic_send_missing_reason_blocks_readiness(self) -> None:
        report = _ready_report()
        report["synthetic_send_enabled"] = False
        report["synthetic_send_observed"] = False
        report["synthetic_send_not_run_reason"] = ""

        review = _review_for(report, "unit-send-missing-reason-report.json")

        self.assertFalse(review["ready_for_next_phase"])
        self.assertIn("synthetic_send_not_observed_or_explained", review["blockers"])

    def test_forbidden_markers_are_rejected_by_review(self) -> None:
        report = _ready_report()
        report["evidence_summary"] = "Pasted LogOutput.log by mistake."
        path = _write_report(report, "unit-forbidden-marker-report.json")
        try:
            with self.assertRaises(BepInExRuntimeSmokeReviewError):
                build_runtime_smoke_review(path)
        finally:
            _delete(path)

    def test_unsafe_report_path_is_rejected(self) -> None:
        with self.assertRaises(Exception):
            build_runtime_smoke_review(Path("docs/manual-smoke/report.json"))

    def test_output_path_safety(self) -> None:
        safe_json = ensure_safe_review_output_path(REVIEW_ROOT / "summary.json", ".json")
        safe_markdown = ensure_safe_review_output_path(REVIEW_ROOT / "summary.md", ".md")

        self.assertEqual(REVIEW_ROOT / "summary.json", safe_json)
        self.assertEqual(REVIEW_ROOT / "summary.md", safe_markdown)
        with self.assertRaises(BepInExRuntimeSmokeReviewError):
            ensure_safe_review_output_path(REPORT_ROOT / "summary.json", ".json")
        with self.assertRaises(BepInExRuntimeSmokeReviewError):
            ensure_safe_review_output_path(REVIEW_ROOT / "summary.txt", ".json")

    def test_cli_writes_redacted_json_and_markdown_outputs(self) -> None:
        report = _ready_report()
        report["notes_redacted"] = "Unique safe note that must not appear in review."
        report["evidence_summary"] = "Unique safe evidence that must not appear in review."
        report_path = _write_report(report, "unit-cli-ready-report.json")
        json_output = REVIEW_ROOT / "unit-review.json"
        markdown_output = REVIEW_ROOT / "unit-review.md"
        for path in (json_output, markdown_output):
            _delete(path)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/review_bepinex_runtime_smoke_report.py",
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

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("ready", completed.stdout)
            self.assertTrue(json_output.exists())
            self.assertTrue(markdown_output.exists())
            rendered = json_output.read_text(encoding="utf-8") + markdown_output.read_text(
                encoding="utf-8"
            )
            self.assertNotIn("Unique safe note", rendered)
            self.assertNotIn("Unique safe evidence", rendered)
            self.assertNotIn("LogOutput.log", rendered)
            self.assertNotIn("raw_english_text", rendered)
            self.assertNotIn("C:\\Users", rendered)
        finally:
            for path in (report_path, json_output, markdown_output):
                _delete(path)

    def test_cli_rejects_unsafe_review_output_path(self) -> None:
        report_path = _write_report(_ready_report(), "unit-unsafe-output-report.json")
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/review_bepinex_runtime_smoke_report.py",
                    "--report",
                    str(report_path),
                    "--output",
                    "docs/manual-smoke/review.json",
                    "--quiet",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        finally:
            _delete(report_path)

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("failed", completed.stdout)

    def test_check_all_does_not_require_a_real_runtime_report(self) -> None:
        check_all = CHECK_ALL.read_text(encoding="utf-8")

        self.assertNotIn("review_bepinex_runtime_smoke_report.py", check_all)


def _ready_report() -> dict[str, object]:
    report = deepcopy(default_report_template())
    report.update(
        {
            "smoke_status": "pass",
            "build_attempted": True,
            "build_succeeded": True,
            "plugin_loaded_observed": True,
            "health_check_observed": True,
            "companion_available_observed": True,
            "companion_unavailable_observed": False,
            "synthetic_send_enabled": False,
            "synthetic_send_observed": False,
            "companion_received_synthetic_event": False,
            "game_continued_when_companion_unavailable": False,
            "warnings_count": 0,
            "msb3277_warning_count": 0,
            "synthetic_send_not_run_reason": "Synthetic send intentionally disabled.",
            "unavailable_case_not_run_reason": "Companion stayed available during this smoke.",
            "evidence_summary_redacted": True,
            "notes_redacted": "Safe metadata-only note.",
            "evidence_summary": "Safe metadata-only evidence.",
            "created_by_user_manually": True,
        }
    )
    return report


def _review_for(report: dict[str, object], name: str) -> dict[str, object]:
    path = _write_report(report, name)
    try:
        return build_runtime_smoke_review(path)
    finally:
        _delete(path)


def _write_report(report: dict[str, object], name: str) -> Path:
    path = REPORT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(report), encoding="utf-8")
    return path


def _delete(path: Path) -> None:
    if path.exists():
        path.unlink()


if __name__ == "__main__":
    unittest.main()
