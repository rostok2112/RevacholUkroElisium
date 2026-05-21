from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.check_bepinex_runtime_smoke_report import (
    FIXTURE_PATH,
    REPORT_ROOT,
    BepInExRuntimeSmokeReportError,
    collect_runtime_smoke_report_errors,
    default_report_template,
    ensure_safe_report_path,
)


ROOT = Path(__file__).resolve().parents[1]


class BepInExRuntimeSmokeReportTests(unittest.TestCase):
    def test_committed_fixture_validates(self) -> None:
        self.assertEqual([], collect_runtime_smoke_report_errors(FIXTURE_PATH))

    def test_invalid_status_fails(self) -> None:
        report = _valid_report()
        report["smoke_status"] = "maybe"

        self.assertTrue(_errors_for(report))

    def test_missing_manual_flag_fails(self) -> None:
        report = _valid_report()
        report["created_by_user_manually"] = False

        errors = _errors_for(report)

        self.assertIn("created_by_user_manually=true", "\n".join(errors))

    def test_raw_log_marker_fails(self) -> None:
        report = _valid_report()
        report["evidence_summary"] = "Observed LogOutput.log content."

        self.assertIn("LogOutput.log", "\n".join(_errors_for(report)))

    def test_private_path_fails(self) -> None:
        report = _valid_report()
        report["notes_redacted"] = r"Local file was C:\Users\player\Game\BepInEx\LogOutput.log"

        errors = "\n".join(_errors_for(report))

        self.assertIn("private absolute path", errors)

    def test_stack_trace_fails(self) -> None:
        report = _valid_report()
        report["evidence_summary"] = "Stack trace: at Revachol.Plugin.Load()"

        errors = "\n".join(_errors_for(report))

        self.assertIn("stack trace", errors.lower())

    def test_payload_marker_fails(self) -> None:
        report = _valid_report()
        report["evidence_summary"] = '{"input_type":"fake_event","event":{"x":"y"}}'

        errors = "\n".join(_errors_for(report))

        self.assertIn("input_type", errors)

    def test_real_game_content_marker_fails(self) -> None:
        report = _valid_report()
        report["notes_redacted"] = "Accidentally referenced steamapps local content."

        self.assertIn("steamapps", "\n".join(_errors_for(report)))

    def test_hook_ocr_extraction_marker_fails(self) -> None:
        report = _valid_report()
        report["notes_redacted"] = "Tried HarmonyPatch and OCR during the run."

        errors = "\n".join(_errors_for(report))

        self.assertIn("HarmonyPatch", errors)
        self.assertIn("OCR", errors)

    def test_non_localhost_url_fails(self) -> None:
        report = _valid_report()
        report["evidence_summary"] = "Checked https://example.invalid/status"

        self.assertIn("non-localhost URL", "\n".join(_errors_for(report)))

    def test_safe_workspace_report_path_allowed(self) -> None:
        path = ensure_safe_report_path(REPORT_ROOT / "report.json")

        self.assertEqual(REPORT_ROOT / "report.json", path)

    def test_unsafe_report_path_rejected(self) -> None:
        with self.assertRaises(BepInExRuntimeSmokeReportError):
            ensure_safe_report_path(Path("docs/manual-smoke/report.json"))

    def test_cli_quiet_validates_fixture(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/check_bepinex_runtime_smoke_report.py", "--quiet"],
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
                "scripts/check_bepinex_runtime_smoke_report.py",
                "--report",
                "docs/manual-smoke/report.json",
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
        output = REPORT_ROOT / "unit-test-report.template.json"
        if output.exists():
            output.unlink()
        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/write_bepinex_runtime_smoke_report.py",
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
            self.assertEqual([], collect_runtime_smoke_report_errors(output))
        finally:
            if output.exists():
                output.unlink()

    def test_template_writer_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/write_bepinex_runtime_smoke_report.py",
                "--output",
                "docs/manual-smoke/report.template.json",
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
    return deepcopy(default_report_template())


def _errors_for(report: dict[str, object]) -> list[str]:
    path = REPORT_ROOT / "unit-test-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        return collect_runtime_smoke_report_errors(path)
    finally:
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    unittest.main()
