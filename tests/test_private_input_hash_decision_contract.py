from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_private_input_hash_decision_contract import (
    ADR_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INDEX_CONTRACT_DOC,
    INPUT_CONTRACT_DOC,
    PRIVATE_OUTPUT_ROOT,
    RECOMMENDED_NEXT_STEP,
    SCHEMA_VERSION,
    collect_private_input_hash_decision_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class PrivateInputHashDecisionContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_private_input_hash_decision_contract_errors())

    def test_fixture_shape_keeps_hash_implementation_blocked(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual(SCHEMA_VERSION, fixture["schema_version"])
        self.assertEqual("5A.5", fixture["milestone"])
        self.assertEqual("contract_only", fixture["decision_status"])
        self.assertFalse(fixture["hash_implementation_allowed_next"])
        self.assertFalse(fixture["file_content_hashing_allowed"])
        self.assertFalse(fixture["path_string_hashing_allowed"])
        self.assertEqual("decision_pending", fixture["dry_run_summary_hashing_allowed_next"])
        self.assertFalse(fixture["private_index_construction_allowed_next"])
        self.assertEqual(PRIVATE_OUTPUT_ROOT, fixture["private_output_root"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])

    def test_fixture_keeps_dangerous_permissions_false(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_forbidden_permissions_true(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = True

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_hash_decision_implementation_or_private_index_approval(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in (
            "hash_implementation_allowed_next",
            "file_content_hashing_allowed",
            "path_string_hashing_allowed",
            "private_index_construction_allowed_next",
        ):
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = True

                errors = _errors_for(mutated)

                self.assertNotEqual([], errors)

    def test_rejects_unexpected_summary_hash_state(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = dict(fixture)
        mutated["dry_run_summary_hashing_allowed_next"] = True

        self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_private_output_root(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for root in (
            "workspace/synthetic-slice/extraction-indexing/",
            "../workspace/local-private/extraction-indexing/",
            "C:\\Users\\local\\private\\extraction-indexing\\",
            "/home/local/private/extraction-indexing/",
            "workspace/local-private/extraction-indexing",
        ):
            with self.subTest(root=root):
                mutated = dict(fixture)
                mutated["private_output_root"] = root

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "hash implementation approved",
            "file content hashing approved",
            "path string hashing approved",
            "private index construction approved",
            "raw payload dump",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "C:\\Users\\local\\secret",
            "screenshot archive",
        ):
            with self.subTest(marker=marker):
                mutated = dict(fixture)
                mutated["unsafe_note"] = marker

                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_fixture_checker_and_contract(self) -> None:
        fixture_ref = "tests/fixtures/private_input_hash_decision.synthetic.json"
        checker_ref = "scripts/check_private_input_hash_decision_contract.py"
        doc_ref = "docs/extraction-indexing-private-input-hash-contract.md"

        for path in (DOC_PATH, ADR_PATH, INPUT_CONTRACT_DOC, INDEX_CONTRACT_DOC):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                self.assertIn(fixture_ref, text)
                self.assertIn(checker_ref, text)
                self.assertIn(doc_ref, text)

    def test_docs_do_not_approve_hashing_or_extraction(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (DOC_PATH, ADR_PATH, INPUT_CONTRACT_DOC, INDEX_CONTRACT_DOC)
        ).lower()

        self.assertNotIn("hash implementation is approved", combined)
        self.assertNotIn("file content hashing is approved", combined)
        self.assertNotIn("path string hashing is approved", combined)
        self.assertNotIn("private index construction is approved", combined)
        self.assertNotIn("real extraction is approved", combined)
        self.assertNotIn("current-line capture is approved", combined)
        self.assertNotIn("ui text reading is approved", combined)
        self.assertNotIn("unity scanning is approved", combined)
        self.assertNotIn("ocr is approved", combined)
        self.assertNotIn("provider execution is approved", combined)
        self.assertIn("does not implement hashing", combined)

    def test_check_all_registers_private_input_hash_decision_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_private_input_hash_decision_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "private-input-hash-decision.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_private_input_hash_decision_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
