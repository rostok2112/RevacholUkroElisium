from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_dry_run_summary_hash_contract import (
    ADR_PATH,
    ALLOWED_CANONICAL_SUMMARY_FIELDS,
    CANONICALIZATION_RULES,
    DOC_PATH,
    EXCLUDED_HASH_INPUT_FIELDS,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    HASH_DECISION_DOC,
    INDEX_CONTRACT_DOC,
    INPUT_CONTRACT_DOC,
    PRIVATE_OUTPUT_ROOT,
    RECOMMENDED_NEXT_STEP,
    SCHEMA_VERSION,
    collect_dry_run_summary_hash_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class DryRunSummaryHashContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_dry_run_summary_hash_contract_errors())

    def test_fixture_shape_keeps_hash_implementation_blocked(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual(SCHEMA_VERSION, fixture["schema_version"])
        self.assertEqual("5A.6", fixture["milestone"])
        self.assertEqual("contract_only", fixture["decision_status"])
        self.assertFalse(fixture["hash_implementation_allowed_next"])
        self.assertEqual(
            "contract_defined_only",
            fixture["canonical_redacted_summary_hash_allowed_next"],
        )
        self.assertFalse(fixture["file_content_hashing_allowed"])
        self.assertFalse(fixture["path_string_hashing_allowed"])
        self.assertFalse(fixture["filename_hashing_allowed"])
        self.assertFalse(fixture["raw_payload_hashing_allowed"])
        self.assertFalse(fixture["private_index_construction_allowed_next"])
        self.assertEqual(PRIVATE_OUTPUT_ROOT, fixture["private_output_root"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])

    def test_fixture_keeps_dangerous_permissions_false(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_fixture_lists_are_stable_and_non_overlapping(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual(
            list(ALLOWED_CANONICAL_SUMMARY_FIELDS),
            fixture["allowed_canonical_summary_fields"],
        )
        self.assertEqual(list(EXCLUDED_HASH_INPUT_FIELDS), fixture["excluded_hash_input_fields"])
        self.assertEqual(list(CANONICALIZATION_RULES), fixture["canonicalization_rules"])
        self.assertEqual(
            set(),
            set(fixture["allowed_canonical_summary_fields"])
            & set(fixture["excluded_hash_input_fields"]),
        )

    def test_rejects_forbidden_permissions_true(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = True

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unexpected_canonical_hash_status(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = dict(fixture)
        mutated["canonical_redacted_summary_hash_allowed_next"] = True

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

    def test_rejects_list_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in (
            "allowed_canonical_summary_fields",
            "excluded_hash_input_fields",
            "canonicalization_rules",
        ):
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = [*fixture[field], "unexpected_field"]

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_allowed_and_excluded_overlap(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = dict(fixture)
        mutated["excluded_hash_input_fields"] = [
            *fixture["excluded_hash_input_fields"],
            "file_count",
        ]

        self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "hash implementation approved",
            "file content hashing approved",
            "path string hashing approved",
            "filename hashing approved",
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
        fixture_ref = "tests/fixtures/dry_run_summary_hash_contract.synthetic.json"
        checker_ref = "scripts/check_dry_run_summary_hash_contract.py"
        doc_ref = "docs/extraction-indexing-dry-run-summary-hash-contract.md"

        for path in (DOC_PATH, ADR_PATH, HASH_DECISION_DOC, INPUT_CONTRACT_DOC, INDEX_CONTRACT_DOC):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                self.assertIn(fixture_ref, text)
                self.assertIn(checker_ref, text)
                self.assertIn(doc_ref, text)

    def test_docs_do_not_approve_hashing_or_extraction(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                DOC_PATH,
                ADR_PATH,
                HASH_DECISION_DOC,
                INPUT_CONTRACT_DOC,
                INDEX_CONTRACT_DOC,
            )
        ).lower()

        self.assertNotIn("hash implementation is approved", combined)
        self.assertNotIn("file content hashing is approved", combined)
        self.assertNotIn("path string hashing is approved", combined)
        self.assertNotIn("filename hashing is approved", combined)
        self.assertNotIn("private index construction is approved", combined)
        self.assertNotIn("real extraction is approved", combined)
        self.assertNotIn("current-line capture is approved", combined)
        self.assertNotIn("ui text reading is approved", combined)
        self.assertNotIn("unity scanning is approved", combined)
        self.assertNotIn("ocr is approved", combined)
        self.assertNotIn("provider execution is approved", combined)
        self.assertIn("does not implement hashing", combined)

    def test_check_all_registers_dry_run_summary_hash_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_dry_run_summary_hash_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "dry-run-summary-hash-contract.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_dry_run_summary_hash_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
