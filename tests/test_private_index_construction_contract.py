from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_private_index_construction_contract import (
    ADR_PATH,
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    HASH_CONTRACT_DOC,
    INPUT_CONTRACT_DOC,
    PRIVATE_INDEX_DOC,
    RECOMMENDED_NEXT_STEP,
    SCHEMA_VERSION,
    collect_private_index_construction_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class PrivateIndexConstructionContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_private_index_construction_contract_errors())

    def test_fixture_shape_keeps_builder_blocked(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual(SCHEMA_VERSION, fixture["schema_version"])
        self.assertEqual("5A.9", fixture["milestone"])
        self.assertEqual("contract_only", fixture["decision_status"])
        self.assertFalse(fixture["private_index_builder_allowed_next"])
        self.assertEqual(
            "contract_defined_only",
            fixture["private_index_construction_allowed_next"],
        )
        self.assertEqual(
            list(ALLOWED_PRIVATE_OUTPUT_ROOTS), fixture["allowed_private_output_roots"]
        )
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

    def test_rejects_builder_or_construction_enabled(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field, value in (
            ("private_index_builder_allowed_next", True),
            ("private_index_construction_allowed_next", True),
            ("private_index_construction_allowed_next", "implementation_allowed"),
        ):
            with self.subTest(field=field, value=value):
                mutated = dict(fixture)
                mutated[field] = value

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_output_roots(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for root in (
            "workspace/local-private/extraction-indexing/",
            "workspace/synthetic-slice/extraction-indexing/index/",
            "../workspace/local-private/extraction-indexing/index/",
            "C:\\Users\\local\\private\\index\\",
            "/home/local/private/index/",
            "workspace/local-private/extraction-indexing/index",
        ):
            with self.subTest(root=root):
                mutated = dict(fixture)
                mutated["allowed_private_output_roots"] = [root]

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "private index builder approved",
            "private index construction approved",
            "real extraction approved",
            "file contents approved",
            "file content hashing approved",
            "path string hashing approved",
            "filename hashing approved",
            "raw payload dump",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "C:\\Users\\local\\secret",
            "screenshot archive",
            "steamapps/common",
        ):
            with self.subTest(marker=marker):
                mutated = dict(fixture)
                mutated["unsafe_note"] = marker

                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_fixture_checker_and_contract(self) -> None:
        fixture_ref = "tests/fixtures/private_index_construction_contract.synthetic.json"
        checker_ref = "scripts/check_private_index_construction_contract.py"
        doc_ref = "docs/extraction-indexing-private-index-construction-contract.md"

        for path in (DOC_PATH, ADR_PATH, PRIVATE_INDEX_DOC, HASH_CONTRACT_DOC, INPUT_CONTRACT_DOC):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                self.assertIn(fixture_ref, text)
                self.assertIn(checker_ref, text)
                self.assertIn(doc_ref, text)

    def test_docs_do_not_approve_implementation_or_capture(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                DOC_PATH,
                ADR_PATH,
                PRIVATE_INDEX_DOC,
                HASH_CONTRACT_DOC,
                INPUT_CONTRACT_DOC,
            )
        ).lower()

        self.assertNotIn("private index builder is approved", combined)
        self.assertNotIn("private index implementation is approved", combined)
        self.assertNotIn("real extraction is approved", combined)
        self.assertNotIn("file contents are approved", combined)
        self.assertNotIn("file content hashing is approved", combined)
        self.assertNotIn("path string hashing is approved", combined)
        self.assertNotIn("filename hashing is approved", combined)
        self.assertNotIn("current-line capture is approved", combined)
        self.assertNotIn("ui text reading is approved", combined)
        self.assertNotIn("unity scanning is approved", combined)
        self.assertNotIn("ocr is approved", combined)
        self.assertNotIn("provider execution is approved", combined)
        self.assertIn("does not implement private index construction", combined)

    def test_check_all_registers_private_index_construction_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_private_index_construction_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "private-index-construction-contract.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_private_index_construction_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
