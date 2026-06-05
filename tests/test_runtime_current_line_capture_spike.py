from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.check_runtime_current_line_capture_spike_report import (
    FIXTURE_PATH,
    REPORT_ROOT,
    RuntimeCurrentLineCaptureSpikeReportError,
    collect_capture_spike_report_errors,
    default_report_template,
    ensure_safe_report_path,
)
from scripts.review_runtime_current_line_capture_spike import build_review
from scripts.run_bepinex_metadata_probe_local_smoke import (
    set_bridge_config_values,
)


ROOT = Path(__file__).resolve().parents[1]


class RuntimeCurrentLineCaptureSpikeTests(unittest.TestCase):
    def test_committed_fixture_validates(self) -> None:
        self.assertEqual([], collect_capture_spike_report_errors(FIXTURE_PATH))

    def test_default_runtime_startup_send_is_disabled(self) -> None:
        plugin = (ROOT / "packages/bepinex-plugin/src/RevacholCompanionBridgePlugin.cs").read_text(
            encoding="utf-8"
        )

        self.assertIn("DefaultRuntimeCurrentLineTransportEnabled = false", plugin)
        self.assertIn("DefaultSendSyntheticRuntimeCurrentLineEventOnStart = false", plugin)
        self.assertIn("SendSyntheticRuntimeCurrentLineEventOnStart", plugin)

    def test_report_rejects_forbidden_flags_true(self) -> None:
        for field in (
            "provider_called",
            "runtime_current_line_capture_enabled",
            "real_text_captured",
            "hooks_used",
            "ui_text_reading_used",
            "unity_scanning_used",
            "screenshots_included",
            "raw_payloads_included",
            "private_paths_included",
        ):
            with self.subTest(field=field):
                report = _valid_report()
                report[field] = True

                self.assertNotEqual([], _errors_for(report))

    def test_report_rejects_unsafe_markers(self) -> None:
        report = _valid_report()
        report["notes_redacted"] = "LogOutput.log screenshot OCR request payload"

        errors = "\n".join(_errors_for(report))

        self.assertIn("LogOutput.log", errors)
        self.assertIn("screenshot", errors)
        self.assertIn("OCR", errors)
        self.assertIn("request payload", errors)

    def test_report_path_bounds(self) -> None:
        self.assertEqual(
            REPORT_ROOT / "report.json", ensure_safe_report_path(REPORT_ROOT / "report.json")
        )
        with self.assertRaises(RuntimeCurrentLineCaptureSpikeReportError):
            ensure_safe_report_path(Path("docs/capture-spike.json"))

    def test_review_ready_and_blocked_states(self) -> None:
        ready = _ready_report()
        review = _review_for(ready)

        self.assertTrue(review["ready_for_capture_strategy_decision"])
        self.assertEqual(
            "runtime_current_line_capture_strategy_decision", review["recommended_next_step"]
        )
        self.assertFalse(review["provider_called"])
        self.assertFalse(review["hooks_allowed_next"])

        blocked = _ready_report()
        blocked["companion_received_runtime_event"] = False
        blocked["translation_memory_checked"] = False
        review = _review_for(blocked)
        self.assertFalse(review["ready_for_capture_strategy_decision"])
        self.assertEqual(
            "repeat_runtime_current_line_capture_spike", review["recommended_next_step"]
        )

    def test_config_helper_toggles_only_safe_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            path = set_bridge_config_values(
                config_dir,
                section="CurrentLineEvent",
                values={
                    "RuntimeCurrentLineTransportEnabled": True,
                    "SendSyntheticRuntimeCurrentLineEventOnStart": True,
                },
            )
            text = path.read_text(encoding="utf-8")

        self.assertIn("RuntimeCurrentLineTransportEnabled = true", text)
        self.assertIn("SendSyntheticRuntimeCurrentLineEventOnStart = true", text)
        self.assertNotIn("HarmonyPatch", text)
        self.assertNotIn("FindObjectOfType", text)

    def test_review_self_test_and_check_all_registration(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_runtime_current_line_capture_spike.py",
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
        self.assertIn("scripts/check_runtime_current_line_capture_spike_report.py", check_all)
        self.assertIn("scripts/review_runtime_current_line_capture_spike.py", check_all)


def _valid_report() -> dict[str, object]:
    return deepcopy(default_report_template())


def _ready_report() -> dict[str, object]:
    report = _valid_report()
    report.update(
        {
            "spike_status": "pass",
            "plugin_loaded_observed": True,
            "companion_health_checked": True,
            "companion_available": True,
            "runtime_transport_enabled": True,
            "synthetic_runtime_send_configured": True,
            "synthetic_runtime_event_sent_observed": True,
            "companion_received_runtime_event": True,
            "translation_memory_checked": True,
            "provider_call_required_observed": True,
            "recommended_next_step": "runtime_current_line_capture_strategy_decision",
        }
    )
    return report


def _errors_for(report: dict[str, object]) -> list[str]:
    path = REPORT_ROOT / "unit-test-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        return collect_capture_spike_report_errors(path)
    finally:
        path.unlink(missing_ok=True)


def _review_for(report: dict[str, object]) -> dict[str, object]:
    path = REPORT_ROOT / "unit-test-review-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        return build_review(path)
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
