from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_synthetic_import_format import (
    ADR_PATH,
    ALLOWED_RELATIONS,
    DOC_PATH,
    FIXTURE_PATH,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    SAFETY_FLAG_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_synthetic_import_format_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2SyntheticImportFormatTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m2_synthetic_import_format_errors())

    def test_fixture_keeps_m2_contract_only(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m2-synthetic-import-db.v1", fixture["schema_version"])
        self.assertEqual("synthetic_fixture", fixture["source_kind"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["metadata"]["recommended_next_step"])
        self.assertEqual(
            set(ALLOWED_RELATIONS), {edge["relation"] for edge in fixture["context_edges"]}
        )
        for field in SAFETY_FLAG_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture["safety_flags"][field], False)

    def test_rejects_duplicate_ids(self) -> None:
        fixture = _fixture_copy()
        fixture["records"][1]["record_id"] = fixture["records"][0]["record_id"]
        fixture["records"][1]["line_id"] = fixture["records"][0]["record_id"]

        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_missing_record_field(self) -> None:
        fixture = _fixture_copy()
        del fixture["records"][0]["speaker_id"]

        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_broken_context_edge(self) -> None:
        fixture = _fixture_copy()
        fixture["context_edges"][0]["to_record_id"] = "synthetic.m2.line.missing"

        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_self_context_edge(self) -> None:
        fixture = _fixture_copy()
        fixture["context_edges"][0]["to_record_id"] = fixture["context_edges"][0]["from_record_id"]

        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_unknown_relation(self) -> None:
        fixture = _fixture_copy()
        fixture["context_edges"][0]["relation"] = "future_spoiler"

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
            "current-line capture approved",
        ):
            with self.subTest(marker=marker):
                fixture = _fixture_copy()
                fixture["records"][0]["source_text"] = marker
                self.assertNotEqual([], _errors_for(fixture))

    def test_docs_link_fixture_checker_and_contract(self) -> None:
        refs = (
            "tests/fixtures/m2_synthetic_import_db.synthetic.json",
            "scripts/check_m2_synthetic_import_format.py",
            "docs/m2-synthetic-import-format-contract.md",
        )
        for path in (DOC_PATH, ADR_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m2_synthetic_import_format.py", text)


def _fixture_copy() -> dict[str, object]:
    return copy.deepcopy(load_json(FIXTURE_PATH))


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-synthetic-import-db.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_m2_synthetic_import_format_errors(path)


if __name__ == "__main__":
    unittest.main()
