from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_local_extraction_import_scope import (
    ALLOWED_PRIVATE_INPUT_ROOTS,
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INCOMPLETE_M2_FIELDS,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_local_extraction_import_scope_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2LocalExtractionImportScopeTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m2_local_extraction_import_scope_errors())

    def test_fixture_keeps_original_m2_incomplete(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m2-local-extraction-import-scope.v1", fixture["schema_version"])
        self.assertEqual("M2", fixture["roadmap_milestone"])
        self.assertEqual("contract_only", fixture["scope_status"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(list(ALLOWED_PRIVATE_INPUT_ROOTS), fixture["allowed_private_input_roots"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_OUTPUT_ROOTS), fixture["allowed_private_output_roots"]
        )
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in (*INCOMPLETE_M2_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_completed_m2_criteria(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in INCOMPLETE_M2_FIELDS:
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

    def test_rejects_unsafe_roots(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for root in (
            "data/extracted/",
            "../workspace/local-private/extraction-indexing/import/",
            "C:\\Users\\local\\private\\",
            "/home/local/private/",
            "workspace/local-private/",
        ):
            with self.subTest(root=root):
                mutated = dict(fixture)
                mutated["allowed_private_output_roots"] = [root]
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "real extraction approved",
            "current-line capture approved",
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

    def test_docs_link_fixture_checker_and_adr(self) -> None:
        refs = (
            "tests/fixtures/m2_local_extraction_import_scope.synthetic.json",
            "scripts/check_m2_local_extraction_import_scope.py",
            "docs/adr/0012-m2-local-extraction-import-scope.md",
        )
        for path in (DOC_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m2_local_extraction_import_scope.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-local-extraction-import-scope.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_m2_local_extraction_import_scope_errors(path)


if __name__ == "__main__":
    unittest.main()
