from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m2_synthetic_context_graph_contract import (
    ADR_PATH,
    DOC_PATH,
    FIXTURE_PATH,
    IMPORT_DOC_PATH,
    LINE_INDEX_DOC_PATH,
    NEXT_ACTIONS_PATH,
    RELATION_TO_BUCKET,
    SAFETY_FLAG_FIELDS,
    SESSION_SUMMARY_PATH,
    collect_m2_synthetic_context_graph_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2SyntheticContextGraphContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_m2_synthetic_context_graph_contract_errors())

    def test_rejects_missing_duplicate_or_extra_nodes(self) -> None:
        for transform in (_remove_node, _duplicate_node, _add_extra_node):
            with self.subTest(transform=transform.__name__):
                fixture = _fixture_copy()
                transform(fixture)
                self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_broken_self_duplicate_or_extra_edges(self) -> None:
        for transform in (_break_edge, _self_edge, _duplicate_edge, _add_extra_edge):
            with self.subTest(transform=transform.__name__):
                fixture = _fixture_copy()
                transform(fixture)
                self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_unknown_relation_or_wrong_bucket(self) -> None:
        fixture = _fixture_copy()
        fixture["edges"][0]["relation"] = "future_spoiler"
        self.assertNotEqual([], _errors_for(fixture))

        fixture = _fixture_copy()
        fixture["edges"][0]["retrieval_bucket"] = "visible_history"
        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_unstable_node_or_edge_order(self) -> None:
        fixture = _fixture_copy()
        fixture["nodes"][0], fixture["nodes"][1] = fixture["nodes"][1], fixture["nodes"][0]
        self.assertNotEqual([], _errors_for(fixture))

        fixture = _fixture_copy()
        fixture["edges"][0], fixture["edges"][1] = fixture["edges"][1], fixture["edges"][0]
        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_non_none_spoiler_budget(self) -> None:
        fixture = _fixture_copy()
        fixture["default_spoiler_budget"] = "full_game"

        self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_source_text_and_unsafe_markers(self) -> None:
        fixture = _fixture_copy()
        fixture["nodes"][0]["source_text"] = "invented but forbidden"
        self.assertNotEqual([], _errors_for(fixture))

        for marker in (
            "raw payload dump",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "C:\\Users\\local\\secret",
            "screenshot archive",
            "savegame.sav",
            "decompiled output",
            "future branch traversal approved",
        ):
            with self.subTest(marker=marker):
                fixture = _fixture_copy()
                fixture["nodes"][0]["context_placeholder"] = marker
                self.assertNotEqual([], _errors_for(fixture))

    def test_rejects_dangerous_safety_flags(self) -> None:
        for field in SAFETY_FLAG_FIELDS:
            with self.subTest(field=field):
                fixture = _fixture_copy()
                fixture["safety_flags"][field] = True
                self.assertNotEqual([], _errors_for(fixture))

    def test_relation_buckets_match_existing_retrieval_semantics(self) -> None:
        self.assertEqual(
            {
                "previous_visible": "visible_history",
                "nearby_branch": "nearby_tree",
                "player_option": "player_options",
            },
            RELATION_TO_BUCKET,
        )

    def test_docs_link_contract_fixture_schema_and_checker(self) -> None:
        refs = (
            "docs/m2-synthetic-context-graph-contract.md",
            "specs/m2-synthetic-context-graph.schema.json",
            "tests/fixtures/m2_synthetic_context_graph.synthetic.json",
            "scripts/check_m2_synthetic_context_graph_contract.py",
        )
        for path in (
            DOC_PATH,
            ADR_PATH,
            IMPORT_DOC_PATH,
            LINE_INDEX_DOC_PATH,
            SESSION_SUMMARY_PATH,
            NEXT_ACTIONS_PATH,
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                for ref in refs:
                    self.assertIn(ref, text)

    def test_schema_and_check_all_register_contract(self) -> None:
        schema_validation = (ROOT / "scripts/validate_schemas.py").read_text(encoding="utf-8")
        check_all = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("m2-synthetic-context-graph.schema.json", schema_validation)
        self.assertIn("m2_synthetic_context_graph.synthetic.json", schema_validation)
        self.assertIn("scripts/check_m2_synthetic_context_graph_contract.py", check_all)


def _fixture_copy() -> dict[str, object]:
    return copy.deepcopy(load_json(FIXTURE_PATH))


def _remove_node(fixture: dict[str, object]) -> None:
    fixture["nodes"].pop()
    fixture["node_count"] -= 1


def _duplicate_node(fixture: dict[str, object]) -> None:
    fixture["nodes"].append(copy.deepcopy(fixture["nodes"][0]))
    fixture["node_count"] += 1


def _add_extra_node(fixture: dict[str, object]) -> None:
    extra = copy.deepcopy(fixture["nodes"][0])
    extra["line_id"] = "synthetic.m2.line.999"
    extra["record_id"] = "synthetic.m2.line.999"
    fixture["nodes"].append(extra)
    fixture["node_count"] += 1


def _break_edge(fixture: dict[str, object]) -> None:
    fixture["edges"][0]["to_line_id"] = "synthetic.m2.line.999"


def _self_edge(fixture: dict[str, object]) -> None:
    fixture["edges"][0]["to_line_id"] = fixture["edges"][0]["from_line_id"]


def _duplicate_edge(fixture: dict[str, object]) -> None:
    fixture["edges"].append(copy.deepcopy(fixture["edges"][0]))
    fixture["edge_count"] += 1


def _add_extra_edge(fixture: dict[str, object]) -> None:
    fixture["edges"].append(
        {
            "from_line_id": "synthetic.m2.line.003",
            "to_line_id": "synthetic.m2.line.001",
            "relation": "nearby_branch",
            "retrieval_bucket": "nearby_tree",
        }
    )
    fixture["edge_count"] += 1


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "m2-synthetic-context-graph.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_m2_synthetic_context_graph_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
