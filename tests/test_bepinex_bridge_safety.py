from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

from scripts.check_bepinex_bridge_safety import (
    ALLOWED_URLS,
    CHECK_ALL,
    DEFAULT_URL,
    FIXTURE_PATH,
    FORBIDDEN_EXTERNAL_MARKERS,
    FORBIDDEN_GAME_CONTENT_MARKERS,
    FORBIDDEN_HOOK_OR_EXTRACTION_MARKERS,
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
                lowered = text.lower()
                for marker in FORBIDDEN_EXTERNAL_MARKERS:
                    self.assertNotIn(marker.lower(), lowered, marker)

    def test_bridge_sources_contain_no_real_game_content_markers(self) -> None:
        for path in _scanned_bridge_files():
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

    def test_project_file_is_manual_and_has_no_package_restore_dependency(self) -> None:
        project = _read(PROJECT_FILE)

        self.assertIn("BepInExCoreDll", project)
        self.assertIn("BepInExIL2CPPDll", project)
        self.assertNotIn("<PackageReference", project)

    def test_check_all_includes_bridge_safety_smoke(self) -> None:
        self.assertIn("scripts/check_bepinex_bridge_safety.py", _read(CHECK_ALL))


def _scanned_bridge_files() -> list[Path]:
    files = [
        PACKAGE_DIR / "README.md",
        PACKAGE_DIR / "DESIGN.md",
        PROJECT_FILE,
        FIXTURE_PATH,
    ]
    files.extend(sorted(SOURCE_DIR.glob("*.cs")))
    return files


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
