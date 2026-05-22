from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.check_bepinex_metadata_probe_report import (
    REPORT_ROOT,
    collect_metadata_probe_report_errors,
)
from scripts.run_bepinex_metadata_probe_local_smoke import (
    BRIDGE_ASSEMBLY_NAME,
    LocalSmokeError,
    check_metadata_probe_log,
    discover_bepinex_paths,
    discover_game_dir,
    discover_local_smoke_paths,
    discover_reference_dlls,
    find_game_from_libraryfolders,
    install_bridge_dll,
    set_probe_config,
    write_metadata_probe_report,
)


ROOT = Path(__file__).resolve().parents[1]


class BepInExMetadataProbeLocalSmokeTests(unittest.TestCase):
    def test_autodiscovers_fake_steam_library_game_dir_from_libraryfolders(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            steam = root / "Steam"
            library = root / "SteamLibrary"
            game = _fake_game(library)
            library_file = steam / "steamapps" / "libraryfolders.vdf"
            library_file.parent.mkdir(parents=True)
            library_file.write_text(
                '"libraryfolders"\n{\n  "0"\n  {\n    "path" "'
                + str(library).replace("\\", "\\\\")
                + '"\n  }\n}\n',
                encoding="utf-8",
            )

            discovered = find_game_from_libraryfolders(steam)
            game_discovery = discover_game_dir(steam_roots=[steam], common_roots=[])

            self.assertEqual(game.resolve(), discovered.resolve())
            self.assertEqual(game.resolve(), game_discovery.game_dir)
            self.assertEqual("steam_library", game_discovery.source)

    def test_discovers_bepinex_paths_under_fake_game_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))

            paths = discover_bepinex_paths(game)

            self.assertEqual(game / "BepInEx" / "plugins", paths.plugins_dir)
            self.assertEqual(game / "BepInEx" / "config", paths.config_dir)
            self.assertEqual(game / "BepInEx" / "LogOutput.log", paths.log_file)

    def test_autodiscovers_fake_bepinex_reference_dlls_from_toolchain_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            core_dir = Path(temp) / "toolchain" / "BepInEx" / "core"
            core_dir.mkdir(parents=True)
            core = core_dir / "BepInEx.Core.dll"
            il2cpp = core_dir / "BepInEx.IL2CPP.dll"
            core.write_text("fake core", encoding="utf-8")
            il2cpp.write_text("fake il2cpp", encoding="utf-8")

            refs = discover_reference_dlls(
                explicit_core=None,
                explicit_il2cpp=None,
                env={},
                game_dir=None,
                toolchain_roots=[Path(temp) / "toolchain"],
            )

            self.assertEqual(core.resolve(), refs.core_dll)
            self.assertEqual(il2cpp.resolve(), refs.il2cpp_dll)

    def test_explicit_cli_paths_override_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = _fake_game(root)
            core = root / "BepInEx.Core.dll"
            il2cpp = root / "BepInEx.Unity.IL2CPP.dll"
            core.write_text("fake core", encoding="utf-8")
            il2cpp.write_text("fake il2cpp", encoding="utf-8")

            discovery = discover_local_smoke_paths(
                game_dir=str(game),
                core_dll=str(core),
                il2cpp_dll=str(il2cpp),
                configuration="Debug",
                env={},
                steam_roots=[],
                common_roots=[],
                toolchain_roots=[],
            )

            self.assertEqual("cli", discovery.game.source)
            self.assertEqual(game.resolve(), discovery.game.game_dir)
            self.assertEqual(core.resolve(), discovery.refs.core_dll)
            self.assertEqual(il2cpp.resolve(), discovery.refs.il2cpp_dll)

    def test_install_writes_only_under_bepinex_plugins(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            bridge = _fake_bridge_dll()
            try:
                result = install_bridge_dll(game, bridge, game / "BepInEx" / "plugins")

                self.assertTrue(result["installed"])
                self.assertTrue((game / "BepInEx" / "plugins" / bridge.name).exists())
            finally:
                _delete(bridge)

    def test_install_rejects_non_plugins_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            outside = game / "BepInEx" / "config"
            bridge = _fake_bridge_dll()
            try:
                with self.assertRaises(LocalSmokeError):
                    install_bridge_dll(game, bridge, outside)
            finally:
                _delete(bridge)

    def test_config_enable_disable_preserves_unrelated_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config_dir = Path(temp) / "BepInEx" / "config"
            config_dir.mkdir(parents=True)
            config = config_dir / "local.revachol.ukrainian-companion.bridge.cfg"
            config.write_text(
                "[Bridge]\nEnabled = true\n\n[MetadataProbe]\n"
                "MetadataProbeEnabled = false\nOtherSetting = keep\n"
                "MetadataProbeLogOnStart = false\n",
                encoding="utf-8",
            )

            set_probe_config(config_dir, enabled=True)
            enabled = config.read_text(encoding="utf-8")
            set_probe_config(config_dir, enabled=False)
            disabled = config.read_text(encoding="utf-8")

            self.assertIn("Enabled = true", enabled)
            self.assertIn("OtherSetting = keep", enabled)
            self.assertIn("MetadataProbeEnabled = true", enabled)
            self.assertIn("MetadataProbeLogOnStart = true", enabled)
            self.assertIn("MetadataProbeEnabled = false", disabled)
            self.assertIn("MetadataProbeLogOnStart = false", disabled)

    def test_missing_config_creates_safe_minimal_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config_dir = Path(temp) / "BepInEx" / "config"

            config = set_probe_config(config_dir, enabled=True)

            text = config.read_text(encoding="utf-8")
            self.assertIn("[MetadataProbe]", text)
            self.assertIn("MetadataProbeEnabled = true", text)
            self.assertIn("MetadataProbeLogOnStart = true", text)

    def test_safe_log_markers_are_detected_and_generated_report_validates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_file = Path(temp) / "LogOutput.log"
            log_file.write_text(_safe_log_text() + "\nUniqueBridgeRawLine\n", encoding="utf-8")
            report_path = REPORT_ROOT / "unit-local-smoke-report.json"
            _delete(report_path)
            try:
                check = check_metadata_probe_log(log_file)
                result = write_metadata_probe_report(check, output_path=report_path)

                report_text = report_path.read_text(encoding="utf-8")
                report = json.loads(report_text)
                self.assertTrue(check.plugin_loaded_observed)
                self.assertTrue(check.metadata_snapshot_observed)
                self.assertFalse(check.forbidden_marker_detected)
                self.assertTrue(result["written"])
                self.assertEqual([], collect_metadata_probe_report_errors(report_path))
                self.assertEqual("pass", report["probe_status"])
                self.assertEqual(1, report["counters"]["metadata_snapshot_created_count"])
                self.assertNotIn("UniqueBridgeRawLine", report_text)
                self.assertNotIn("Metadata probe snapshot:", report_text)
            finally:
                _delete(report_path)

    def test_unsafe_log_markers_block_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            log_file = Path(temp) / "LogOutput.log"
            log_file.write_text(_safe_log_text() + "\nreal_text_captured=true\n", encoding="utf-8")
            check = check_metadata_probe_log(log_file)

            self.assertTrue(check.forbidden_marker_detected)
            with self.assertRaises(LocalSmokeError):
                write_metadata_probe_report(check, output_path=REPORT_ROOT / "unit-blocked.json")

    def test_cli_quiet_mode_uses_fake_game_and_does_not_need_real_steam(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_bepinex_metadata_probe_local_smoke.py",
                    "--game-dir",
                    str(game),
                    "--skip-build",
                    "--skip-install",
                    "--check-log",
                    "--quiet",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("ok", completed.stdout)
            self.assertIn("game_dir_found=true", completed.stdout)
            self.assertNotIn(_safe_log_text(), completed.stdout)

    def test_cli_verbose_discovery_may_show_paths_but_never_raw_log_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            game = _fake_game(Path(temp))
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_bepinex_metadata_probe_local_smoke.py",
                    "--game-dir",
                    str(game),
                    "--print-discovery",
                    "--verbose",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("Disco Elysium", completed.stdout)
            self.assertNotIn("UniqueBridgeRawLine", completed.stdout)
            self.assertNotIn("Metadata probe snapshot:", completed.stdout)


def _fake_game(root: Path) -> Path:
    game = root / "steamapps" / "common" / "Disco Elysium"
    (game / "BepInEx" / "plugins").mkdir(parents=True)
    (game / "BepInEx" / "config").mkdir(parents=True)
    (game / "BepInEx" / "LogOutput.log").write_text(_safe_log_text(), encoding="utf-8")
    return game


def _safe_log_text() -> str:
    return (
        "Revachol Ukrainian Companion Bridge 0.4.0-synthetic loaded in synthetic/manual "
        "bridge mode.\n"
        "Companion health check passed: status=200.\n"
        "Metadata probe snapshot: synthetic_manual=true, probe_enabled=true, "
        "probe_attempted=true, probe_completed=true, plugin_loaded=true, "
        "companion_health_checked=true, companion_available=true, "
        "synthetic_event_send_configured=false, real_text_captured=false, "
        "current_line_capture_enabled=false, ui_probe_attempted=false, "
        "scene_probe_attempted=false, counters.safe_status_events=0, "
        "counters.synthetic_events=0, counters.metadata_snapshot_created_count=1, "
        "counters.health_check_observed_count=1, "
        "counters.synthetic_send_configured_count=0."
    )


def _fake_bridge_dll() -> Path:
    path = (
        ROOT
        / "packages"
        / "bepinex-plugin"
        / "bin"
        / "Debug"
        / "unit-local-smoke"
        / f"{BRIDGE_ASSEMBLY_NAME}.dll"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("fake bridge dll", encoding="utf-8")
    return path


def _delete(path: Path) -> None:
    if path.exists():
        path.unlink()


if __name__ == "__main__":
    unittest.main()
