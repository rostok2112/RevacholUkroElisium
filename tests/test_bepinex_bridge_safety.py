from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

from scripts.check_bepinex_bridge_safety import (
    ALLOWED_URLS,
    BUILD_HELPER,
    CHECK_ALL,
    CURRENT_LINE_CAPTURE_ADR,
    DEFAULT_URL,
    FIXTURE_PATH,
    FORBIDDEN_EXTERNAL_MARKERS,
    FORBIDDEN_GAME_CONTENT_MARKERS,
    FORBIDDEN_HOOK_OR_EXTRACTION_MARKERS,
    FORBIDDEN_DOWNLOAD_OR_INSTALL_MARKERS,
    GITIGNORE,
    LOG_CONTRACT_DOC,
    LOG_CONTRACT_PATH,
    METADATA_PROBE_CHECKER,
    METADATA_PROBE_FIXTURE_PATH,
    METADATA_PROBE_GATE_DOC,
    METADATA_PROBE_REPORT_ROOT,
    RUNTIME_REPORT_CHECKER,
    RUNTIME_REPORT_DOC,
    RUNTIME_REPORT_FIXTURE_PATH,
    RUNTIME_REPORT_REVIEWER,
    RUNTIME_REPORT_ROOT,
    RUNTIME_REPORT_WRITER,
    RUNTIME_SMOKE_DOC,
    PACKAGE_DIR,
    PROJECT_FILE,
    RAW_PAYLOAD_LOG_PATTERNS,
    SECRET_VALUE_PATTERN,
    SOURCE_DIR,
    SYNTHETIC_EVENT_ID,
    SYNTHETIC_LINE_ID,
    collect_bepinex_bridge_safety_errors,
)
from scripts.schema_validator import collect_errors, load_json


ROOT = Path(__file__).resolve().parents[1]
FAKE_EVENT_SCHEMA = ROOT / "specs/fake-game-event.schema.json"


class BepInExBridgeSafetyTests(unittest.TestCase):
    def test_safety_checker_passes_current_bridge(self) -> None:
        self.assertEqual([], collect_bepinex_bridge_safety_errors())

    def test_provider_annotate_fixture_shape_is_wrapped_fake_event(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("fake_event", fixture["input_type"])
        self.assertIn("event", fixture)
        self.assertEqual(SYNTHETIC_EVENT_ID, fixture["event"]["event_id"])
        self.assertEqual(SYNTHETIC_LINE_ID, fixture["event"]["synthetic_line_id"])
        self.assertIn("synthetic", json.dumps(fixture, ensure_ascii=False).lower())

    def test_synthetic_bridge_event_validates_fake_event_schema(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        errors = collect_errors(fixture["event"], load_json(FAKE_EVENT_SCHEMA))

        self.assertEqual([], errors)

    def test_log_contract_fixture_shape_and_expected_snippets(self) -> None:
        contract = load_json(LOG_CONTRACT_PATH)
        source = "\n".join(_read(path) for path in SOURCE_DIR.glob("*.cs"))

        self.assertEqual("bepinex-bridge-log-contract.v1", contract["schema_version"])
        self.assertTrue(contract["synthetic_only"])
        self.assertIsInstance(contract["expected_safe_log_snippets"], list)
        self.assertIsInstance(contract["forbidden_log_content"], list)
        self.assertFalse(contract["runtime_report_policy"]["commit_runtime_logs"])
        self.assertFalse(contract["runtime_report_policy"]["commit_bepinex_logs"])
        self.assertFalse(contract["runtime_report_policy"]["commit_game_logs"])
        self.assertFalse(contract["runtime_report_policy"]["commit_smoke_reports"])
        for snippet in contract["expected_safe_log_snippets"]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, source)

    def test_manual_smoke_docs_point_to_log_contract(self) -> None:
        fixture_ref = "tests/fixtures/bepinex_bridge.log_contract.synthetic.json"

        self.assertIn(fixture_ref, _read(RUNTIME_SMOKE_DOC))
        self.assertIn(fixture_ref, _read(LOG_CONTRACT_DOC))

    def test_runtime_report_contract_is_registered_without_requiring_real_report(self) -> None:
        fixture_ref = "tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json"
        checker_ref = "scripts/check_bepinex_runtime_smoke_report.py"
        reviewer_ref = "scripts/review_bepinex_runtime_smoke_report.py"

        self.assertTrue(RUNTIME_REPORT_FIXTURE_PATH.exists())
        self.assertTrue(RUNTIME_REPORT_DOC.exists())
        self.assertTrue(RUNTIME_REPORT_CHECKER.exists())
        self.assertTrue(RUNTIME_REPORT_WRITER.exists())
        self.assertTrue(RUNTIME_REPORT_REVIEWER.exists())
        self.assertIn(fixture_ref, _read(RUNTIME_SMOKE_DOC))
        self.assertIn(fixture_ref, _read(RUNTIME_REPORT_DOC))
        self.assertIn(checker_ref, _read(RUNTIME_SMOKE_DOC))
        self.assertIn(checker_ref, _read(RUNTIME_REPORT_DOC))
        self.assertIn(reviewer_ref, _read(RUNTIME_SMOKE_DOC))
        self.assertIn(reviewer_ref, _read(RUNTIME_REPORT_DOC))
        self.assertNotIn(checker_ref, _read(CHECK_ALL))
        self.assertNotIn(reviewer_ref, _read(CHECK_ALL))
        self.assertTrue(str(RUNTIME_REPORT_ROOT.relative_to(ROOT)).startswith("workspace"))

    def test_metadata_probe_gate_is_registered_without_requiring_real_report(self) -> None:
        fixture_ref = "tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json"
        checker_ref = "scripts/check_bepinex_metadata_probe_report.py"
        gate_ref = "docs/bepinex-metadata-probe-gate.md"

        self.assertTrue(METADATA_PROBE_GATE_DOC.exists())
        self.assertTrue(METADATA_PROBE_FIXTURE_PATH.exists())
        self.assertTrue(METADATA_PROBE_CHECKER.exists())
        self.assertIn(fixture_ref, _read(METADATA_PROBE_GATE_DOC))
        self.assertIn(checker_ref, _read(METADATA_PROBE_GATE_DOC))
        report_root = str(METADATA_PROBE_REPORT_ROOT.relative_to(ROOT)).replace("\\", "/")
        self.assertIn(report_root, _read(METADATA_PROBE_GATE_DOC))
        self.assertIn(gate_ref, _read(ROOT / "docs/bepinex-bridge.md"))
        self.assertNotIn(checker_ref, _read(CHECK_ALL))
        self.assertTrue(str(METADATA_PROBE_REPORT_ROOT.relative_to(ROOT)).startswith("workspace"))

    def test_current_line_capture_research_adr_is_registered(self) -> None:
        self.assertTrue(CURRENT_LINE_CAPTURE_ADR.exists())
        text = _read(CURRENT_LINE_CAPTURE_ADR)

        self.assertIn("Manual or synthetic event trigger only", text)
        self.assertIn("Current-line capture remains unimplemented", text)
        self.assertIn("Milestone 4F", text)

    def test_config_defaults_are_safe_and_manual_first(self) -> None:
        plugin_source = _read(SOURCE_DIR / "RevacholCompanionBridgePlugin.cs")

        self.assertIn(f'DefaultCompanionServerUrl = "{DEFAULT_URL}"', plugin_source)
        self.assertIn("DefaultRequestTimeoutMs = 3000", plugin_source)
        self.assertIn("DefaultEnabled = true", plugin_source)
        self.assertIn("DefaultSendSyntheticEventOnStart = false", plugin_source)
        self.assertIn("SendSyntheticEventOnStart", plugin_source)

    def test_companion_client_has_localhost_guard(self) -> None:
        client_source = _read(SOURCE_DIR / "CompanionHttpClient.cs")

        self.assertIn("IsLocalhost", client_source)
        self.assertIn("IsLoopbackHost", client_source)
        self.assertIn("127.0.0.1", client_source)
        self.assertIn("localhost", client_source)

    def test_bridge_sources_contain_no_external_urls_or_secret_values(self) -> None:
        for path in _scanned_bridge_files():
            text = _read(path)
            with self.subTest(path=path.relative_to(ROOT)):
                for url in re.findall(r"https?://[^\s\"'<>)]+", text, flags=re.IGNORECASE):
                    self.assertIn(url.rstrip(".,)"), ALLOWED_URLS)
                self.assertIsNone(SECRET_VALUE_PATTERN.search(text))
                if path == RUNTIME_REPORT_CHECKER:
                    continue
                lowered = text.lower()
                for marker in FORBIDDEN_EXTERNAL_MARKERS:
                    self.assertNotIn(marker.lower(), lowered, marker)

    def test_bridge_sources_contain_no_real_game_content_markers(self) -> None:
        for path in _scanned_bridge_files():
            if path == RUNTIME_REPORT_CHECKER:
                continue
            text = _read(path).lower()
            with self.subTest(path=path.relative_to(ROOT)):
                for marker in FORBIDDEN_GAME_CONTENT_MARKERS:
                    self.assertNotIn(marker.lower(), text, marker)

    def test_csharp_sources_contain_no_hook_extraction_or_ui_side_effect_markers(self) -> None:
        for path in SOURCE_DIR.glob("*.cs"):
            text = _read(path)
            with self.subTest(path=path.name):
                for marker in FORBIDDEN_HOOK_OR_EXTRACTION_MARKERS:
                    self.assertNotIn(marker, text, marker)

    def test_csharp_sources_do_not_log_raw_payloads(self) -> None:
        source = "\n".join(_read(path) for path in SOURCE_DIR.glob("*.cs"))

        for pattern in RAW_PAYLOAD_LOG_PATTERNS:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, source))
        self.assertNotIn("RawEnglishText +", source)
        self.assertNotIn("ReadAsStringAsync", source)
        self.assertNotIn("response.Content", source)

    def test_unavailable_companion_path_is_non_fatal_and_has_no_stack_trace_logging(self) -> None:
        plugin_source = _read(SOURCE_DIR / "RevacholCompanionBridgePlugin.cs")

        self.assertIn("Companion unavailable during bridge startup", plugin_source)
        self.assertIn("Game continues without companion data", plugin_source)
        self.assertIn("exc.GetType().Name", plugin_source)
        self.assertIn("exc.Message", plugin_source)
        self.assertNotIn("exc.ToString()", plugin_source)
        self.assertNotIn("StackTrace", plugin_source)

    def test_project_file_is_manual_and_has_no_package_restore_dependency(self) -> None:
        project = _read(PROJECT_FILE)

        self.assertIn("BepInExCoreDll", project)
        self.assertIn("BepInExIL2CPPDll", project)
        self.assertNotIn("<PackageReference", project)

    def test_check_all_includes_bridge_safety_smoke(self) -> None:
        self.assertIn("scripts/check_bepinex_bridge_safety.py", _read(CHECK_ALL))

    def test_check_all_does_not_require_optional_dotnet_build(self) -> None:
        self.assertNotIn("scripts/build_bepinex_bridge.py", _read(CHECK_ALL))

    def test_local_build_outputs_and_toolchains_are_ignored(self) -> None:
        gitignore = _read(GITIGNORE)

        for marker in ("bin/", "obj/", "workspace/"):
            with self.subTest(marker=marker):
                self.assertIn(marker, gitignore)

    def test_build_helper_is_optional_and_performs_no_downloads(self) -> None:
        helper = _read(BUILD_HELPER)

        self.assertIn("build_attempted", helper)
        self.assertIn("skipped_reason", helper)
        self.assertIn("no_downloads_performed", helper)
        self.assertIn("no_game_files_required", helper)
        for marker in FORBIDDEN_DOWNLOAD_OR_INSTALL_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, helper)


def _scanned_bridge_files() -> list[Path]:
    files = [
        PACKAGE_DIR / "README.md",
        PACKAGE_DIR / "DESIGN.md",
        PROJECT_FILE,
        FIXTURE_PATH,
        LOG_CONTRACT_PATH,
        RUNTIME_REPORT_FIXTURE_PATH,
        BUILD_HELPER,
        RUNTIME_REPORT_CHECKER,
        RUNTIME_REPORT_WRITER,
        RUNTIME_REPORT_REVIEWER,
        RUNTIME_SMOKE_DOC,
        LOG_CONTRACT_DOC,
        RUNTIME_REPORT_DOC,
    ]
    files.extend(sorted(SOURCE_DIR.glob("*.cs")))
    return files


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
