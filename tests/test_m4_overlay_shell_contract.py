from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m4_overlay_shell_contract import (
    DECISIONS_PENDING_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INCOMPLETE_M4_FIELDS,
    KNOWN_RISKS_PATH,
    NEXT_ACTIONS_PATH,
    OVERLAY_DOC_PATH,
    RECOMMENDED_NEXT_STEP,
    SESSION_SUMMARY_PATH,
    collect_m4_overlay_shell_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M4OverlayShellContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m4_overlay_shell_contract_errors())

    def test_fixture_is_contract_only(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m4-overlay-shell-contract.v1", fixture["schema_version"])
        self.assertEqual("M4", fixture["roadmap_milestone"])
        self.assertEqual("contract_only", fixture["scope_status"])
        self.assertNotIn("m4_commit_cap", fixture)
        self.assertNotIn("m4_commits_used", fixture)
        self.assertEqual(
            ["workspace/local-private/overlay/"], fixture["allowed_private_output_roots"]
        )
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        for field in INCOMPLETE_M4_FIELDS:
            self.assertIs(fixture[field], False)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            self.assertIs(fixture[field], False)

    def test_rejects_implementation_or_completion_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in INCOMPLETE_M4_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = True
            self.assertNotEqual([], _errors_for(mutated))
        for field in FORBIDDEN_PERMISSION_FIELDS:
            mutated = copy.deepcopy(fixture)
            mutated[field] = True
            self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_contract_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field, value in (
            ("m4_commit_cap", 6),
            ("m4_commits_used", 2),
            ("recommended_next_step", "m4_shell_implementation"),
            ("required_next_step", "m4_shell_implementation"),
            ("allowed_private_output_roots", ["workspace/synthetic-slice/overlay/"]),
            ("allowed_input_schema_versions", ["new-overlay-state.v1"]),
            ("required_reused_modules", ["scripts/new_overlay.py"]),
        ):
            mutated = copy.deepcopy(fixture)
            mutated[field] = value
            self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "global keyboard hook approved",
            "clipboard write approved",
            "debug internals in player view approved",
            "raw provider payload",
            "raw prompt",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "C:\\Users\\local\\secret",
            "screenshot archive",
        ):
            with self.subTest(marker=marker):
                mutated = copy.deepcopy(fixture)
                mutated["unsafe_note"] = marker
                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_contract_fixture_checker_and_next_step(self) -> None:
        refs = (
            "docs/m4-overlay-shell-contract.md",
            "tests/fixtures/m4_overlay_shell_contract.synthetic.json",
            "scripts/check_m4_overlay_shell_contract.py",
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
            text = path.read_text(encoding="utf-8").replace("\\", "/")
            for ref in refs:
                with self.subTest(path=path.relative_to(ROOT), ref=ref):
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m4_overlay_shell_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m4-shell-contract.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m4_overlay_shell_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
