from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_extraction_indexing_scope import (
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    LOCAL_WORKFLOW_DOC,
    RECOMMENDED_NEXT_STEP,
    collect_extraction_indexing_scope_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class ExtractionIndexingScopeTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_extraction_indexing_scope_errors())

    def test_fixture_shape_is_contract_only(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("extraction-indexing-scope.v1", fixture["schema_version"])
        self.assertEqual("5A", fixture["milestone"])
        self.assertEqual("contract_only", fixture["scope_status"])
        self.assertFalse(fixture["implementation_allowed_next"])
        self.assertTrue(fixture["local_only"])
        self.assertTrue(fixture["synthetic_fixtures_allowed"])
        self.assertTrue(fixture["user_selected_private_inputs_allowed"])
        self.assertTrue(fixture["metadata_only_file_summaries_allowed"])
        self.assertTrue(fixture["private_index_allowed"])
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

    def test_rejects_unsafe_output_roots(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for root in (
            "data/extracted/",
            "../workspace/local-private/extraction-indexing/",
            "C:\\Users\\local\\private\\extraction-indexing\\",
            "/home/local/private/extraction-indexing/",
            "workspace/local-private/",
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
        ):
            with self.subTest(marker=marker):
                mutated = dict(fixture)
                mutated["unsafe_note"] = marker

                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_fixture_and_checker(self) -> None:
        fixture_ref = "tests/fixtures/extraction_indexing_scope.synthetic.json"
        checker_ref = "scripts/check_extraction_indexing_scope.py"

        for path in (DOC_PATH, LOCAL_WORKFLOW_DOC):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                self.assertIn(fixture_ref, text)
                self.assertIn(checker_ref, text)

    def test_docs_do_not_approve_capture_or_implementation(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (DOC_PATH, LOCAL_WORKFLOW_DOC)
        ).lower()

        self.assertNotIn("current-line capture is approved", combined)
        self.assertNotIn("real text capture is approved", combined)
        self.assertNotIn("automatic game install scanning is approved", combined)
        self.assertNotIn("real extraction implementation is approved", combined)
        self.assertIn("real extraction/indexing implementation remains blocked", combined)

    def test_check_all_registers_scope_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_extraction_indexing_scope.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "extraction-indexing-scope.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_extraction_indexing_scope_errors(path)


if __name__ == "__main__":
    unittest.main()
