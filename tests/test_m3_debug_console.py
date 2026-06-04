from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m3_debug_console import (
    ALLOWED_COMMANDS,
    BEPINEX_DOC_PATH,
    DESIGN_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    NEXT_ACTIONS_PATH,
    PLUGIN_SOURCE_PATH,
    README_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    SOURCE_PATH,
    collect_m3_debug_console_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M3DebugConsoleTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m3_debug_console_errors())

    def test_fixture_marks_all_m3_criteria_done(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m3-debug-console.v1", fixture["schema_version"])
        self.assertEqual("M3", fixture["roadmap_milestone"])
        self.assertEqual(6, fixture["m3_commit_cap"])
        self.assertIs(fixture["m3_current_line_event_done"], True)
        self.assertIs(fixture["m3_line_id_matching_done"], True)
        self.assertIs(fixture["m3_debug_console_done"], True)
        self.assertEqual(list(ALLOWED_COMMANDS), fixture["allowed_commands"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_dangerous_permissions_and_command_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutations = [
            ("allowed_commands", [*fixture["allowed_commands"], "dump_payload"]),
            ("recommended_next_step", "m4_overlay"),
            ("required_next_step", "m4_overlay"),
            ("m3_commit_cap", 7),
        ]
        for field in FORBIDDEN_PERMISSION_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = True
            self.assertNotEqual([], _errors_for(mutated))
        for field, value in mutations:
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated[field] = value
                self.assertNotEqual([], _errors_for(mutated))

    def test_source_defines_disabled_redacted_command_surface(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        plugin = PLUGIN_SOURCE_PATH.read_text(encoding="utf-8")

        self.assertIn("DefaultDebugConsoleEnabled = false", plugin)
        self.assertIn("RunDebugCommand", plugin)
        for command in ALLOWED_COMMANDS:
            self.assertIn(command, source)
        self.assertIn('"raw_text_included"', source)
        self.assertIn('"payload_dump_included"', source)
        self.assertIn('"provider_called"', source)
        self.assertNotIn("ReadAllText", source)
        self.assertNotIn("PostSyntheticProviderAnnotateAsync(", source)
        self.assertNotIn("RawEnglishText", source)

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "raw text dump approved",
            "payload dump approved",
            "private path dump approved",
            "provider execution approved",
            "companion contract change approved",
            "raw payload dump",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "screenshot archive",
            "decompiled output",
        ):
            with self.subTest(marker=marker):
                mutated = copy.deepcopy(fixture)
                mutated["unsafe_note"] = marker
                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_debug_console_guardrail(self) -> None:
        refs = (
            "packages/bepinex-plugin/src/DebugCommandHandler.cs",
            "tests/fixtures/m3_debug_console.synthetic.json",
            "scripts/check_m3_debug_console.py",
            RECOMMENDED_NEXT_STEP,
        )
        for path in (
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

        self.assertIn("scripts/check_m3_debug_console.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m3-debug-console.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m3_debug_console_errors(path)


if __name__ == "__main__":
    unittest.main()
