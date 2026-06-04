from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m3_bepinex_bridge_scope import (
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INCOMPLETE_M3_FIELDS,
    M3_COMMIT_CAP,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m3_bepinex_bridge_scope_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M3BepInExBridgeScopeTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m3_bepinex_bridge_scope_errors())

    def test_fixture_records_m3_active_and_incomplete(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m3-bepinex-bridge-scope.v1", fixture["schema_version"])
        self.assertEqual("M3", fixture["roadmap_milestone"])
        self.assertEqual("baseline_recovery", fixture["scope_status"])
        self.assertEqual(M3_COMMIT_CAP, fixture["m3_commit_cap"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in (*INCOMPLETE_M3_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_completed_m3_criteria(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in INCOMPLETE_M3_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = True
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_forbidden_permissions(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = True
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_commit_cap_or_next_step_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for mutation in (
            {"m3_commit_cap": 7},
            {"recommended_next_step": "m3_current_line_event_implementation"},
            {"required_next_step": "m3_current_line_event_implementation"},
        ):
            with self.subTest(mutation=mutation):
                mutated = dict(fixture)
                mutated.update(mutation)
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "current-line capture approved",
            "real text capture approved",
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
                mutated = dict(fixture)
                mutated["unsafe_note"] = marker
                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_fixture_checker_and_next_step(self) -> None:
        refs = (
            "docs/m3-bepinex-bridge-scope.md",
            "tests/fixtures/m3_bepinex_bridge_scope.synthetic.json",
            "scripts/check_m3_bepinex_bridge_scope.py",
            RECOMMENDED_NEXT_STEP,
        )
        for path in (DOC_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m3_bepinex_bridge_scope.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m3-bepinex-bridge-scope.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_m3_bepinex_bridge_scope_errors(path)


if __name__ == "__main__":
    unittest.main()
