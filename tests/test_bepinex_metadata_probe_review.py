from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.check_bepinex_metadata_probe_report import (
    REPORT_ROOT,
    canonical_json,
    default_metadata_probe_report_template,
)
from scripts.review_bepinex_metadata_probe_report import (
    REVIEW_ROOT,
    BepInExMetadataProbeReviewError,
    build_metadata_probe_review,
    ensure_safe_metadata_probe_review_output_path,
)


ROOT = Path(__file__).resolve().parents[1]
CHECK_ALL = ROOT / "scripts/check_all.py"


class BepInExMetadataProbeReviewTests(unittest.TestCase):
    def test_valid_pass_report_reviews_as_ready(self) -> None:
        review = _review_for(_ready_report(), "unit-ready-metadata-probe-report.json")

        self.assertEqual("ready", review["readiness_status"])
        self.assertEqual([], review["blockers"])
        self.assertEqual("pass", review["report_status"])
        self.assertTrue(review["evidence_summary_redacted"])
        self.assertFalse(review["logs_read"])
        self.assertFalse(review["game_files_read"])
        self.assertFalse(review["screenshots_read"])
        self.assertFalse(review["companion_called"])
        self.assertFalse(review["provider_called"])
        self.assertIn("does not approve", review["recommended_next_step"])

    def test_not_run_partial_and_fail_reports_are_not_ready(self) -> None:
        for status in ("not_run", "partial", "fail"):
            with self.subTest(status=status):
                report = _ready_report()
                report["probe_status"] = status

                review = _review_for(report, f"unit-{status}-metadata-probe-report.json")

                self.assertEqual("not_ready", review["readiness_status"])
                self.assertIn(f"report_status_not_pass:{status}", review["blockers"])

    def test_real_text_captured_true_is_rejected_by_validation(self) -> None:
        report = _ready_report()
        report["real_text_captured"] = True

        with self.assertRaises(BepInExMetadataProbeReviewError):
            _review_for(report, "unit-real-text-metadata-probe-report.json")

    def test_current_line_capture_enabled_true_is_rejected_by_validation(self) -> None:
        report = _ready_report()
        report["current_line_capture_enabled"] = True

        with self.assertRaises(BepInExMetadataProbeReviewError):
            _review_for(report, "unit-current-line-metadata-probe-report.json")

    def test_ui_probe_attempted_blocks_readiness(self) -> None:
        report = _ready_report()
        report["ui_probe_attempted"] = True

        review = _review_for(report, "unit-ui-probe-metadata-probe-report.json")

        self.assertEqual("not_ready", review["readiness_status"])
        self.assertIn("ui_probe_attempted_not_false", review["blockers"])

    def test_scene_probe_attempted_blocks_readiness(self) -> None:
        report = _ready_report()
        report["scene_probe_attempted"] = True

        review = _review_for(report, "unit-scene-probe-metadata-probe-report.json")

        self.assertEqual("not_ready", review["readiness_status"])
        self.assertIn("scene_probe_attempted_not_false", review["blockers"])

    def test_missing_probe_completed_blocks_readiness(self) -> None:
        report = _ready_report()
        report["probe_completed"] = False

        review = _review_for(report, "unit-incomplete-metadata-probe-report.json")

        self.assertEqual("not_ready", review["readiness_status"])
        self.assertIn("probe_not_completed", review["blockers"])

    def test_forbidden_markers_are_rejected_by_review(self) -> None:
        report = _ready_report()
        report["redacted_notes"] = "Pasted LogOutput.log by mistake."

        with self.assertRaises(BepInExMetadataProbeReviewError):
            _review_for(report, "unit-forbidden-marker-metadata-probe-report.json")

    def test_unsafe_report_path_is_rejected(self) -> None:
        with self.assertRaises(Exception):
            build_metadata_probe_review(Path("docs/manual-smoke/metadata-probe.json"))

    def test_output_path_safety(self) -> None:
        safe_json = ensure_safe_metadata_probe_review_output_path(
            REVIEW_ROOT / "summary.json", ".json"
        )
        safe_markdown = ensure_safe_metadata_probe_review_output_path(
            REVIEW_ROOT / "summary.md", ".md"
        )

        self.assertEqual(REVIEW_ROOT / "summary.json", safe_json)
        self.assertEqual(REVIEW_ROOT / "summary.md", safe_markdown)
        with self.assertRaises(BepInExMetadataProbeReviewError):
            ensure_safe_metadata_probe_review_output_path(REPORT_ROOT / "summary.json", ".json")
        with self.assertRaises(BepInExMetadataProbeReviewError):
            ensure_safe_metadata_probe_review_output_path(REVIEW_ROOT / "summary.txt", ".json")

    def test_cli_writes_redacted_json_and_markdown_outputs(self) -> None:
        report = _ready_report()
        report["redacted_notes"] = "Unique safe note that must not appear in review."
        report_path = _write_report(report, "unit-cli-ready-metadata-probe-report.json")
        json_output = REVIEW_ROOT / "unit-metadata-probe-review.json"
        markdown_output = REVIEW_ROOT / "unit-metadata-probe-review.md"
        for path in (json_output, markdown_output):
            _delete(path)
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/review_bepinex_metadata_probe_report.py",
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
            self.assertNotIn("LogOutput.log", rendered)
            self.assertNotIn("raw_english_text", rendered)
            self.assertNotIn("C:\\Users", rendered)
            self.assertIn("Evidence summary redacted", rendered)
            self.assertIn("Provider called: `false`", rendered)
        finally:
            for path in (report_path, json_output, markdown_output):
                _delete(path)

    def test_cli_rejects_unsafe_review_output_path(self) -> None:
        report_path = _write_report(_ready_report(), "unit-unsafe-output-metadata-report.json")
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/review_bepinex_metadata_probe_report.py",
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

    def test_check_all_does_not_require_a_real_metadata_probe_report(self) -> None:
        check_all = CHECK_ALL.read_text(encoding="utf-8")

        self.assertNotIn("review_bepinex_metadata_probe_report.py", check_all)


def _ready_report() -> dict[str, object]:
    report = deepcopy(default_metadata_probe_report_template())
    report.update(
        {
            "probe_status": "pass",
            "metadata_only": True,
            "probe_enabled": True,
            "probe_attempted": True,
            "probe_completed": True,
            "plugin_loaded": True,
            "companion_health_checked": True,
            "companion_available": True,
            "synthetic_event_send_configured": False,
            "synthetic_event_sent": False,
            "scene_probe_attempted": False,
            "ui_probe_attempted": False,
            "current_line_capture_enabled": False,
            "real_text_captured": False,
            "counters": {
                "metadata_snapshot_created_count": 1,
                "health_check_observed_count": 1,
                "synthetic_send_configured_count": 0,
                "safe_status_events": 1,
                "synthetic_events": 0,
            },
            "blockers": [],
            "next_step_notes": "Ready for discussion only.",
            "not_run_reason": "",
            "evidence_summary_redacted": True,
            "redacted_notes": "Safe metadata-only note.",
            "created_by_user_manually": True,
        }
    )
    return report


def _review_for(report: dict[str, object], name: str) -> dict[str, object]:
    path = _write_report(report, name)
    try:
        return build_metadata_probe_review(path)
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
