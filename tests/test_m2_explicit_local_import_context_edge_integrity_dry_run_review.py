from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m2_explicit_local_import_context_edge_integrity_dry_run import (
    DECISION_FALSE_FIELDS,
    DECISION_FIXTURE_PATH,
    DECISION_SCHEMA_VERSION,
    RECOMMENDED_LOCAL_IMPORT_FINAL_APPROVAL_CONTRACT_STEP,
    RECOMMENDED_REPEAT_DRY_RUN_STEP,
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_summary_errors,
    resolve_review_output_path,
    resolve_summary_input_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.run_m2_explicit_local_import_context_edge_integrity_dry_run import (
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    build_m2_explicit_local_import_context_edge_integrity_dry_run,
    write_summary,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKER = "PRIVATE_CONTEXT_EDGE_INTEGRITY_REVIEW_VALUE_SHOULD_NOT_LEAK"
PRIVATE_RECORD_A = "private.integrity.review.record.a"
PRIVATE_RECORD_B = "private.integrity.review.record.b"


class M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewTests(unittest.TestCase):
    def test_ready_review_is_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_summary_from_payload(root, _compatible_payload())

            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["summary_valid"])
            self.assertTrue(review["ready_for_local_import_final_approval_contract_decision"])
            self.assertEqual(
                RECOMMENDED_LOCAL_IMPORT_FINAL_APPROVAL_CONTRACT_STEP,
                review["recommended_next_step"],
            )
            self.assertFalse(review["retrieval_bucket_mapping_allowed_next"])
            self.assertFalse(review["real_db_import_allowed_next"])
            self.assertFalse(review["line_index_construction_allowed_next"])
            self.assertFalse(review["context_graph_construction_allowed_next"])
            self.assertFalse(review["original_m2_import_done"])
            self.assertFalse(review["original_m2_line_index_done"])
            self.assertFalse(review["original_m2_context_graph_done"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn(PRIVATE_RECORD_A, rendered)
            self.assertNotIn("previous_visible", rendered)
            self.assertNotIn(str(root), rendered)

    def test_self_edge_and_duplicate_edge_summaries_are_blocked_but_reviewable(self) -> None:
        with _fake_repo() as root:
            self_edge_payload = _compatible_payload()
            self_edge_payload["context_edges"] = [
                {
                    "from_record_id": PRIVATE_RECORD_A,
                    "to_record_id": PRIVATE_RECORD_A,
                    "relation": "previous_visible",
                }
            ]
            self_edge_path = _write_summary_from_payload(root, self_edge_payload)
            self_edge_review = build_review(
                load_json(self_edge_path), summary_path=self_edge_path, root=root
            )

            self.assertTrue(self_edge_review["summary_valid"])
            self.assertFalse(
                self_edge_review["ready_for_local_import_final_approval_contract_decision"]
            )
            self.assertEqual(
                RECOMMENDED_REPEAT_DRY_RUN_STEP, self_edge_review["recommended_next_step"]
            )
            self.assertEqual(1, self_edge_review["self_edge_count"])
            self.assertIn("self_edges_found", self_edge_review["blockers"])

            duplicate_payload = _compatible_payload()
            duplicate = {
                "from_record_id": PRIVATE_RECORD_A,
                "to_record_id": PRIVATE_RECORD_B,
                "relation": "nearby_branch",
            }
            duplicate_payload["context_edges"] = [duplicate, dict(duplicate)]
            duplicate_path = _write_summary_from_payload(root, duplicate_payload)
            duplicate_review = build_review(
                load_json(duplicate_path), summary_path=duplicate_path, root=root
            )

            self.assertTrue(duplicate_review["summary_valid"])
            self.assertFalse(
                duplicate_review["ready_for_local_import_final_approval_contract_decision"]
            )
            self.assertEqual(1, duplicate_review["duplicate_edge_count"])
            self.assertIn("duplicate_edges_found", duplicate_review["blockers"])
            self.assertNotIn(PRIVATE_RECORD_A, json.dumps(duplicate_review, sort_keys=True))

    def test_decode_failed_summary_is_structurally_reviewable_but_blocked(self) -> None:
        with _fake_repo() as root:
            summary = _base_summary()
            summary["context_edge_integrity_status"] = "decode_failed"
            summary["blocker_categories"] = ["json_decode_failed"]
            path = _write_summary(root, "decode-failed.json", summary)

            review = build_review(load_json(path), summary_path=path, root=root)

            self.assertTrue(review["summary_valid"])
            self.assertFalse(review["ready_for_local_import_final_approval_contract_decision"])
            self.assertEqual("decode_failed", review["context_edge_integrity_status"])
            self.assertIn("json_decode_failed", review["blockers"])

    def test_malformed_summary_and_count_inconsistencies_are_rejected(self) -> None:
        with _fake_repo() as root:
            good = _base_summary()
            good_path = _write_summary(root, "good.json", good)
            self.assertEqual([], collect_summary_errors(good, summary_path=good_path, root=root))

            for mutation in (
                {"schema_version": "wrong"},
                {"context_edges_count": -1},
                {"self_edge_count": 3},
                {"duplicate_edge_count": 3},
                {"all_context_edges_integrity_compatible": False},
                {"context_edge_references_reviewed": False},
                {"context_edge_integrity_status": "unknown"},
            ):
                with self.subTest(mutation=mutation):
                    bad = copy.deepcopy(good)
                    bad.update(mutation)
                    path = _write_summary(root, "bad.json", bad)
                    self.assertNotEqual(
                        [], collect_summary_errors(bad, summary_path=path, root=root)
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
                        M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError
                    ):
                        resolve_summary_input_path(path, root=root)

            valid_output = resolve_review_output_path(
                Path(REVIEW_OUTPUT_ROOT) / "review.json", root=root
            )
            self.assertEqual(
                ("context-edge-integrity-review", "review.json"), valid_output.parts[-2:]
            )
            for path in (
                Path("docs/review.json"),
                Path(
                    "workspace/local-private/extraction-indexing/import/context-edge-integrity/review.json"
                ),
                Path(REVIEW_OUTPUT_ROOT) / "../review.json",
                Path(REVIEW_OUTPUT_ROOT) / "LogOutput.log.json",
            ):
                with self.subTest(output_path=path):
                    with self.assertRaises(
                        M2ExplicitLocalImportContextEdgeIntegrityDryRunReviewError
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
                "duplicate tuple emission approved",
                "retrieval bucket mapping approved",
                "source text emission approved",
            ):
                with self.subTest(marker=marker):
                    mutated = copy.deepcopy(summary)
                    mutated["blocker_categories"] = [marker]
                    path = _write_summary(root, "marker.json", mutated)
                    self.assertNotEqual(
                        [], collect_summary_errors(mutated, summary_path=path, root=root)
                    )

            for field in (
                "record_ids_included",
                "edge_ids_included",
                "relation_values_included",
                "duplicate_tuples_included",
                "retrieval_bucket_mapping_used",
                "real_db_imported",
                "line_index_constructed",
                "context_graph_constructed",
            ):
                with self.subTest(field=field):
                    mutated = copy.deepcopy(summary)
                    mutated[field] = True
                    path = _write_summary(root, "flag.json", mutated)
                    self.assertNotEqual(
                        [], collect_summary_errors(mutated, summary_path=path, root=root)
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
            self.assertNotIn(PRIVATE_RECORD_A, written)
            self.assertNotIn("previous_visible", written)
            self.assertNotIn(str(root), written)
            self.assertIn("ready_for_local_import_final_approval_contract_decision", written)

    def test_decision_fixture_safety(self) -> None:
        self.assertEqual([], collect_decision_fixture_errors())
        fixture = load_json(DECISION_FIXTURE_PATH)

        self.assertEqual(DECISION_SCHEMA_VERSION, fixture["schema_version"])
        self.assertEqual("M2", fixture["roadmap_milestone"])
        self.assertIs(fixture["context_edge_integrity_review_evidence_required"], True)
        self.assertEqual(
            "decision_pending",
            fixture["local_import_final_approval_contract_allowed_next"],
        )
        self.assertEqual(
            RECOMMENDED_LOCAL_IMPORT_FINAL_APPROVAL_CONTRACT_STEP,
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
                "scripts/review_m2_explicit_local_import_context_edge_integrity_dry_run.py",
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
            "scripts/review_m2_explicit_local_import_context_edge_integrity_dry_run.py",
            text,
        )
        self.assertIn("--self-test", text)


def _compatible_payload() -> dict[str, object]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            _compatible_record(PRIVATE_RECORD_A),
            _compatible_record(PRIVATE_RECORD_B),
        ],
        "context_edges": [
            {
                "from_record_id": PRIVATE_RECORD_A,
                "to_record_id": PRIVATE_RECORD_B,
                "relation": "previous_visible",
            },
            {
                "from_record_id": PRIVATE_RECORD_B,
                "to_record_id": PRIVATE_RECORD_A,
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
    summary = build_m2_explicit_local_import_context_edge_integrity_dry_run(
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
            "context_edge_references_reviewed": True,
            "context_edges_count": 1,
            "self_edge_count": 0,
            "duplicate_edge_count": 0,
            "all_context_edges_integrity_compatible": True,
            "context_edge_integrity_status": "compatible",
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
    summary = build_m2_explicit_local_import_context_edge_integrity_dry_run(
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
