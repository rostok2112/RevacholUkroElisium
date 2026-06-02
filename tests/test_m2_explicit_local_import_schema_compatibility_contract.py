from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_explicit_local_import_schema_compatibility_contract import (
    ADAPTER_DOC_PATH,
    ADR_PATH,
    ALLOWED_ENVELOPE_FIELDS,
    ALLOWED_FUTURE_SUMMARY_FIELDS,
    ALLOWED_PRIVATE_INPUT_ROOTS,
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    FUTURE_PROFILE_SCHEMA_VERSION,
    INCOMPLETE_M2_FIELDS,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_explicit_local_import_schema_compatibility_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2ExplicitLocalImportSchemaCompatibilityContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual(
            [],
            collect_m2_explicit_local_import_schema_compatibility_contract_errors(),
        )

    def test_fixture_keeps_contract_static_and_m2_incomplete(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual(
            "m2-explicit-local-import-schema-compatibility-scope.v1",
            fixture["schema_version"],
        )
        self.assertEqual("M2", fixture["roadmap_milestone"])
        self.assertEqual("contract_only", fixture["scope_status"])
        self.assertEqual("utf8_json_object", fixture["future_input_format"])
        self.assertEqual(FUTURE_PROFILE_SCHEMA_VERSION, fixture["future_profile_schema_version"])
        self.assertEqual("top_level_envelope_only", fixture["inspection_depth"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(list(ALLOWED_PRIVATE_INPUT_ROOTS), fixture["allowed_private_input_roots"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_OUTPUT_ROOTS),
            fixture["allowed_private_output_roots"],
        )
        self.assertEqual(
            list(ALLOWED_ENVELOPE_FIELDS),
            fixture["allowed_top_level_envelope_fields"],
        )
        self.assertEqual(
            list(ALLOWED_FUTURE_SUMMARY_FIELDS),
            fixture["allowed_future_summary_fields"],
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

    def test_rejects_changed_inspection_depth_or_extra_envelope_fields(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field, value in (
            ("inspection_depth", "nested_record_sampling"),
            (
                "allowed_top_level_envelope_fields",
                [*fixture["allowed_top_level_envelope_fields"], "private_details"],
            ),
        ):
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = value
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
            "nested traversal approved",
            "source text emission approved",
            "real db import approved",
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

    def test_requires_workspace_ignore(self) -> None:
        self.assertIn("workspace/", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_docs_link_contract_fixture_and_checker(self) -> None:
        refs = (
            "docs/m2-explicit-local-import-schema-compatibility-contract.md",
            "tests/fixtures/m2_explicit_local_import_schema_compatibility_scope.synthetic.json",
            "scripts/check_m2_explicit_local_import_schema_compatibility_contract.py",
        )
        for path in (DOC_PATH, ADAPTER_DOC_PATH, ADR_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn(
            "scripts/check_m2_explicit_local_import_schema_compatibility_contract.py",
            text,
        )


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-explicit-local-import-schema-compatibility-scope.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m2_explicit_local_import_schema_compatibility_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
