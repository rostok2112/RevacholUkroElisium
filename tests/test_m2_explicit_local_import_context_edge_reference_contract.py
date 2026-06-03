from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_explicit_local_import_context_edge_reference_contract import (
    ADR_PATH,
    ALLOWED_FUTURE_SUMMARY_FIELDS,
    ALLOWED_PRIVATE_INPUT_ROOTS,
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    CONTEXT_EDGE_SHAPE_DOC_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    FUTURE_PROFILE_SCHEMA_VERSION,
    FUTURE_REFERENCE_FIELDS,
    INCOMPLETE_M2_FIELDS,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    REFERENCE_VALIDATION_STATUS,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_explicit_local_import_context_edge_reference_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2ExplicitLocalImportContextEdgeReferenceContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual(
            [], collect_m2_explicit_local_import_context_edge_reference_contract_errors()
        )

    def test_fixture_keeps_contract_static_and_m2_incomplete(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual(
            "m2-explicit-local-import-context-edge-reference-scope.v1",
            fixture["schema_version"],
        )
        self.assertEqual("M2", fixture["roadmap_milestone"])
        self.assertEqual("contract_only", fixture["scope_status"])
        self.assertEqual(FUTURE_PROFILE_SCHEMA_VERSION, fixture["future_profile_schema_version"])
        self.assertEqual(
            "context_edge_reference_membership_contract_only",
            fixture["inspection_depth"],
        )
        self.assertEqual(
            REFERENCE_VALIDATION_STATUS,
            fixture["context_edge_reference_validation_allowed_next"],
        )
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(list(ALLOWED_PRIVATE_INPUT_ROOTS), fixture["allowed_private_input_roots"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_OUTPUT_ROOTS),
            fixture["allowed_private_output_roots"],
        )
        self.assertEqual(list(FUTURE_REFERENCE_FIELDS), fixture["future_reference_fields"])
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

    def test_rejects_changed_next_step_and_implementation_enabled(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field, value in (
            ("recommended_next_step", "m2_explicit_local_import_context_edge_reference_validator"),
            ("required_next_step", "m2_explicit_local_import_context_edge_reference_validator"),
            ("implementation_allowed_next", True),
            ("context_edge_reference_validation_allowed_next", True),
        ):
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated[field] = value
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_completed_m2_criteria_and_forbidden_permissions(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in (*INCOMPLETE_M2_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
                mutated[field] = True
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_reference_field_or_summary_drift(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutations = (
            ("inspection_depth", "context_edge_reference_validation_implementation"),
            ("future_reference_fields", [*fixture["future_reference_fields"], "edge_payload"]),
            ("future_reference_fields", fixture["future_reference_fields"][:-1]),
            (
                "allowed_future_summary_fields",
                [*fixture["allowed_future_summary_fields"], "record_id_values"],
            ),
        )
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                mutated = copy.deepcopy(fixture)
                mutated[field] = value
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_self_edge_duplicate_edge_and_graph_permissions(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in (
            "self_edge_check_allowed",
            "duplicate_edge_check_allowed",
            "context_graph_construction_allowed_next",
            "retrieval_bucket_mapping_allowed",
        ):
            with self.subTest(field=field):
                mutated = copy.deepcopy(fixture)
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
                mutated = copy.deepcopy(fixture)
                mutated["allowed_private_output_roots"] = [root]
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "reference validation approved",
            "edge id emission approved",
            "record id logging approved",
            "self edge check approved",
            "duplicate edge check approved",
            "graph construction approved",
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
                mutated = copy.deepcopy(fixture)
                mutated["unsafe_note"] = marker
                self.assertNotEqual([], _errors_for(mutated))

    def test_requires_workspace_ignore(self) -> None:
        self.assertIn("workspace/", (ROOT / ".gitignore").read_text(encoding="utf-8"))

    def test_docs_link_contract_fixture_and_checker(self) -> None:
        refs = (
            "docs/m2-explicit-local-import-context-edge-reference-contract.md",
            "tests/fixtures/m2_explicit_local_import_context_edge_reference_scope.synthetic.json",
            "scripts/check_m2_explicit_local_import_context_edge_reference_contract.py",
        )
        for path in (
            DOC_PATH,
            CONTEXT_EDGE_SHAPE_DOC_PATH,
            ADR_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn(
            "scripts/check_m2_explicit_local_import_context_edge_reference_contract.py",
            text,
        )


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-explicit-local-import-context-edge-reference-scope.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m2_explicit_local_import_context_edge_reference_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
