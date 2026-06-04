from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_context_graph_contract import (
    ADR_PATH,
    ALLOWED_NEXT_GRAPH_INPUTS,
    ALLOWED_PRIVATE_EDGE_FIELDS,
    ALLOWED_PRIVATE_GRAPH_FIELDS,
    ALLOWED_PRIVATE_INPUT_ROOTS,
    ALLOWED_PRIVATE_NODE_FIELDS,
    ALLOWED_PRIVATE_OUTPUT_ROOTS,
    ALLOWED_PUBLIC_SUMMARY_FIELDS,
    ALLOWED_RELATION_TO_BUCKET_MAPPINGS,
    CONTEXT_GRAPH_SCHEMA_VERSION,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_FALSE_FIELDS,
    LINE_INDEX_DOC_PATH,
    LINE_INDEX_SCHEMA_VERSION,
    NEXT_ACTIONS_PATH,
    PRIVATE_DB_SCHEMA_VERSION,
    RECOMMENDED_NEXT_STEP,
    REQUIRED_TRUE_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_context_graph_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2ContextGraphContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m2_context_graph_contract_errors())

    def test_fixture_approves_only_next_context_graph_implementation(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("m2-context-graph-scope.v1", fixture["schema_version"])
        self.assertEqual("M2", fixture["roadmap_milestone"])
        self.assertEqual("context_graph_contract", fixture["scope_status"])
        self.assertEqual(PRIVATE_DB_SCHEMA_VERSION, fixture["future_private_db_schema_version"])
        self.assertEqual(LINE_INDEX_SCHEMA_VERSION, fixture["future_line_index_schema_version"])
        self.assertEqual(
            CONTEXT_GRAPH_SCHEMA_VERSION, fixture["future_context_graph_schema_version"]
        )
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["required_next_step"])
        self.assertEqual(
            "line_index_review_required",
            fixture["context_graph_implementation_allowed_next"],
        )
        self.assertTrue(fixture["line_index_review_required"])
        self.assertEqual(list(ALLOWED_PRIVATE_INPUT_ROOTS), fixture["allowed_private_input_roots"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_OUTPUT_ROOTS), fixture["allowed_private_output_roots"]
        )
        self.assertEqual(list(ALLOWED_NEXT_GRAPH_INPUTS), fixture["allowed_next_graph_inputs"])
        self.assertEqual(
            list(ALLOWED_PRIVATE_GRAPH_FIELDS), fixture["allowed_private_graph_fields"]
        )
        self.assertEqual(list(ALLOWED_PRIVATE_NODE_FIELDS), fixture["allowed_private_node_fields"])
        self.assertEqual(list(ALLOWED_PRIVATE_EDGE_FIELDS), fixture["allowed_private_edge_fields"])
        self.assertEqual(
            list(ALLOWED_RELATION_TO_BUCKET_MAPPINGS),
            fixture["allowed_relation_to_bucket_mappings"],
        )
        self.assertEqual("none", fixture["default_spoiler_budget"])
        self.assertEqual(
            "context_graph_relation_mapping_only",
            fixture["retrieval_bucket_mapping_allowed_next"],
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
            {"recommended_next_step": "m3_bepinex_bridge"},
            {"required_next_step": "m2_context_graph_implementation"},
            {"context_graph_implementation_allowed_next": True},
            {"future_private_db_schema_version": "m2-local-private-export.v1"},
            {"future_line_index_schema_version": "m2-synthetic-line-index.v1"},
            {"future_context_graph_schema_version": "m2-synthetic-context-graph.v1"},
            {"default_spoiler_budget": "all"},
            {"retrieval_bucket_mapping_allowed_next": True},
            {"allowed_next_graph_inputs": ["source_text"]},
            {"allowed_private_graph_fields": ["source_text"]},
            {"allowed_private_node_fields": ["source_text"]},
            {"allowed_private_edge_fields": ["raw_relation"]},
            {"allowed_relation_to_bucket_mappings": ["player_option:any_future_branch"]},
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
            "../workspace/local-private/extraction-indexing/import/context-graph/",
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
            "game file reads approved",
            "arbitrary future branch traversal approved",
            "directory input approved",
            "current-line capture approved",
            "commit context graph approved",
            "commit extracted text approved",
            "source text duplication approved",
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
            "docs/m2-context-graph-contract.md",
            "tests/fixtures/m2_context_graph_scope.synthetic.json",
            "scripts/check_m2_context_graph_contract.py",
            "scripts/review_m2_line_index.py",
            "tests/fixtures/m2_line_index_review_decision.synthetic.json",
        )
        for path in (
            DOC_PATH,
            ADR_PATH,
            LINE_INDEX_DOC_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_check_all_registers_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m2_context_graph_contract.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-context-graph-scope.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m2_context_graph_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
