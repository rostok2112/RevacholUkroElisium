from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_line_index_contract import (
    ADR_PATH,
    ALLOWED_NEXT_INDEX_INPUTS,
    ALLOWED_PRIVATE_ENTRY_FIELDS,
    ALLOWED_PRIVATE_INDEX_FIELDS,
    ALLOWED_PRIVATE_INPUT_ROOTS,
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    ALLOWED_PUBLIC_SUMMARY_FIELDS,
    DOC_PATH,
    FINAL_IMPORT_DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_FALSE_FIELDS,
    LINE_INDEX_SCHEMA_VERSION,
    NEXT_ACTIONS_PATH,
    PRIVATE_DB_SCHEMA_VERSION,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_line_index_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2LineIndexContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m2_line_index_contract_errors())

    def test_fixture_approves_only_next_line_index_implementation(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m2-line-index-scope.v1", fixture["schema_version"])
        self.assertEqual("M2", fixture["roadmap_milestone"])
        self.assertEqual("line_index_contract", fixture["scope_status"])
        self.assertEqual(PRIVATE_DB_SCHEMA_VERSION, fixture["future_private_db_schema_version"])
        self.assertEqual(LINE_INDEX_SCHEMA_VERSION, fixture["future_line_index_schema_version"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["required_next_step"])
        self.assertEqual(list(ALLOWED_PRIVATE_INPUT_ROOTS), fixture["allowed_private_input_roots"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_OUTPUT_ROOTS), fixture["allowed_private_output_roots"]
        )
        self.assertEqual(list(ALLOWED_NEXT_INDEX_INPUTS), fixture["allowed_next_index_inputs"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_INDEX_FIELDS), fixture["allowed_private_index_fields"]
        )
        self.assertEqual(
            list(ALLOWED_PRIVATE_ENTRY_FIELDS), fixture["allowed_private_entry_fields"]
        )
        self.assertEqual(
            list(ALLOWED_PUBLIC_SUMMARY_FIELDS), fixture["allowed_public_summary_fields"]
        )
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in FORBIDDEN_FALSE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_required_true_fields_disabled(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = False
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_forbidden_fields_enabled(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in FORBIDDEN_FALSE_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = True
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_scope_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for mutation in (
            {"recommended_next_step": "m2_context_graph_contract"},
            {"required_next_step": "m2_context_graph_contract"},
            {"future_private_db_schema_version": "m2-local-private-export.v1"},
            {"allowed_next_index_inputs": ["context_edges"]},
            {"allowed_private_index_fields": ["entries"]},
            {"allowed_private_entry_fields": ["source_path"]},
            {"allowed_public_summary_fields": ["input_path"]},
        ):
            with self.subTest(mutation=mutation):
                mutated = dict(fixture)
                mutated.update(mutation)
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_roots(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for root in (
            "data/extracted/",
            "../workspace/local-private/extraction-indexing/import/line-index/",
            "C:\\Users\\local\\private\\",
            "/home/local/private/",
            "workspace/local-private/extraction-indexing/input/",
        ):
            with self.subTest(root=root):
                mutated = dict(fixture)
                mutated["allowed_private_output_roots"] = [root]
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "context graph construction approved",
            "retrieval bucket mapping approved",
            "directory input approved",
            "current-line capture approved",
            "commit line index approved",
            "commit extracted text approved",
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

    def test_requires_workspace_ignore(self) -> None:
        self.assertIn("workspace/", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_docs_link_contract_fixture_and_checker(self) -> None:
        refs = (
            "docs/m2-line-index-contract.md",
            "tests/fixtures/m2_line_index_scope.synthetic.json",
            "scripts/check_m2_line_index_contract.py",
        )
        for path in (
            DOC_PATH,
            ADR_PATH,
            FINAL_IMPORT_DOC_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m2_line_index_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-line-index-scope.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m2_line_index_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
