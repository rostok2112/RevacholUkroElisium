from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m2_local_import import (
    DECISION_FIXTURE_PATH,
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    SUMMARY_ROOT,
    M2LocalImportReviewError,
    build_review,
    collect_decision_fixture_errors,
    resolve_review_output_path,
    resolve_summary_input_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.run_m2_local_import import PRIVATE_INPUT_ROOT, run_m2_local_import, write_summary
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKER = "PRIVATE_LOCAL_IMPORT_REVIEW_VALUE_SHOULD_NOT_LEAK"


class M2LocalImportReviewTests(unittest.TestCase):
    def test_ready_review_reads_summary_only(self) -> None:
        with _fake_repo() as root:
            summary_path, private_file, db_path = _write_ready_summary(root)
            private_file.unlink()
            db_path.unlink()

            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["summary_valid"])
            self.assertTrue(review["ready_for_line_index_implementation"])
            self.assertTrue(review["line_index_construction_allowed_next"])
            self.assertFalse(review["context_graph_construction_allowed_next"])
            self.assertFalse(review["retrieval_bucket_mapping_allowed_next"])
            self.assertTrue(review["original_m2_import_done"])
            self.assertFalse(review["original_m2_line_index_done"])
            self.assertEqual("m2_line_index_implementation", review["recommended_next_step"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn(str(root), rendered)

    def test_blocked_summary_recommends_repeat_import(self) -> None:
        with _fake_repo() as root:
            path = root / SUMMARY_ROOT / "blocked.json"
            path.parent.mkdir(parents=True)
            summary = _ready_summary()
            summary["import_status"] = "incompatible"
            summary["private_db_output_written"] = False
            summary["blocker_categories"] = ["record_shape_precondition_failed"]
            write_summary(summary, path)

            review = build_review(load_json(path), summary_path=path, root=root)

            self.assertTrue(review["summary_valid"])
            self.assertFalse(review["ready_for_line_index_implementation"])
            self.assertFalse(review["line_index_construction_allowed_next"])
            self.assertIn("record_shape_precondition_failed", review["blockers"])
            self.assertEqual(
                "repeat_m2_local_import_implementation", review["recommended_next_step"]
            )

    def test_malformed_summary_is_rejected(self) -> None:
        with _fake_repo() as root:
            path = root / SUMMARY_ROOT / "bad.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")

            review = build_review(load_json(path), summary_path=path, root=root)

            self.assertFalse(review["summary_valid"])
            self.assertFalse(review["ready_for_line_index_implementation"])
            self.assertIn("malformed_summary", review["blockers"])

    def test_rejects_unsafe_paths(self) -> None:
        with _fake_repo() as root:
            summary_path, _private_file, _db_path = _write_ready_summary(root)
            self.assertEqual(summary_path, resolve_summary_input_path(summary_path, root=root))
            self.assertEqual(
                (root / REVIEW_OUTPUT_ROOT / "review.json").resolve(strict=False),
                resolve_review_output_path(root / REVIEW_OUTPUT_ROOT / "review.json", root=root),
            )
            for path in (
                root / "docs/summary.json",
                root / SUMMARY_ROOT / "../summary.json",
                root / SUMMARY_ROOT / "raw-log-summary.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M2LocalImportReviewError):
                        resolve_summary_input_path(path, root=root)
            for path in (
                root / "docs/review.json",
                root / REVIEW_OUTPUT_ROOT / "../review.json",
                root / REVIEW_OUTPUT_ROOT / "payload-dump-review.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M2LocalImportReviewError):
                        resolve_review_output_path(path, root=root)

    def test_rejects_unsafe_markers_and_true_safety_flags(self) -> None:
        with _fake_repo() as root:
            path = root / SUMMARY_ROOT / "unsafe.json"
            path.parent.mkdir(parents=True)
            summary = _ready_summary()
            summary["unsafe"] = "raw payload dump"
            write_summary(summary, path)
            review = build_review(load_json(path), summary_path=path, root=root)
            self.assertFalse(review["summary_valid"])
            self.assertIn("unsafe_marker_detected", review["blockers"])

            flagged = _ready_summary()
            flagged["context_graph_constructed"] = True
            flag_path = root / SUMMARY_ROOT / "flagged.json"
            write_summary(flagged, flag_path)
            flagged_review = build_review(load_json(flag_path), summary_path=flag_path, root=root)
            self.assertFalse(flagged_review["summary_valid"])
            self.assertIn("invalid_local_import_summary", flagged_review["blockers"])

    def test_writes_redacted_json_and_markdown(self) -> None:
        with _fake_repo() as root:
            summary_path, _private_file, _db_path = _write_ready_summary(root)
            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            json_path = root / REVIEW_OUTPUT_ROOT / "review.json"
            md_path = root / REVIEW_OUTPUT_ROOT / "review.md"

            write_json_review(review, resolve_review_output_path(json_path, root=root))
            write_markdown_review(review, resolve_review_output_path(md_path, root=root))
            written = json_path.read_text(encoding="utf-8") + md_path.read_text(encoding="utf-8")

            self.assertNotIn(PRIVATE_MARKER, written)
            self.assertNotIn(str(root), written)
            self.assertIn("ready_for_line_index_implementation", written)

    def test_decision_fixture_and_self_test(self) -> None:
        self.assertEqual([], collect_decision_fixture_errors())
        fixture = load_json(DECISION_FIXTURE_PATH)
        self.assertEqual("m2-local-import-review-decision.v1", fixture["schema_version"])
        self.assertEqual("review_required", fixture["line_index_implementation_allowed_next"])
        self.assertFalse(fixture["private_db_reopen_allowed_during_review"])
        self.assertFalse(fixture["context_graph_construction_allowed_next"])

        run_self_test()
        completed = subprocess.run(
            [sys.executable, "scripts/review_m2_local_import.py", "--self-test", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn(PRIVATE_MARKER, completed.stdout)

    def test_check_all_registers_review_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/review_m2_local_import.py", text)
        self.assertIn("--self-test", text)


def _ready_summary() -> dict[str, object]:
    return {
        "schema_version": "m2-local-import-summary.v1",
        "input_exists": True,
        "input_kind": "file",
        "json_object_decoded": True,
        "profile_schema_version_matches": True,
        "records_count": 2,
        "context_edges_count": 1,
        "import_status": "imported",
        "blocker_categories": [],
        "private_db_output_written": True,
        "private_db_schema_version": "m2-local-import-db.v1",
        "m2_import_locally_extracted_db_implemented": True,
        "m2_import_locally_extracted_db_done": True,
        "self_edge_count": 0,
        "duplicate_edge_count": 0,
        "ready_for_line_index_contract": True,
        "private_paths_included": False,
        "filenames_included": False,
        "record_values_in_stdout": False,
        "edge_values_in_stdout": False,
        "metadata_values_in_stdout": False,
        "source_text_in_stdout": False,
        "hashes_computed": False,
        "content_hashing_used": False,
        "path_string_hashing_used": False,
        "filename_hashing_used": False,
        "line_index_constructed": False,
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
        "automatic_game_install_scanning": False,
        "recursive_discovery_used": False,
        "game_files_read": False,
        "bepinex_logs_read": False,
        "screenshots_read": False,
        "ocr_used": False,
        "save_files_read": False,
        "current_line_capture_used": False,
        "ui_text_reading_used": False,
        "unity_scanning_used": False,
        "hooks_used": False,
        "decompiled_code_used": False,
        "provider_called": False,
        "companion_contract_changed": False,
        "raw_payloads_included": False,
        "raw_logs_included": False,
        "runtime_evidence_included": False,
    }


def _write_ready_summary(root: Path) -> tuple[Path, Path, Path]:
    private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
    private_file.parent.mkdir(parents=True)
    private_file.write_text(json.dumps(_compatible_payload()), encoding="utf-8")
    db_path = root / "workspace/local-private/extraction-indexing/import/db/imported-db.json"
    summary = run_m2_local_import(
        Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
        Path("workspace/local-private/extraction-indexing/import/db/imported-db.json"),
        root=root,
    )
    summary_path = root / SUMMARY_ROOT / "summary.json"
    write_summary(summary, summary_path)
    return summary_path, private_file, db_path


def _compatible_payload() -> dict[str, object]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            _compatible_record(f"{PRIVATE_MARKER}_A"),
            _compatible_record(f"{PRIVATE_MARKER}_B"),
        ],
        "context_edges": [
            {
                "from_record_id": f"{PRIVATE_MARKER}_A",
                "to_record_id": f"{PRIVATE_MARKER}_B",
                "relation": "previous_visible",
            }
        ],
        "metadata": {"nested_marker": PRIVATE_MARKER},
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
        "redacted_metadata": {"nested_marker": PRIVATE_MARKER},
    }


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
