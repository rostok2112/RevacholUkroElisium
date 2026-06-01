from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.m2_synthetic_import_validator import (
    M2SyntheticImportValidationError,
    assert_valid_m2_synthetic_import,
    collect_m2_synthetic_import_errors,
    load_and_validate_m2_synthetic_import,
)
from scripts.schema_validator import collect_errors, load_json


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/m2_synthetic_import_db.synthetic.json"
SCHEMA_PATH = ROOT / "specs/m2-synthetic-import-db.schema.json"


class M2SyntheticImportValidatorTests(unittest.TestCase):
    def test_schema_accepts_canonical_fixture(self) -> None:
        self.assertEqual([], collect_errors(load_json(FIXTURE_PATH), load_json(SCHEMA_PATH)))

    def test_assert_and_load_accept_canonical_fixture(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        assert_valid_m2_synthetic_import(fixture)
        self.assertEqual(fixture, load_and_validate_m2_synthetic_import(FIXTURE_PATH))

    def test_assert_rejects_invalid_fixture(self) -> None:
        fixture = _fixture_copy()
        fixture["records"][0]["speaker_id"] = "not-synthetic"

        with self.assertRaises(M2SyntheticImportValidationError):
            assert_valid_m2_synthetic_import(fixture)

    def test_rejects_duplicate_edge(self) -> None:
        fixture = _fixture_copy()
        fixture["context_edges"].append(copy.deepcopy(fixture["context_edges"][0]))

        self.assertNotEqual([], collect_m2_synthetic_import_errors(fixture))

    def test_rejects_non_synthetic_placeholder(self) -> None:
        fixture = _fixture_copy()
        fixture["records"][0]["context_placeholder"] = "office_entry"

        self.assertNotEqual([], collect_m2_synthetic_import_errors(fixture))

    def test_rejects_unexpected_structural_field(self) -> None:
        fixture = _fixture_copy()
        fixture["records"][0]["private_filename"] = "local.txt"

        self.assertNotEqual([], collect_m2_synthetic_import_errors(fixture))

    def test_load_reads_only_explicit_file(self) -> None:
        fixture = _fixture_copy()
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "explicit.synthetic.json"
            path.write_text(json.dumps(fixture), encoding="utf-8")

            self.assertEqual(fixture, load_and_validate_m2_synthetic_import(path))


def _fixture_copy() -> dict[str, object]:
    return copy.deepcopy(load_json(FIXTURE_PATH))


if __name__ == "__main__":
    unittest.main()
