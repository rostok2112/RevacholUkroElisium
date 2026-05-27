from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_extraction_private_input_adapter_contract import (
    ADR_PATH,
    ALLOWED_PRIVATE_INPUT_ROOTS,
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    INDEX_CONTRACT_DOC,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_SUMMARY_FIELDS,
    collect_extraction_private_input_adapter_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class ExtractionPrivateInputAdapterContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_extraction_private_input_adapter_contract_errors())

    def test_fixture_shape_is_contract_only(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("extraction-private-input-adapter-scope.v1", fixture["schema_version"])
        self.assertEqual("5A.2", fixture["milestone"])
        self.assertEqual("contract_only", fixture["scope_status"])
        self.assertFalse(fixture["implementation_allowed_next"])
        self.assertTrue(fixture["explicit_user_selected_input_required"])
        self.assertTrue(fixture["dry_run_metadata_summary_default"])
        self.assertFalse(fixture["external_absolute_input_paths_allowed"])
        self.assertEqual(list(ALLOWED_PRIVATE_INPUT_ROOTS), fixture["allowed_private_input_roots"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_OUTPUT_ROOTS), fixture["allowed_private_output_roots"]
        )
        self.assertEqual(list(REQUIRED_SUMMARY_FIELDS), fixture["allowed_tracked_summary_fields"])
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

    def test_rejects_missing_explicit_input_requirement(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = dict(fixture)
        mutated["explicit_user_selected_input_required"] = False

        self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_missing_dry_run_default(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = dict(fixture)
        mutated["dry_run_metadata_summary_default"] = False

        self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_input_roots(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for root in (
            "workspace/local-private/extraction-indexing/",
            "workspace/synthetic-slice/extraction-indexing/input/",
            "../workspace/local-private/extraction-indexing/input/",
            "C:\\Users\\local\\private\\input\\",
            "/home/local/private/input/",
            "workspace/local-private/extraction-indexing/input",
        ):
            with self.subTest(root=root):
                mutated = dict(fixture)
                mutated["allowed_private_input_roots"] = [root]

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_output_roots(self) -> None:
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
                mutated["allowed_private_output_roots"] = [root]

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "current-line capture approved",
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

    def test_docs_link_fixture_and_checker(self) -> None:
        fixture_ref = "tests/fixtures/extraction_private_input_adapter_scope.synthetic.json"
        checker_ref = "scripts/check_extraction_private_input_adapter_contract.py"

        for path in (DOC_PATH, ADR_PATH, INDEX_CONTRACT_DOC):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                self.assertIn(fixture_ref, text)
                self.assertIn(checker_ref, text)

    def test_docs_do_not_approve_capture_or_real_input_reading(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (DOC_PATH, ADR_PATH, INDEX_CONTRACT_DOC)
        ).lower()

        self.assertNotIn("current-line capture is approved", combined)
        self.assertNotIn("real text capture is approved", combined)
        self.assertNotIn("automatic game install scanning is approved", combined)
        self.assertNotIn("real extraction implementation is approved", combined)
        self.assertNotIn("external absolute input paths are approved", combined)
        self.assertIn("implementation remains blocked", combined)

    def test_check_all_registers_private_input_adapter_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_extraction_private_input_adapter_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "extraction-private-input-adapter-scope.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_extraction_private_input_adapter_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
