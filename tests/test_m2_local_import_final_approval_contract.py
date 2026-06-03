from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_local_import_final_approval_contract import (
    ADR_PATH,
    ALLOWED_NEXT_IMPORT_INPUTS,
    ALLOWED_PRIVATE_IMPORT_FIELDS,
    ALLOWED_PRIVATE_INPUT_ROOTS,
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    ALLOWED_PUBLIC_SUMMARY_FIELDS,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INCOMPLETE_M2_FIELDS,
    INTEGRITY_DOC_PATH,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_local_import_final_approval_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2LocalImportFinalApprovalContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m2_local_import_final_approval_contract_errors())

    def test_fixture_approves_only_local_import_next_and_keeps_m2_incomplete(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m2-local-import-final-approval-scope.v1", fixture["schema_version"])
        self.assertEqual("M2", fixture["roadmap_milestone"])
        self.assertEqual("final_approval_contract", fixture["scope_status"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["required_next_step"])
        self.assertEqual(list(ALLOWED_PRIVATE_INPUT_ROOTS), fixture["allowed_private_input_roots"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_OUTPUT_ROOTS), fixture["allowed_private_output_roots"]
        )
        self.assertEqual(list(ALLOWED_NEXT_IMPORT_INPUTS), fixture["allowed_next_import_inputs"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_IMPORT_FIELDS), fixture["allowed_private_import_fields"]
        )
        self.assertEqual(
            list(ALLOWED_PUBLIC_SUMMARY_FIELDS), fixture["allowed_public_summary_fields"]
        )
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in (*INCOMPLETE_M2_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_disabling_required_final_approval_fields(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in REQUIRED_TRUE_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = False
                self.assertNotEqual([], _errors_for(mutated))

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

    def test_rejects_next_step_or_import_scope_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for mutation in (
            {"recommended_next_step": "m2_line_index_contract"},
            {"required_next_step": "m2_line_index_contract"},
            {"allowed_next_import_inputs": ["records"]},
            {"allowed_private_import_fields": ["records"]},
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
            "../workspace/local-private/extraction-indexing/import/db/",
            "C:\\Users\\local\\private\\",
            "/home/local/private/",
            "workspace/local-private/extraction-indexing/import/",
        ):
            with self.subTest(root=root):
                mutated = dict(fixture)
                mutated["allowed_private_output_roots"] = [root]
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "line index construction approved",
            "context graph construction approved",
            "retrieval bucket mapping approved",
            "directory input approved",
            "current-line capture approved",
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
            "docs/m2-local-import-final-approval-contract.md",
            "tests/fixtures/m2_local_import_final_approval_scope.synthetic.json",
            "scripts/check_m2_local_import_final_approval_contract.py",
        )
        for path in (
            DOC_PATH,
            ADR_PATH,
            INTEGRITY_DOC_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m2_local_import_final_approval_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-local-import-final-approval-scope.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m2_local_import_final_approval_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
