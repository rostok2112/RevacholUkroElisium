from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_synthetic_line_index_contract import (
    ADR_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    NEXT_ACTIONS_PATH,
    SAFETY_FLAG_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_synthetic_line_index_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2SyntheticLineIndexContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m2_synthetic_line_index_contract_errors())

    def test_rejects_missing_duplicate_or_extra_entries(self) -> None:
        for transform in (_remove_entry, _duplicate_entry, _add_extra_entry):
            with self.subTest(transform=transform.__name__):
                fixture = _fixture_copy()
                transform(fixture)
                self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_incorrect_mapping(self) -> None:
        fixture = _fixture_copy()
        fixture["entries"][0]["speaker_id"] = "synthetic.m2.speaker.wrong"

        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_unstable_order(self) -> None:
        fixture = _fixture_copy()
        fixture["entries"][0], fixture["entries"][1] = fixture["entries"][1], fixture["entries"][0]

        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_source_text_leakage(self) -> None:
        fixture = _fixture_copy()
        fixture["entries"][0]["source_text"] = "invented but forbidden in the line index"

        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_dangerous_safety_flags(self) -> None:
        fixture = _fixture_copy()
        for field in SAFETY_FLAG_FIELDS:
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated["safety_flags"][field] = True
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        for marker in (
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
                fixture = _fixture_copy()
                fixture["entries"][0]["context_placeholder"] = marker
                self.assertNotEqual([], _errors_for(fixture))

    def test_docs_link_contract_fixture_schema_and_checker(self) -> None:
        refs = (
            "docs/m2-synthetic-line-index-contract.md",
            "specs/m2-synthetic-line-index.schema.json",
            "tests/fixtures/m2_synthetic_line_index.synthetic.json",
            "scripts/check_m2_synthetic_line_index_contract.py",
        )
        for path in (DOC_PATH, ADR_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m2_synthetic_line_index_contract.py", text)


def _fixture_copy() -> dict[str, object]:
    return copy.deepcopy(load_json(FIXTURE_PATH))


def _remove_entry(fixture: dict[str, object]) -> None:
    fixture["entries"].pop()
    fixture["record_count"] -= 1


def _duplicate_entry(fixture: dict[str, object]) -> None:
    fixture["entries"].append(copy.deepcopy(fixture["entries"][0]))
    fixture["record_count"] += 1


def _add_extra_entry(fixture: dict[str, object]) -> None:
    extra = copy.deepcopy(fixture["entries"][0])
    extra["line_id"] = "synthetic.m2.line.999"
    extra["record_id"] = "synthetic.m2.line.999"
    fixture["entries"].append(extra)
    fixture["record_count"] += 1


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-synthetic-line-index.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m2_synthetic_line_index_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
