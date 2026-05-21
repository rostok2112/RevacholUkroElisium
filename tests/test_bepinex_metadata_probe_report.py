from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.check_bepinex_metadata_probe_report import (
    FIXTURE_PATH,
    REPORT_ROOT,
    BepInExMetadataProbeReportError,
    collect_metadata_probe_report_errors,
    default_metadata_probe_report_template,
    ensure_safe_metadata_probe_report_path,
)


ROOT = Path(__file__).resolve().parents[1]


class BepInExMetadataProbeReportTests(unittest.TestCase):
    def test_committed_fixture_validates(self) -> None:
        self.assertEqual([], collect_metadata_probe_report_errors(FIXTURE_PATH))

    def test_committed_fixture_contains_disabled_probe_skeleton_fields(self) -> None:
        report = _valid_report()

        self.assertFalse(report["probe_enabled"])
        self.assertFalse(report["probe_attempted"])
        self.assertFalse(report["probe_completed"])
        self.assertFalse(report["synthetic_event_send_configured"])
        self.assertFalse(report["real_text_captured"])
        self.assertFalse(report["current_line_capture_enabled"])

    def test_default_template_contains_safe_manual_fields(self) -> None:
        report = default_metadata_probe_report_template()

        self.assertEqual("not_run", report["probe_status"])
        self.assertTrue(report["metadata_only"])
        self.assertFalse(report["probe_enabled"])
        self.assertFalse(report["probe_attempted"])
        self.assertFalse(report["probe_completed"])
        self.assertFalse(report["real_text_captured"])
        self.assertFalse(report["current_line_capture_enabled"])
        self.assertFalse(report["ui_probe_attempted"])
        self.assertFalse(report["scene_probe_attempted"])
        self.assertEqual([], _errors_for(report))

    def test_real_text_captured_true_fails(self) -> None:
        report = _valid_report()
        report["real_text_captured"] = True

        self.assertIn("real_text_captured=false", "\n".join(_errors_for(report)))

    def test_current_line_capture_enabled_true_fails(self) -> None:
        report = _valid_report()
        report["current_line_capture_enabled"] = True

        self.assertIn("current_line_capture_enabled=false", "\n".join(_errors_for(report)))

    def test_probe_attempted_without_enabled_fails(self) -> None:
        report = _valid_report()
        report["probe_attempted"] = True

        self.assertIn("probe_attempted=true", "\n".join(_errors_for(report)))

    def test_probe_completed_without_attempted_fails(self) -> None:
        report = _valid_report()
        report["probe_enabled"] = True
        report["probe_completed"] = True

        self.assertIn("probe_completed=true", "\n".join(_errors_for(report)))

    def test_synthetic_event_sent_without_configured_fails(self) -> None:
        report = _valid_report()
        report["synthetic_event_sent"] = True

        self.assertIn("synthetic_event_sent=true", "\n".join(_errors_for(report)))

    def test_raw_dialogue_like_marker_fails(self) -> None:
        report = _valid_report()
        report["redacted_notes"] = "This report accidentally includes dialogue text."

        self.assertIn("dialogue text", "\n".join(_errors_for(report)))

    def test_screenshot_and_ocr_markers_fail(self) -> None:
        report = _valid_report()
        report["redacted_notes"] = "A screenshot and OCR output were attached."

        errors = "\n".join(_errors_for(report))

        self.assertIn("screenshot", errors)
        self.assertIn("OCR", errors)

    def test_private_path_fails(self) -> None:
        report = _valid_report()
        report["redacted_notes"] = r"Local file was C:\Users\player\Game\probe.json"

        self.assertIn("private absolute path", "\n".join(_errors_for(report)))

    def test_stack_trace_fails(self) -> None:
        report = _valid_report()
        report["redacted_notes"] = "Stack trace: at Revachol.Plugin.Load()"

        self.assertIn("stack trace", "\n".join(_errors_for(report)).lower())

    def test_raw_payload_marker_fails(self) -> None:
        report = _valid_report()
        report["redacted_notes"] = '{"input_type":"fake_event","event":{}}'

        self.assertIn("input_type", "\n".join(_errors_for(report)))

    def test_secret_like_value_fails(self) -> None:
        report = _valid_report()
        report["redacted_notes"] = "api_key=abc123456789"

        self.assertIn("secret", "\n".join(_errors_for(report)).lower())

    def test_non_localhost_url_fails(self) -> None:
        report = _valid_report()
        report["redacted_notes"] = "Checked https://example.invalid/status"

        self.assertIn("non-localhost URL", "\n".join(_errors_for(report)))

    def test_safe_workspace_report_path_allowed(self) -> None:
        path = ensure_safe_metadata_probe_report_path(REPORT_ROOT / "report.json")

        self.assertEqual(REPORT_ROOT / "report.json", path)

    def test_unsafe_report_path_rejected(self) -> None:
        with self.assertRaises(BepInExMetadataProbeReportError):
            ensure_safe_metadata_probe_report_path(Path("docs/metadata-probe/report.json"))

    def test_cli_quiet_validates_fixture(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/check_bepinex_metadata_probe_report.py", "--quiet"],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout)

    def test_cli_rejects_report_outside_workspace(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/check_bepinex_metadata_probe_report.py",
                "--report",
                "docs/manual-smoke/probe.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("workspace", completed.stderr)

    def test_template_writer_writes_workspace_only_template(self) -> None:
        output = REPORT_ROOT / "unit-test-metadata-probe.template.json"
        if output.exists():
            output.unlink()
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/write_bepinex_metadata_probe_report.py",
                    "--output",
                    str(output),
                    "--quiet",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(output.exists())
            self.assertEqual([], collect_metadata_probe_report_errors(output))
        finally:
            if output.exists():
                output.unlink()

    def test_template_writer_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/write_bepinex_metadata_probe_report.py",
                "--output",
                "docs/manual-smoke/metadata-probe.template.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("workspace", completed.stderr)


def _valid_report() -> dict[str, object]:
    return deepcopy(json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _errors_for(report: dict[str, object]) -> list[str]:
    path = REPORT_ROOT / "unit-test-metadata-probe-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        return collect_metadata_probe_report_errors(path)
    finally:
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    unittest.main()
