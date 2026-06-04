from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m4_real_overlay_scope import (
    DECISIONS_PENDING_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INCOMPLETE_M4_FIELDS,
    KNOWN_RISKS_PATH,
    NEXT_ACTIONS_PATH,
    OVERLAY_DOC_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m4_real_overlay_scope_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M4RealOverlayScopeTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m4_real_overlay_scope_errors())

    def test_fixture_marks_m4_active_and_incomplete(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m4-real-overlay-scope.v1", fixture["schema_version"])
        self.assertEqual("M4", fixture["roadmap_milestone"])
        self.assertEqual("active", fixture["scope_status"])
        self.assertEqual(6, fixture["m4_commit_cap"])
        self.assertEqual(1, fixture["m4_commits_used"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in INCOMPLETE_M4_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_missing_reuse_or_completed_criteria(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in REQUIRED_TRUE_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = False
            self.assertNotEqual([], _errors_for(mutated))
        for field in INCOMPLETE_M4_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = True
            self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_dangerous_permissions_or_next_step_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = True
            self.assertNotEqual([], _errors_for(mutated))
        for field, value in (
            ("m4_commit_cap", 7),
            ("m4_commits_used", 2),
            ("recommended_next_step", "m4_compact_shell"),
            ("required_next_step", "m4_compact_shell"),
        ):
            mutated = copy.deepcopy(fixture)
            mutated[field] = value
            self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "native always-on-top approved",
            "global keyboard hook approved",
            "clipboard write approved",
            "provider execution approved",
            "companion contract change approved",
            "raw provider payload",
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

    def test_docs_link_scope_fixture_checker_and_next_step(self) -> None:
        refs = (
            "docs/m4-real-overlay-scope.md",
            "tests/fixtures/m4_real_overlay_scope.synthetic.json",
            "scripts/check_m4_real_overlay_scope.py",
            RECOMMENDED_NEXT_STEP,
        )
        for path in (
            DOC_PATH,
            OVERLAY_DOC_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
            KNOWN_RISKS_PATH,
            DECISIONS_PENDING_PATH,
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m4_real_overlay_scope.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m4-scope.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m4_real_overlay_scope_errors(path)


if __name__ == "__main__":
    unittest.main()
