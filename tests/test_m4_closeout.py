from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m4_closeout import (
    DECISIONS_PENDING_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    KNOWN_RISKS_PATH,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m4_closeout_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M4CloseoutTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m4_closeout_errors())

    def test_fixture_closes_m4_and_points_to_m5(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m4-closeout.v1", fixture["schema_version"])
        self.assertEqual("M4", fixture["roadmap_milestone"])
        self.assertEqual("closed", fixture["scope_status"])
        self.assertEqual(6, fixture["m4_commit_cap"])
        self.assertEqual(6, fixture["m4_commits_used"])
        self.assertEqual("M5", fixture["next_roadmap_milestone"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        for field in REQUIRED_TRUE_FIELDS:
            self.assertIs(fixture[field], True)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            self.assertIs(fixture[field], False)

    def test_rejects_incomplete_m4_or_dangerous_permissions(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in REQUIRED_TRUE_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = False
            self.assertNotEqual([], _errors_for(mutated))
        for field in FORBIDDEN_PERMISSION_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = True
            self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_commit_cap_or_next_step_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field, value in (
            ("m4_commit_cap", 7),
            ("m4_commits_used", 7),
            ("next_roadmap_milestone", "M6"),
            ("recommended_next_step", "m5_pipeline_implementation"),
            ("required_next_step", "m5_pipeline_implementation"),
        ):
            mutated = copy.deepcopy(fixture)
            mutated[field] = value
            self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "native always-on-top approved",
            "global keyboard hook approved",
            "game input hook approved",
            "clipboard write approved",
            "provider execution approved",
            "raw provider payload",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "C:\\Users\\local\\secret",
            "screenshot archive",
        ):
            mutated = copy.deepcopy(fixture)
            mutated["unsafe_note"] = marker
            self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_closeout_fixture_checker_and_next_step(self) -> None:
        refs = (
            "docs/m4-closeout.md",
            "tests/fixtures/m4_closeout.synthetic.json",
            "scripts/check_m4_closeout.py",
            RECOMMENDED_NEXT_STEP,
        )
        for path in (
            DOC_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
            KNOWN_RISKS_PATH,
            DECISIONS_PENDING_PATH,
        ):
            text = path.read_text(encoding="utf-8").replace("\\", "/")
            for ref in refs:
                with self.subTest(path=path.relative_to(ROOT), ref=ref):
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m4_closeout.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m4-closeout.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m4_closeout_errors(path)


if __name__ == "__main__":
    unittest.main()
