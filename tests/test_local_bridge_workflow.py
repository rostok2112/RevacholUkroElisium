from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.check_bepinex_metadata_probe_report import REPORT_ROOT
from scripts.run_bridge_to_overlay_synthetic_smoke import DEFAULT_SUMMARY_OUTPUT
from scripts.run_bepinex_metadata_probe_local_smoke import BRIDGE_ASSEMBLY_NAME
from scripts.run_local_bridge_workflow import (
    GitCommandResult,
    WorkflowOptions,
    collect_git_summary,
    is_runtime_artifact_path,
    run_local_bridge_workflow,
)
from scripts.schema_validator import load_json
from scripts.synthetic_slice import ROOT


PROVIDER_SUCCESS_FIXTURE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"


class LocalBridgeWorkflowTests(unittest.TestCase):
    def tearDown(self) -> None:
        for path in (
            DEFAULT_SUMMARY_OUTPUT,
            REPORT_ROOT / "report.json",
            ROOT
            / "packages"
            / "bepinex-plugin"
            / "bin"
            / "Debug"
            / "unit-local-workflow"
            / f"{BRIDGE_ASSEMBLY_NAME}.dll",
        ):
            if path.exists():
                path.unlink()

    def test_doctor_reports_ready_with_fake_paths_and_clean_git(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = _fake_game(root)
            core, il2cpp = _fake_refs(root)
            _fake_bridge_dll()

            summary, exit_code = run_local_bridge_workflow(
                "doctor",
                WorkflowOptions(
                    game_dir=str(game),
                    core_dll=str(core),
                    il2cpp_dll=str(il2cpp),
                ),
                client=FakeCompanionClient(*_provider_payloads()),
                git_runner=_fake_git_runner(status="", staged=""),
            )
            rendered = json.dumps(summary, ensure_ascii=False)

            self.assertEqual(0, exit_code, summary.get("blockers"))
            self.assertTrue(summary["ok"])
            self.assertTrue(summary["doctor"]["git_clean"])
            self.assertTrue(summary["doctor"]["bepinex_refs_found"])
            self.assertTrue(summary["doctor"]["steam_game_autodiscovery"])
            self.assertTrue(summary["doctor"]["bepinex_plugins_exists"])
            self.assertTrue(summary["doctor"]["companion_health_available"])
            self.assertTrue(summary["doctor"]["bridge_dll_built_or_found"])
            self.assertTrue(summary["doctor"]["no_raw_logs_reports_staged"])
            self.assertNotIn(str(game), rendered)
            self.assertNotIn("UniqueBridgeRawLine", rendered)

    def test_doctor_reports_not_ready_for_staged_runtime_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))

            summary, exit_code = run_local_bridge_workflow(
                "doctor",
                WorkflowOptions(game_dir=str(game)),
                client=FakeCompanionClient(*_provider_payloads()),
                git_runner=_fake_git_runner(
                    status="A  workspace/synthetic-slice/bepinex-bridge/report.json\n",
                    staged="workspace/synthetic-slice/bepinex-bridge/report.json\n",
                ),
            )

            self.assertEqual(1, exit_code)
            self.assertFalse(summary["doctor"]["no_raw_logs_reports_staged"])
            self.assertIn("raw_logs_reports_staged", summary["blockers"])
            self.assertTrue(is_runtime_artifact_path("workspace/synthetic-slice/x/report.json"))
            self.assertFalse(is_runtime_artifact_path("docs/manual-smoke/note.md"))

    def test_collect_git_summary_uses_redacted_counts_only(self) -> None:
        summary = collect_git_summary(
            git_runner=_fake_git_runner(
                status=" M docs/local-workflow.md\n",
                staged="docs/local-workflow.md\nBepInEx/LogOutput.log\n",
            )
        )

        rendered = json.dumps(summary, ensure_ascii=False)
        self.assertFalse(summary["git_clean"])
        self.assertFalse(summary["no_raw_logs_reports_staged"])
        self.assertEqual(2, summary["staged_entry_count"])
        self.assertEqual(1, summary["staged_artifact_candidate_count"])
        self.assertNotIn("LogOutput.log", rendered)

    def test_prepare_metadata_smoke_enables_probe_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))

            summary, exit_code = run_local_bridge_workflow(
                "prepare-metadata-smoke",
                WorkflowOptions(game_dir=str(game), skip_build=True, skip_install=True),
                client=FakeCompanionClient(*_provider_payloads()),
            )
            config = _config_text(game)

            self.assertEqual(0, exit_code)
            self.assertTrue(summary["ok"])
            self.assertTrue(summary["prepare_metadata_smoke"]["metadata_probe_enabled"])
            self.assertTrue(summary["prepare_metadata_smoke"]["metadata_probe_log_on_start"])
            self.assertFalse(summary["prepare_metadata_smoke"]["send_synthetic_event_on_start"])
            self.assertIn("MetadataProbeEnabled = true", config)
            self.assertIn("MetadataProbeLogOnStart = true", config)
            self.assertNotIn("SendSyntheticEventOnStart = true", config)

    def test_prepare_companion_smoke_requires_health_before_config_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))

            summary, exit_code = run_local_bridge_workflow(
                "prepare-companion-smoke",
                WorkflowOptions(game_dir=str(game), skip_build=True, skip_install=True),
                client=UnavailableCompanionClient(),
            )

            self.assertEqual(1, exit_code)
            self.assertFalse(summary["ok"])
            self.assertIn("companion_health_unavailable", summary["blockers"])
            self.assertFalse(_config_path(game).exists())

    def test_prepare_companion_smoke_enables_probe_and_synthetic_send(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))

            summary, exit_code = run_local_bridge_workflow(
                "prepare-companion-smoke",
                WorkflowOptions(game_dir=str(game), skip_build=True, skip_install=True),
                client=FakeCompanionClient(*_provider_payloads()),
            )
            config = _config_text(game)

            self.assertEqual(0, exit_code)
            self.assertTrue(summary["ok"])
            self.assertTrue(summary["prepare_companion_smoke"]["metadata_probe_enabled"])
            self.assertTrue(summary["prepare_companion_smoke"]["metadata_probe_log_on_start"])
            self.assertTrue(summary["prepare_companion_smoke"]["send_synthetic_event_on_start"])
            self.assertIn("SendSyntheticEventOnStart = true", config)

    def test_bridge_to_overlay_prepare_and_cleanup_delegate_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp), log_text=_safe_companion_connected_log_text())
            client = FakeCompanionClient(*_provider_payloads())

            prepare, prepare_exit = run_local_bridge_workflow(
                "prepare-bridge-to-overlay-smoke",
                WorkflowOptions(game_dir=str(game), skip_build=True, skip_install=True),
                client=client,
            )
            cleanup, cleanup_exit = run_local_bridge_workflow(
                "cleanup",
                WorkflowOptions(game_dir=str(game)),
                client=client,
            )
            config = _config_text(game)

            self.assertEqual(0, prepare_exit)
            self.assertTrue(prepare["ok"])
            self.assertEqual("prepare", prepare["delegated_phase"])
            self.assertEqual(0, cleanup_exit)
            self.assertTrue(cleanup["ok"])
            self.assertIn("MetadataProbeEnabled = false", config)
            self.assertIn("MetadataProbeLogOnStart = false", config)
            self.assertIn("SendSyntheticEventOnStart = false", config)

    def test_post_bridge_to_overlay_smoke_redacts_logs_and_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp), log_text=_safe_companion_connected_log_text())
            context_packet, annotation_card = _provider_payloads()

            summary, exit_code = run_local_bridge_workflow(
                "post-bridge-to-overlay-smoke",
                WorkflowOptions(game_dir=str(game), write_report=True),
                client=FakeCompanionClient(context_packet, annotation_card),
            )
            rendered = json.dumps(summary, ensure_ascii=False, sort_keys=True)

            self.assertEqual(0, exit_code, summary.get("blockers"))
            self.assertTrue(summary["ok"])
            self.assertTrue(summary["bridge_to_overlay"]["bridge_log"]["plugin_loaded_observed"])
            self.assertTrue(DEFAULT_SUMMARY_OUTPUT.exists())
            self.assertNotIn("UniqueBridgeRawLine", rendered)
            self.assertNotIn("Metadata probe snapshot:", rendered)
            self.assertNotIn("raw_english_text", rendered)
            self.assertNotIn(context_packet["current_line"]["source_text"], rendered)
            self.assertNotIn(annotation_card["concise_meaning_uk"], rendered)

    def test_cli_cleanup_quiet_uses_fake_game_without_real_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_local_bridge_workflow.py",
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
            self.assertNotIn("UniqueBridgeRawLine", completed.stdout)


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


def _fake_git_runner(*, status: str, staged: str):
    def run(args: object) -> GitCommandResult:
        command = tuple(args)
        if command == ("status", "--porcelain"):
            return GitCommandResult(0, status)
        if command == ("diff", "--cached", "--name-only"):
            return GitCommandResult(0, staged)
        return GitCommandResult(1, "")

    return run


def _provider_payloads() -> tuple[dict[str, object], dict[str, object]]:
    envelope = load_json(PROVIDER_SUCCESS_FIXTURE)
    return (
        deepcopy(envelope["data"]["context_packet"]),
        deepcopy(envelope["data"]["annotation_card"]),
    )


def _fake_game(root: Path, *, log_text: str | None = None) -> Path:
    game = root / "local-game"
    (game / "BepInEx" / "plugins").mkdir(parents=True)
    (game / "BepInEx" / "config").mkdir(parents=True)
    (game / "BepInEx" / "LogOutput.log").write_text(
        log_text or _safe_companion_connected_log_text(), encoding="utf-8"
    )
    return game


def _fake_refs(root: Path) -> tuple[Path, Path]:
    core = root / "BepInEx.Core.dll"
    il2cpp = root / "BepInEx.IL2CPP.dll"
    core.write_text("fake core", encoding="utf-8")
    il2cpp.write_text("fake il2cpp", encoding="utf-8")
    return core, il2cpp


def _fake_bridge_dll() -> Path:
    path = (
        ROOT
        / "packages"
        / "bepinex-plugin"
        / "bin"
        / "Debug"
        / "unit-local-workflow"
        / f"{BRIDGE_ASSEMBLY_NAME}.dll"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("fake bridge dll", encoding="utf-8")
    return path


def _config_path(game: Path) -> Path:
    return game / "BepInEx" / "config" / "local.revachol.ukrainian-companion.bridge.cfg"


def _config_text(game: Path) -> str:
    return _config_path(game).read_text(encoding="utf-8")


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
