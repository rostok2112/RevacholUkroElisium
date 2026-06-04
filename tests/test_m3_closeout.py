from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m3_closeout import (
    BEPINEX_DOC_PATH,
    DECISIONS_PENDING_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    KNOWN_RISKS_PATH,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m3_closeout_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M3CloseoutTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m3_closeout_errors())

    def test_fixture_closes_m3_and_points_to_m4_recovery(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m3-closeout.v1", fixture["schema_version"])
        self.assertEqual("M3", fixture["roadmap_milestone"])
        self.assertEqual("closed", fixture["scope_status"])
        self.assertNotIn("m3_commit_cap", fixture)
        self.assertNotIn("m3_commits_used", fixture)
        self.assertEqual("M4", fixture["next_roadmap_milestone"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_incomplete_m3_or_dangerous_permissions(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in REQUIRED_TRUE_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = False
            self.assertNotEqual([], _errors_for(mutated))
        for field in FORBIDDEN_PERMISSION_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = True
            self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_legacy_commit_cap_or_next_step_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutations = (
            ("m3_commit_cap", 6),
            ("m3_commits_used", 6),
            ("next_roadmap_milestone", "M5"),
            ("recommended_next_step", "m4_implementation"),
            ("required_next_step", "m4_implementation"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated[field] = value
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "raw text capture approved",
            "payload dump approved",
            "line id dump approved",
            "provider execution approved",
            "companion contract change approved",
            "raw payload dump",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "C:\\Users\\local\\secret",
            "screenshot archive",
            "decompiled output",
        ):
            with self.subTest(marker=marker):
                mutated = copy.deepcopy(fixture)
                mutated["unsafe_note"] = marker
                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_closeout_fixture_checker_and_next_step(self) -> None:
        refs = (
            "docs/m3-closeout.md",
            "tests/fixtures/m3_closeout.synthetic.json",
            "scripts/check_m3_closeout.py",
            RECOMMENDED_NEXT_STEP,
        )
        for path in (
            DOC_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
            KNOWN_RISKS_PATH,
            DECISIONS_PENDING_PATH,
            BEPINEX_DOC_PATH,
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m3_closeout.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m3-closeout.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m3_closeout_errors(path)


if __name__ == "__main__":
    unittest.main()
