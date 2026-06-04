from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m3_current_line_event_implementation import (
    BEPINEX_DOC_PATH,
    CONTRACT_DOC_PATH,
    DESIGN_PATH,
    EVENT_SOURCE_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INCOMPLETE_M3_FIELDS,
    NEXT_ACTIONS_PATH,
    PLUGIN_SOURCE_PATH,
    README_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m3_current_line_event_implementation_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M3CurrentLineEventImplementationTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m3_current_line_event_implementation_errors())

    def test_fixture_marks_only_current_line_done(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m3-current-line-event-implementation.v1", fixture["schema_version"])
        self.assertEqual("M3", fixture["roadmap_milestone"])
        self.assertEqual("implementation_guarded", fixture["scope_status"])
        self.assertNotIn("m3_commit_cap", fixture)
        self.assertIs(fixture["m3_current_line_event_done"], True)
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["required_next_step"])
        self.assertIs(fixture["default_runtime_current_line_transport_enabled"], False)
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in (*INCOMPLETE_M3_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_m3_completion_drift_and_forbidden_permissions(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in (*INCOMPLETE_M3_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated[field] = True
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_enabled_defaults_and_next_step_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutations = (
            ("default_current_line_event_enabled", True),
            ("default_emit_synthetic_current_line_event_on_start", True),
            ("default_runtime_current_line_transport_enabled", True),
            ("m3_commit_cap", 6),
            ("m3_commits_used", 6),
            ("recommended_next_step", "m3_debug_console"),
            ("required_next_step", "m3_debug_console"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated[field] = value
                self.assertNotEqual([], _errors_for(mutated))

    def test_source_contains_redacted_disabled_event_path(self) -> None:
        plugin = PLUGIN_SOURCE_PATH.read_text(encoding="utf-8")
        event_source = EVENT_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("DefaultCurrentLineEventEnabled = false", plugin)
        self.assertIn("DefaultEmitSyntheticCurrentLineEventOnStart = false", plugin)
        self.assertIn("DefaultRuntimeCurrentLineTransportEnabled = false", plugin)
        self.assertIn("EmitSyntheticCurrentLineEventNow", plugin)
        self.assertIn("SendSyntheticRuntimeCurrentLineEventNowAsync", plugin)
        self.assertIn("m3-current-line-event.v1", event_source)
        self.assertIn("runtime-current-line-event.v1", event_source)
        self.assertIn('\\"raw_text_included\\":false', event_source)
        self.assertIn('\\"provider_called\\":false', event_source)
        self.assertNotIn("raw_english_text", event_source)
        self.assertNotIn("RawEnglishText", event_source)
        self.assertNotIn("PostSyntheticProviderAnnotateAsync", event_source)
        self.assertNotIn("HarmonyPatch", event_source)
        self.assertNotIn("FindObjectOfType", event_source)

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "raw text approved",
            "ui text reading approved",
            "unity scanning approved",
            "provider execution approved",
            "companion contract change approved",
            "line id matching approved in this step",
            "private line index reads approved",
            "raw payload dump",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "C:\\Users\\local\\secret",
            "screenshot archive",
            "savegame.sav",
            "decompiled output",
        ):
            with self.subTest(marker=marker):
                mutated = copy.deepcopy(fixture)
                mutated["unsafe_note"] = marker
                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_implementation_fixture_checker_source_and_next_step(self) -> None:
        refs = (
            "tests/fixtures/m3_current_line_event_implementation.synthetic.json",
            "scripts/check_m3_current_line_event_implementation.py",
            "packages/bepinex-plugin/src/CurrentLineEventFactory.cs",
            RECOMMENDED_NEXT_STEP,
        )
        for path in (
            CONTRACT_DOC_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
            BEPINEX_DOC_PATH,
            DESIGN_PATH,
            README_PATH,
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m3_current_line_event_implementation.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m3-current-line-event-implementation.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m3_current_line_event_implementation_errors(path)


if __name__ == "__main__":
    unittest.main()
