from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m2_explicit_local_import_context_edge_reference_dry_run import (
    DECISION_FALSE_FIELDS,
    DECISION_FIXTURE_PATH,
    DECISION_SCHEMA_VERSION,
    RECOMMENDED_CONTEXT_EDGE_INTEGRITY_CONTRACT_STEP,
    RECOMMENDED_REPEAT_DRY_RUN_STEP,
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    collect_decision_fixture_errors,
    collect_summary_errors,
    resolve_review_output_path,
    resolve_summary_input_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
    build_review,
    M2ExplicitLocalImportContextEdgeReferenceDryRunReviewError,
)
from scripts.run_m2_explicit_local_import_context_edge_reference_dry_run import (
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    build_m2_explicit_local_import_context_edge_reference_dry_run,
    write_summary,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKER = "PRIVATE_CONTEXT_EDGE_REFERENCE_REVIEW_VALUE_SHOULD_NOT_LEAK"


class M2ExplicitLocalImportContextEdgeReferenceDryRunReviewTests(unittest.TestCase):
    def test_ready_review_is_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_summary_from_payload(root, _compatible_payload())

            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["summary_valid"])
            self.assertTrue(review["ready_for_context_edge_integrity_contract_decision"])
            self.assertEqual(
                RECOMMENDED_CONTEXT_EDGE_INTEGRITY_CONTRACT_STEP,
                review["recommended_next_step"],
            )
            self.assertFalse(review["self_edge_check_allowed_next"])
            self.assertFalse(review["duplicate_edge_check_allowed_next"])
            self.assertFalse(review["retrieval_bucket_mapping_allowed_next"])
            self.assertFalse(review["original_m2_import_done"])
            self.assertFalse(review["original_m2_line_index_done"])
            self.assertFalse(review["original_m2_context_graph_done"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn("private.record", rendered)
            self.assertNotIn(str(root), rendered)

    def test_incompatible_and_decode_failed_are_structurally_reviewable_but_blocked(self) -> None:
        with _fake_repo() as root:
            unresolved = _compatible_payload()
            unresolved["context_edges"] = [
                {
                    "from_record_id": "private.record.a",
                    "to_record_id": "UNKNOWN_PRIVATE_ID_SHOULD_NOT_LEAK",
                    "relation": "previous_visible",
                }
            ]
            unresolved_path = _write_summary_from_payload(root, unresolved)
            unresolved_review = build_review(
                load_json(unresolved_path),
                summary_path=unresolved_path,
                root=root,
            )

            self.assertTrue(unresolved_review["summary_valid"])
            self.assertFalse(
                unresolved_review["ready_for_context_edge_integrity_contract_decision"]
            )
            self.assertEqual(
                RECOMMENDED_REPEAT_DRY_RUN_STEP, unresolved_review["recommended_next_step"]
            )
            self.assertIn("context_edge_reference_unresolved", unresolved_review["blockers"])

            malformed_summary = _base_summary()
            malformed_summary["context_edge_reference_status"] = "decode_failed"
            malformed_summary["blocker_categories"] = ["json_decode_failed"]
            malformed_path = _write_summary(root, "decode-failed.json", malformed_summary)
            malformed_review = build_review(
                load_json(malformed_path),
                summary_path=malformed_path,
                root=root,
            )

            self.assertTrue(malformed_review["summary_valid"])
            self.assertFalse(malformed_review["ready_for_context_edge_integrity_contract_decision"])
            self.assertEqual("decode_failed", malformed_review["context_edge_reference_status"])
            self.assertIn("json_decode_failed", malformed_review["blockers"])

    def test_malformed_summary_and_count_inconsistencies_are_rejected(self) -> None:
        with _fake_repo() as root:
            good = _base_summary()
            good_path = _write_summary(root, "good.json", good)
            self.assertEqual([], collect_summary_errors(good, summary_path=good_path, root=root))

            for mutation in (
                {"schema_version": "wrong"},
                {"context_edges_references_checked_count": 99},
                {"context_edges_with_resolved_from_count": 99},
                {"context_edges_with_unresolved_reference_count": 99},
                {"all_context_edge_references_resolved": False},
                {"record_id_set_built": False},
                {"context_edge_reference_status": "unknown"},
            ):
                with self.subTest(mutation=mutation):
                    bad = copy.deepcopy(good)
                    bad.update(mutation)
                    bad_path = _write_summary(root, "bad.json", bad)
                    self.assertNotEqual(
                        [],
                        collect_summary_errors(bad, summary_path=bad_path, root=root),
                    )

    def test_unsafe_paths_are_rejected(self) -> None:
        with _fake_repo() as root:
            valid_path = _write_summary_from_payload(root, _compatible_payload())
            self.assertEqual(valid_path, resolve_summary_input_path(valid_path, root=root))
            for path in (
                Path("docs/summary.json"),
                Path("workspace/local-private/extraction-indexing/import/summary.json"),
                Path(PRIVATE_OUTPUT_ROOT) / "../summary.json",
                Path(PRIVATE_OUTPUT_ROOT) / "raw-log-summary.json",
            ):
                with self.subTest(summary_path=path):
                    with self.assertRaises(
                        M2ExplicitLocalImportContextEdgeReferenceDryRunReviewError
                    ):
                        resolve_summary_input_path(path, root=root)

            valid_output = resolve_review_output_path(
                Path(REVIEW_OUTPUT_ROOT) / "review.json",
                root=root,
            )
            self.assertEqual(
                ("context-edge-reference-review", "review.json"), valid_output.parts[-2:]
            )
            for path in (
                Path("docs/review.json"),
                Path(
                    "workspace/local-private/extraction-indexing/import/context-edge-reference/review.json"
                ),
                Path(REVIEW_OUTPUT_ROOT) / "../review.json",
                Path(REVIEW_OUTPUT_ROOT) / "LogOutput.log.json",
            ):
                with self.subTest(output_path=path):
                    with self.assertRaises(
                        M2ExplicitLocalImportContextEdgeReferenceDryRunReviewError
                    ):
                        resolve_review_output_path(path, root=root)

    def test_unsafe_markers_and_true_safety_flags_are_rejected(self) -> None:
        with _fake_repo() as root:
            summary = _base_summary()
            for marker in (
                "raw payload dump",
                "LogOutput.log",
                "api_key=secret",
                "https://example.invalid",
                "C:\\Users\\local\\secret",
                "record id emission approved",
                "self edge check approved",
                "retrieval bucket mapping approved",
                "source text emission approved",
            ):
                with self.subTest(marker=marker):
                    mutated = copy.deepcopy(summary)
                    mutated["blocker_categories"] = [marker]
                    path = _write_summary(root, "marker.json", mutated)
                    self.assertNotEqual(
                        [],
                        collect_summary_errors(mutated, summary_path=path, root=root),
                    )

            for field in (
                "record_ids_included",
                "edge_ids_included",
                "relation_values_included",
                "self_edge_check_used",
                "duplicate_edge_check_used",
                "retrieval_bucket_mapping_used",
                "context_graph_constructed",
            ):
                with self.subTest(field=field):
                    mutated = copy.deepcopy(summary)
                    mutated[field] = True
                    path = _write_summary(root, "flag.json", mutated)
                    self.assertNotEqual(
                        [],
                        collect_summary_errors(mutated, summary_path=path, root=root),
                    )

    def test_json_and_markdown_outputs_are_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_summary_from_payload(root, _compatible_payload())
            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            json_path = resolve_review_output_path(
                Path(REVIEW_OUTPUT_ROOT) / "review.json", root=root
            )
            md_path = resolve_review_output_path(Path(REVIEW_OUTPUT_ROOT) / "review.md", root=root)

            write_json_review(review, json_path)
            write_markdown_review(review, md_path)
            written = json_path.read_text(encoding="utf-8") + md_path.read_text(encoding="utf-8")

            self.assertNotIn(PRIVATE_MARKER, written)
            self.assertNotIn("private.record", written)
            self.assertNotIn(str(root), written)
            self.assertIn("ready_for_context_edge_integrity_contract_decision", written)

    def test_decision_fixture_safety(self) -> None:
        self.assertEqual([], collect_decision_fixture_errors())
        fixture = load_json(DECISION_FIXTURE_PATH)

        self.assertEqual(DECISION_SCHEMA_VERSION, fixture["schema_version"])
        self.assertEqual("M2", fixture["roadmap_milestone"])
        self.assertIs(fixture["context_edge_reference_review_evidence_required"], True)
        self.assertEqual(
            "decision_pending",
            fixture["context_edge_integrity_contract_allowed_next"],
        )
        self.assertEqual(
            RECOMMENDED_CONTEXT_EDGE_INTEGRITY_CONTRACT_STEP,
            fixture["recommended_next_step"],
        )
        for field in DECISION_FALSE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_self_test_and_quiet_cli_delete_export_before_review(self) -> None:
        run_self_test()
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_context_edge_reference_dry_run.py",
                "--self-test",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn(PRIVATE_MARKER, completed.stdout)

    def test_check_all_registers_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn(
            "scripts/review_m2_explicit_local_import_context_edge_reference_dry_run.py",
            text,
        )
        self.assertIn("--self-test", text)


def _compatible_payload() -> dict[str, object]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            _compatible_record("private.record.a"),
            _compatible_record("private.record.b"),
        ],
        "context_edges": [
            {
                "from_record_id": "private.record.a",
                "to_record_id": "private.record.b",
                "relation": "previous_visible",
            },
            {
                "from_record_id": "private.record.a",
                "to_record_id": "private.record.a",
                "relation": "nearby_branch",
            },
        ],
        "metadata": {"nested": PRIVATE_MARKER},
    }


def _compatible_record(record_id: str) -> dict[str, object]:
    return {
        "record_id": record_id,
        "line_id": PRIVATE_MARKER,
        "conversation_id": PRIVATE_MARKER,
        "speaker_id": PRIVATE_MARKER,
        "speaker_label": PRIVATE_MARKER,
        "context_placeholder": PRIVATE_MARKER,
        "source_text": PRIVATE_MARKER,
        "context_tags": [PRIVATE_MARKER],
        "redacted_metadata": {"nested": PRIVATE_MARKER},
    }


def _base_summary() -> dict[str, object]:
    summary = build_m2_explicit_local_import_context_edge_reference_dry_run(
        Path(PRIVATE_INPUT_ROOT) / "dummy.json",
        root=Path("unused"),
    )
    summary.update(
        {
            "input_exists": True,
            "input_kind": "file",
            "envelope_compatible": True,
            "records_shape_reviewed": True,
            "context_edges_shape_reviewed": True,
            "record_id_set_built": True,
            "context_edges_count": 1,
            "context_edges_references_checked_count": 1,
            "context_edges_with_resolved_from_count": 1,
            "context_edges_with_resolved_to_count": 1,
            "context_edges_with_unresolved_reference_count": 0,
            "all_context_edge_references_resolved": True,
            "context_edge_reference_status": "compatible",
            "blocker_categories": [],
        }
    )
    return summary


def _write_private_json(root: Path, name: str, payload: object) -> Path:
    path = root / PRIVATE_INPUT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_summary_from_payload(root: Path, payload: object) -> Path:
    private_file = _write_private_json(root, "selected-export.json", payload)
    summary = build_m2_explicit_local_import_context_edge_reference_dry_run(
        private_file.relative_to(root),
        root=root,
    )
    summary_path = root / PRIVATE_OUTPUT_ROOT / "summary.json"
    write_summary(summary, summary_path)
    private_file.unlink()
    return summary_path


def _write_summary(root: Path, name: str, summary: object) -> Path:
    path = root / PRIVATE_OUTPUT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary), encoding="utf-8")
    return path


class _fake_repo:
    def __enter__(self) -> Path:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "fake-repo"
        self.root.mkdir()
        return self.root

    def __exit__(self, *_exc: object) -> None:
        self._tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
