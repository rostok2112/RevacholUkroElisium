from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.build_bepinex_bridge import (
    OUTPUT_ROOT,
    BepInExBridgeBuildError,
    build_bepinex_bridge_report,
    build_dotnet_command,
    ensure_safe_output_path,
    parse_warning_counts,
    redact_command,
    safe_path_string_for_report,
)


class BepInExBridgeBuildTests(unittest.TestCase):
    def test_missing_dotnet_skips_cleanly(self) -> None:
        report = build_bepinex_bridge_report(env={}, dotnet_path="")

        self.assertFalse(report["dotnet_found"])
        self.assertFalse(report["references_supplied"])
        self.assertFalse(report["build_attempted"])
        self.assertFalse(report["build_succeeded"])
        self.assertEqual("dotnet_not_found", report["skipped_reason"])
        self.assertTrue(report["no_game_files_required"])
        self.assertTrue(report["no_downloads_performed"])
        self.assertTrue(report["no_companion_contract_change"])

    def test_missing_references_skip_without_build(self) -> None:
        report = build_bepinex_bridge_report(env={}, dotnet_path="dotnet")

        self.assertTrue(report["dotnet_found"])
        self.assertFalse(report["references_supplied"])
        self.assertFalse(report["build_attempted"])
        self.assertEqual("bepinex_references_missing", report["skipped_reason"])

    def test_safe_command_construction_uses_argument_list(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            core = root / "BepInEx.Core.dll"
            il2cpp = root / "BepInEx.Unity.IL2CPP.dll"
            core.write_text("", encoding="utf-8")
            il2cpp.write_text("", encoding="utf-8")

            command = build_dotnet_command("dotnet", core, il2cpp, "Debug")

        self.assertIsInstance(command, list)
        self.assertEqual("dotnet", command[0])
        self.assertIn("build", command)
        self.assertIn("--configuration", command)
        self.assertTrue(any(part.startswith("-p:BepInExCoreDll=") for part in command))
        self.assertTrue(any(part.startswith("-p:BepInExIL2CPPDll=") for part in command))

    def test_report_shape_and_warning_counts_from_fake_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            core = root / "BepInEx.Core.dll"
            il2cpp = root / "BepInEx.Unity.IL2CPP.dll"
            core.write_text("", encoding="utf-8")
            il2cpp.write_text("", encoding="utf-8")
            captured: dict[str, list[str]] = {}

            def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                captured["command"] = command
                output = "\n".join(
                    [
                        "Bridge.csproj : warning MSB3277: Found conflicts.",
                        "Synthetic.cs(1,1): warning CS0168: Example warning.",
                        "Build succeeded.",
                    ]
                )
                return subprocess.CompletedProcess(command, 0, stdout=output)

            report = build_bepinex_bridge_report(
                core_dll=str(core),
                il2cpp_dll=str(il2cpp),
                dotnet_path="dotnet",
                runner=runner,
            )

        self.assertTrue(report["references_supplied"])
        self.assertTrue(report["build_attempted"])
        self.assertTrue(report["build_succeeded"])
        self.assertEqual(2, report["warning_count"])
        self.assertEqual(1, report["msb3277_warning_count"])
        self.assertIn("command", captured)
        self.assertNotIn(str(root), " ".join(report["command"]))  # type: ignore[arg-type]

    def test_build_failure_is_reported_without_private_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            core = root / "BepInEx.Core.dll"
            il2cpp = root / "BepInEx.Unity.IL2CPP.dll"
            core.write_text("", encoding="utf-8")
            il2cpp.write_text("", encoding="utf-8")

            def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
                return subprocess.CompletedProcess(
                    command,
                    1,
                    stdout=f"{root / 'Private.cs'}(1,1): error CS0000: synthetic failure",
                )

            report = build_bepinex_bridge_report(
                core_dll=str(core),
                il2cpp_dll=str(il2cpp),
                dotnet_path="dotnet",
                runner=runner,
            )

        self.assertTrue(report["build_attempted"])
        self.assertFalse(report["build_succeeded"])
        self.assertEqual(1, report["dotnet_exit_code"])
        self.assertIn("synthetic failure", report["failure_summary"])
        self.assertNotIn(str(root), report["failure_summary"])  # type: ignore[arg-type]

    def test_warning_parser_counts_msb3277_separately(self) -> None:
        output = "\n".join(
            [
                "x.csproj : warning MSB3277: conflict",
                "x.cs(2,4): warning CS0219: variable assigned",
                "    2 Warning(s)",
            ]
        )

        warning_count, msb3277_count = parse_warning_counts(output)

        self.assertEqual(2, warning_count)
        self.assertEqual(1, msb3277_count)

    def test_safe_output_path_allows_workspace_report(self) -> None:
        path = ensure_safe_output_path(OUTPUT_ROOT / "build-report.json")

        self.assertEqual(OUTPUT_ROOT / "build-report.json", path)

    def test_safe_output_path_rejects_outside_workspace(self) -> None:
        with self.assertRaises(BepInExBridgeBuildError):
            ensure_safe_output_path(Path("docs/build-report.json"))

    def test_safe_output_path_requires_json_suffix(self) -> None:
        with self.assertRaises(BepInExBridgeBuildError):
            ensure_safe_output_path(OUTPUT_ROOT / "build-report.txt")

    def test_path_redaction_hides_local_absolute_path(self) -> None:
        redacted = safe_path_string_for_report(r"C:\Users\someone\BepInEx.Core.dll")

        self.assertEqual("<local:BepInEx.Core.dll>", redacted)

    def test_redacted_command_hides_reference_paths(self) -> None:
        redacted = redact_command(
            [
                "dotnet",
                "build",
                r"C:\repo\project.csproj",
                r"-p:BepInExCoreDll=C:\Users\me\BepInEx.Core.dll",
                r"-p:BepInExIL2CPPDll=C:\Users\me\BepInEx.Unity.IL2CPP.dll",
            ]
        )

        joined = " ".join(redacted)
        self.assertIn("<local:BepInEx.Core.dll>", joined)
        self.assertIn("<local:BepInEx.Unity.IL2CPP.dll>", joined)
        self.assertNotIn(r"C:\Users\me", joined)


if __name__ == "__main__":
    unittest.main()
