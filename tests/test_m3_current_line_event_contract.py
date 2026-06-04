from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m3_current_line_event_contract import (
    ALLOWED_EVENT_FIELDS,
    ALLOWED_EVENT_SOURCES,
    BEPINEX_DOC_PATH,
    DESIGN_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INCOMPLETE_M3_FIELDS,
    NEXT_ACTIONS_PATH,
    README_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SCOPE_DOC_PATH,
    SESSION_SUMMARY_PATH,
    collect_m3_current_line_event_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M3CurrentLineEventContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m3_current_line_event_contract_errors())

    def test_fixture_keeps_m3_contract_only_and_incomplete(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m3-current-line-event-contract.v1", fixture["schema_version"])
        self.assertEqual("M3", fixture["roadmap_milestone"])
        self.assertEqual("contract_only", fixture["scope_status"])
        self.assertEqual(6, fixture["m3_commit_cap"])
        self.assertEqual("m3-current-line-event.v1", fixture["event_schema_version"])
        self.assertEqual("current_line", fixture["event_kind"])
        self.assertEqual(list(ALLOWED_EVENT_FIELDS), fixture["allowed_event_fields"])
        self.assertEqual(list(ALLOWED_EVENT_SOURCES), fixture["allowed_event_sources"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["required_next_step"])
        self.assertEqual(
            "contract_defined_only",
            fixture["current_line_event_implementation_allowed_next"],
        )
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in (*INCOMPLETE_M3_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_completed_m3_criteria_and_forbidden_permissions(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in (*INCOMPLETE_M3_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated[field] = True
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_changed_next_step_commit_cap_event_fields_and_sources(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutations = (
            ("recommended_next_step", "m3_line_id_matching_contract"),
            ("required_next_step", "m3_line_id_matching_contract"),
            ("m3_commit_cap", 7),
            ("allowed_event_fields", [*fixture["allowed_event_fields"], "raw_text"]),
            ("allowed_event_fields", fixture["allowed_event_fields"][:-1]),
            ("allowed_event_sources", [*fixture["allowed_event_sources"], "ui_text"]),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated[field] = value
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "raw text approved",
            "raw dialogue approved",
            "ui text reading approved",
            "unity scanning approved",
            "hook implementation approved",
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

    def test_docs_link_contract_fixture_checker_and_next_step(self) -> None:
        refs = (
            "docs/m3-current-line-event-contract.md",
            "tests/fixtures/m3_current_line_event_contract.synthetic.json",
            "scripts/check_m3_current_line_event_contract.py",
            RECOMMENDED_NEXT_STEP,
        )
        for path in (
            DOC_PATH,
            SCOPE_DOC_PATH,
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

        self.assertIn("scripts/check_m3_current_line_event_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m3-current-line-event-contract.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m3_current_line_event_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
