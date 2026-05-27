from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.check_bepinex_metadata_probe_report import REPORT_ROOT
from scripts.run_bridge_to_overlay_synthetic_smoke import (
    DEFAULT_SUMMARY_OUTPUT,
    OVERLAY_OUTPUT_ROOT,
    BridgeToOverlaySmokeError,
    SmokeOptions,
    ensure_safe_overlay_output_path,
    ensure_safe_summary_output_path,
    run_bridge_to_overlay_smoke,
)
from scripts.schema_validator import load_json
from scripts.synthetic_slice import ROOT


PROVIDER_SUCCESS_FIXTURE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"


class BridgeToOverlaySyntheticSmokeTests(unittest.TestCase):
    def tearDown(self) -> None:
        for path in (
            DEFAULT_SUMMARY_OUTPUT,
            REPORT_ROOT / "report.json",
            OVERLAY_OUTPUT_ROOT / "overlay.html",
        ):
            if path.exists():
                path.unlink()

    def test_prepare_enables_probe_and_synthetic_send_with_fake_game(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            summary, exit_code = run_bridge_to_overlay_smoke(
                "prepare",
                SmokeOptions(game_dir=str(game), skip_build=True, skip_install=True),
                client=FakeCompanionClient(*_provider_payloads()),
            )

            config = (
                game / "BepInEx" / "config" / "local.revachol.ukrainian-companion.bridge.cfg"
            ).read_text(encoding="utf-8")

            self.assertEqual(0, exit_code)
            self.assertTrue(summary["ok"])
            self.assertTrue(summary["companion_health_available"])
            self.assertTrue(summary["prepare"]["metadata_probe_enabled"])
            self.assertTrue(summary["prepare"]["metadata_probe_log_on_start"])
            self.assertTrue(summary["prepare"]["send_synthetic_event_on_start"])
            self.assertIn("MetadataProbeEnabled = true", config)
            self.assertIn("MetadataProbeLogOnStart = true", config)
            self.assertIn("SendSyntheticEventOnStart = true", config)
            self.assertFalse(summary["no_game_launch_performed"] is False)

    def test_prepare_does_not_change_config_when_health_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            summary, exit_code = run_bridge_to_overlay_smoke(
                "prepare",
                SmokeOptions(game_dir=str(game), skip_build=True, skip_install=True),
                client=UnavailableCompanionClient(),
            )

            config = game / "BepInEx" / "config" / "local.revachol.ukrainian-companion.bridge.cfg"

            self.assertEqual(1, exit_code)
            self.assertFalse(summary["ok"])
            self.assertIn("companion_health_unavailable", summary["blockers"])
            self.assertFalse(config.exists())

    def test_post_builds_overlay_summary_without_raw_payload_or_log_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp), log_text=_safe_companion_connected_log_text())
            context_packet, annotation_card = _provider_payloads()
            summary, exit_code = run_bridge_to_overlay_smoke(
                "post",
                SmokeOptions(game_dir=str(game), write_report=True),
                client=FakeCompanionClient(context_packet, annotation_card),
            )
            rendered = json.dumps(summary, ensure_ascii=False, sort_keys=True)

            self.assertEqual(0, exit_code, summary.get("blockers"))
            self.assertTrue(summary["ok"])
            self.assertTrue(summary["bridge_to_overlay_ready"])
            self.assertTrue(summary["bridge_log"]["plugin_loaded_observed"])
            self.assertTrue(summary["bridge_log"]["synthetic_send_observed"])
            self.assertTrue(
                summary["companion_provider_state"]["latest_provider_context_available"]
            )
            self.assertTrue(
                summary["companion_provider_state"]["latest_provider_annotation_available"]
            )
            self.assertEqual("ready", summary["overlay"]["state_source_status"])
            self.assertTrue(summary["overlay"]["state_source_valid"])
            self.assertTrue(summary["overlay"]["view_model_valid"])
            self.assertTrue(summary["overlay"]["html_rendered"])
            self.assertTrue(summary["overlay"]["html_accessibility_valid"])
            self.assertTrue(DEFAULT_SUMMARY_OUTPUT.exists())
            self.assertNotIn("UniqueBridgeRawLine", rendered)
            self.assertNotIn("Metadata probe snapshot:", rendered)
            self.assertNotIn("raw_english_text", rendered)
            self.assertNotIn(context_packet["current_line"]["source_text"], rendered)
            self.assertNotIn(annotation_card["concise_meaning_uk"], rendered)

    def test_post_can_write_overlay_html_only_under_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp), log_text=_safe_companion_connected_log_text())
            summary, exit_code = run_bridge_to_overlay_smoke(
                "post",
                SmokeOptions(
                    game_dir=str(game),
                    write_overlay_html=True,
                    overlay_output=OVERLAY_OUTPUT_ROOT / "overlay.html",
                ),
                client=FakeCompanionClient(*_provider_payloads()),
            )

            self.assertEqual(0, exit_code, summary.get("blockers"))
            self.assertTrue((OVERLAY_OUTPUT_ROOT / "overlay.html").exists())
            self.assertTrue(summary["overlay"]["html_written"])

    def test_post_missing_provider_state_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp), log_text=_safe_companion_connected_log_text())
            summary, exit_code = run_bridge_to_overlay_smoke(
                "post",
                SmokeOptions(game_dir=str(game)),
                client=FakeCompanionClient(None, None),
            )

            self.assertEqual(1, exit_code)
            self.assertFalse(summary["bridge_to_overlay_ready"])
            self.assertIn("latest_provider_state_missing", summary["blockers"])
            self.assertIn("overlay_state_source_no_provider_state", summary["blockers"])

    def test_post_invalid_overlay_state_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp), log_text=_safe_companion_connected_log_text())
            context_packet, annotation_card = _provider_payloads()
            broken_context = deepcopy(context_packet)
            del broken_context["current_line"]["source_text"]

            summary, exit_code = run_bridge_to_overlay_smoke(
                "post",
                SmokeOptions(game_dir=str(game)),
                client=FakeCompanionClient(broken_context, annotation_card),
            )

            self.assertEqual(1, exit_code)
            self.assertFalse(summary["bridge_to_overlay_ready"])
            self.assertIn("overlay_state_source_error", summary["blockers"])

    def test_post_forbidden_log_marker_blocks_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(
                Path(temp), log_text=_safe_companion_connected_log_text() + "\nstack trace\n"
            )
            summary, exit_code = run_bridge_to_overlay_smoke(
                "post",
                SmokeOptions(game_dir=str(game), write_report=True),
                client=FakeCompanionClient(*_provider_payloads()),
            )

            self.assertEqual(1, exit_code)
            self.assertFalse(summary["ok"])
            self.assertIn("forbidden_bridge_log_marker_detected", summary["blockers"])

    def test_cleanup_restores_all_local_flags_false(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            run_bridge_to_overlay_smoke(
                "prepare",
                SmokeOptions(game_dir=str(game), skip_build=True, skip_install=True),
                client=FakeCompanionClient(*_provider_payloads()),
            )

            summary, exit_code = run_bridge_to_overlay_smoke(
                "cleanup",
                SmokeOptions(game_dir=str(game)),
                client=FakeCompanionClient(*_provider_payloads()),
            )
            config = (
                game / "BepInEx" / "config" / "local.revachol.ukrainian-companion.bridge.cfg"
            ).read_text(encoding="utf-8")

            self.assertEqual(0, exit_code)
            self.assertTrue(summary["ok"])
            self.assertIn("MetadataProbeEnabled = false", config)
            self.assertIn("MetadataProbeLogOnStart = false", config)
            self.assertIn("SendSyntheticEventOnStart = false", config)

    def test_unsafe_output_paths_are_rejected(self) -> None:
        with self.assertRaises(BridgeToOverlaySmokeError):
            ensure_safe_summary_output_path(Path("docs/summary.json"))
        with self.assertRaises(BridgeToOverlaySmokeError):
            ensure_safe_overlay_output_path(Path("docs/overlay.html"))

    def test_cli_cleanup_quiet_uses_fake_game_without_real_steam_or_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_bridge_to_overlay_synthetic_smoke.py",
                    "--phase",
                    "cleanup",
                    "--game-dir",
                    str(game),
                    "--quiet",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("cleanup: ok", completed.stdout)
            self.assertNotIn(_safe_companion_connected_log_text(), completed.stdout)


class FakeCompanionClient:
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


class UnavailableCompanionClient:
    def health(self) -> None:
        raise OSError("unavailable")


def _provider_payloads() -> tuple[dict[str, object], dict[str, object]]:
    envelope = load_json(PROVIDER_SUCCESS_FIXTURE)
    return (
        deepcopy(envelope["data"]["context_packet"]),
        deepcopy(envelope["data"]["annotation_card"]),
    )


def _fake_game(root: Path, *, log_text: str | None = None) -> Path:
    game = root / "steamapps" / "common" / "Disco Elysium"
    (game / "BepInEx" / "plugins").mkdir(parents=True)
    (game / "BepInEx" / "config").mkdir(parents=True)
    (game / "BepInEx" / "LogOutput.log").write_text(
        log_text or _safe_companion_connected_log_text(), encoding="utf-8"
    )
    return game


def _safe_companion_connected_log_text() -> str:
    return (
        "Revachol Ukrainian Companion Bridge 0.4.0-synthetic loaded in synthetic/manual "
        "bridge mode.\n"
        "Companion health check passed: status=200.\n"
        "Metadata probe snapshot: synthetic_manual=true, probe_enabled=true, "
        "probe_attempted=true, probe_completed=true, plugin_loaded=true, "
        "companion_health_checked=true, companion_available=true, "
        "synthetic_event_send_configured=true, real_text_captured=false, "
        "current_line_capture_enabled=false, ui_probe_attempted=false, "
        "scene_probe_attempted=false, counters.safe_status_events=0, "
        "counters.synthetic_events=0, counters.metadata_snapshot_created_count=1, "
        "counters.health_check_observed_count=1, "
        "counters.synthetic_send_configured_count=1.\n"
        "Synthetic provider event sent: event_id=synthetic.event.bepinex.4a.001, "
        "line_id=synthetic.bepinex.4a.001, status=200.\n"
        "UniqueBridgeRawLine"
    )


if __name__ == "__main__":
    unittest.main()
