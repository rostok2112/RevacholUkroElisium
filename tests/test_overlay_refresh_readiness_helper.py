from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.run_overlay_refresh_readiness import (
    DEFAULT_OUTPUT,
    SUMMARY_ROOT,
    OverlayRefreshReadinessError,
    build_overlay_refresh_readiness_summary,
    ensure_safe_output_path,
    load_synthetic_provider_payloads,
    write_summary,
)
from scripts.synthetic_slice import ROOT


DOC_PATHS = (
    ROOT / "docs/overlay-refresh-readiness-contract.md",
    ROOT / "docs/overlay-prototype.md",
    ROOT / "docs/bepinex-bridge.md",
)


class OverlayRefreshReadinessHelperTests(unittest.TestCase):
    def tearDown(self) -> None:
        if DEFAULT_OUTPUT.exists():
            DEFAULT_OUTPUT.unlink()

    def test_ready_synthetic_provider_state_reaches_html_review_ready(self) -> None:
        summary = build_overlay_refresh_readiness_summary(
            FakeClient(*load_synthetic_provider_payloads()),
            fixture_based=True,
        )

        self.assertEqual("overlay-refresh-readiness-summary.v1", summary["schema_version"])
        self.assertEqual("ok", summary["companion_health_status"])
        self.assertTrue(summary["latest_provider_context_exists"])
        self.assertTrue(summary["latest_provider_annotation_exists"])
        self.assertTrue(summary["overlay_state_source_ready"])
        self.assertTrue(summary["overlay_state_source_valid"])
        self.assertTrue(summary["overlay_view_model_valid"])
        self.assertTrue(summary["overlay_html_review_ready"])
        self.assertTrue(summary["accessibility_check_passed"])
        self.assertEqual("overlay_html_review_ready", summary["readiness_state"])
        self.assertTrue(summary["metadata_only"])

    def test_companion_unavailable_is_no_companion_without_crashing(self) -> None:
        summary = build_overlay_refresh_readiness_summary(UnavailableClient())

        self.assertEqual("unavailable", summary["companion_health_status"])
        self.assertEqual("no_companion", summary["readiness_state"])
        self.assertIn("companion_unavailable", summary["blockers"])
        self.assertFalse(summary["latest_provider_context_exists"])

    def test_companion_available_without_provider_state_is_no_provider_state(self) -> None:
        summary = build_overlay_refresh_readiness_summary(FakeClient(None, None))

        self.assertEqual("ok", summary["companion_health_status"])
        self.assertEqual("no_provider_state", summary["readiness_state"])
        self.assertEqual("no_provider_state", summary["overlay_state_source_status"])
        self.assertFalse(summary["overlay_view_model_valid"])

    def test_partial_provider_state_is_redacted_error(self) -> None:
        context_packet, _annotation_card = load_synthetic_provider_payloads()

        summary = build_overlay_refresh_readiness_summary(FakeClient(context_packet, None))
        rendered = json.dumps(summary, ensure_ascii=False, sort_keys=True)

        self.assertEqual("error", summary["readiness_state"])
        self.assertEqual("partial_provider_state", summary["error"])
        self.assertNotIn(context_packet["current_line"]["source_text"], rendered)

    def test_invalid_provider_state_does_not_copy_payload_text(self) -> None:
        context_packet, annotation_card = load_synthetic_provider_payloads()
        broken_context = deepcopy(context_packet)
        del broken_context["current_line"]["source_text"]

        summary = build_overlay_refresh_readiness_summary(
            FakeClient(broken_context, annotation_card)
        )
        rendered = json.dumps(summary, ensure_ascii=False, sort_keys=True)

        self.assertEqual("error", summary["readiness_state"])
        self.assertIn(
            summary["error"], {"overlay_state_source_error", "overlay_state_source_failed"}
        )
        self.assertNotIn(annotation_card["concise_meaning_uk"], rendered)
        self.assertNotIn("Disco Elysium: The Final Cut", rendered)

    def test_summary_redacts_payloads_logs_html_and_disallowed_permissions(self) -> None:
        context_packet, annotation_card = load_synthetic_provider_payloads()
        summary = build_overlay_refresh_readiness_summary(
            FakeClient(context_packet, annotation_card),
            fixture_based=True,
        )
        rendered = json.dumps(summary, ensure_ascii=False, sort_keys=True)

        self.assertFalse(summary["raw_payloads_included"])
        self.assertFalse(summary["raw_logs_included"])
        self.assertFalse(summary["raw_html_included"])
        self.assertFalse(summary["game_launched"])
        self.assertFalse(summary["provider_called"])
        self.assertFalse(summary["polling_loop_started"])
        self.assertFalse(summary["timer_started"])
        self.assertFalse(summary["background_worker_started"])
        self.assertFalse(summary["production_overlay_shell_started"])
        self.assertFalse(summary["current_line_capture_allowed"])
        self.assertFalse(summary["real_text_capture_allowed"])
        self.assertFalse(summary["ui_text_reading_allowed"])
        self.assertFalse(summary["unity_scanning_allowed"])
        self.assertFalse(summary["hooks_allowed"])
        self.assertFalse(summary["ocr_allowed"])
        self.assertFalse(summary["extraction_allowed"])
        self.assertFalse(summary["companion_contract_change_allowed"])
        self.assertNotIn(context_packet["current_line"]["source_text"], rendered)
        self.assertNotIn(annotation_card["translation_uk"], rendered)
        self.assertNotIn("<!doctype html>", rendered.lower())

    def test_report_output_path_must_stay_under_workspace_root(self) -> None:
        with self.assertRaises(OverlayRefreshReadinessError):
            ensure_safe_output_path(Path("docs/overlay-refresh.json"))
        with self.assertRaises(OverlayRefreshReadinessError):
            ensure_safe_output_path(SUMMARY_ROOT / "summary.txt")

    def test_write_report_uses_workspace_only_and_stays_redacted(self) -> None:
        output = SUMMARY_ROOT / "unit-test" / "summary.json"
        if output.exists():
            output.unlink()
        summary = build_overlay_refresh_readiness_summary(
            FakeClient(*load_synthetic_provider_payloads()),
            fixture_based=True,
        )

        try:
            written = write_summary(summary, output)
            payload = json.loads(written.read_text(encoding="utf-8"))
            rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)

            self.assertTrue(written.exists())
            self.assertEqual("overlay_html_review_ready", payload["readiness_state"])
            self.assertNotIn("The committee pinned", rendered)
            self.assertNotIn("<!doctype html>", rendered.lower())
        finally:
            if output.exists():
                output.unlink()

    def test_cli_self_test_quiet_needs_no_real_server(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_refresh_readiness.py",
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
        self.assertIn("Overlay refresh readiness: overlay_html_review_ready.", completed.stdout)
        self.assertNotIn("The committee pinned", completed.stdout)

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_refresh_readiness.py",
                "--self-test",
                "--write-report",
                "--output",
                "docs/summary.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)

    def test_docs_and_check_all_register_helper(self) -> None:
        helper_ref = "scripts/run_overlay_refresh_readiness.py"
        for path in DOC_PATHS:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn(helper_ref, text)
                self.assertIn("workspace/synthetic-slice/overlay-refresh-readiness", text)

        check_all = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        self.assertIn(helper_ref, check_all)
        self.assertIn("--self-test", check_all)


class FakeClient:
    def __init__(
        self,
        context_packet: dict[str, object] | None,
        annotation_card: dict[str, object] | None,
    ) -> None:
        self.context_packet = context_packet
        self.annotation_card = annotation_card

    def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def latest_provider_context(self) -> dict[str, object] | None:
        return self.context_packet

    def latest_provider_annotation(self) -> dict[str, object] | None:
        return self.annotation_card


class UnavailableClient:
    def health(self) -> None:
        raise OSError("unavailable")


if __name__ == "__main__":
    unittest.main()
