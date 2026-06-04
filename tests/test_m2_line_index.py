from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m2_local_import import build_review
from scripts.run_m2_line_index import (
    LINE_INDEX_SCHEMA_VERSION,
    LOCAL_IMPORT_REVIEW_ROOT,
    PRIVATE_DB_ROOT,
    PRIVATE_LINE_INDEX_ROOT,
    SUMMARY_SCHEMA_VERSION,
    M2LineIndexError,
    resolve_import_review_input_path,
    resolve_line_index_output_path,
    resolve_private_db_input_path,
    run_m2_line_index,
    run_self_test,
)
from scripts.run_m2_local_import import PRIVATE_INPUT_ROOT, run_m2_local_import, write_summary
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKER = "PRIVATE_LINE_INDEX_VALUE_SHOULD_NOT_LEAK"


class M2LineIndexTests(unittest.TestCase):
    def test_builds_private_line_index_from_private_db_and_review(self) -> None:
        with _fake_repo() as root:
            db_path, review_path = _prepare_private_db_and_review(root)
            output_path = Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json"

            summary = run_m2_line_index(db_path, review_path, output_path, root=root)
            rendered = json.dumps(summary, sort_keys=True)
            line_index = load_json(root / output_path)

            self.assertEqual(SUMMARY_SCHEMA_VERSION, summary["schema_version"])
            self.assertEqual("built", summary["line_index_status"])
            self.assertTrue(summary["private_db_schema_version_matches"])
            self.assertEqual(2, summary["records_count"])
            self.assertEqual(2, summary["line_index_entry_count"])
            self.assertTrue(summary["line_index_output_written"])
            self.assertTrue(summary["m2_line_index_done"])
            self.assertFalse(summary["context_graph_constructed"])
            self.assertFalse(summary["retrieval_bucket_mapping_used"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn(str(root), rendered)

            self.assertEqual(LINE_INDEX_SCHEMA_VERSION, line_index["schema_version"])
            self.assertEqual("m2-local-import-db.v1", line_index["source_schema_version"])
            self.assertEqual(2, len(line_index["entries"]))
            self.assertEqual(
                sorted(entry["line_id"] for entry in line_index["entries"]),
                [entry["line_id"] for entry in line_index["entries"]],
            )
            self.assertIn(PRIVATE_MARKER, json.dumps(line_index, sort_keys=True))
            self.assertFalse(line_index["context_graph_constructed"])
            self.assertFalse(line_index["retrieval_bucket_mapping_used"])

    def test_requires_ready_local_import_review(self) -> None:
        with _fake_repo() as root:
            db_path, review_path = _prepare_private_db_and_review(root)
            review = load_json(root / review_path)
            review["ready_for_line_index_implementation"] = False
            review["line_index_construction_allowed_next"] = False
            (root / review_path).write_text(json.dumps(review), encoding="utf-8")

            summary = run_m2_line_index(
                db_path,
                review_path,
                Path(PRIVATE_LINE_INDEX_ROOT) / "blocked.json",
                root=root,
            )

            self.assertEqual("incompatible", summary["line_index_status"])
            self.assertIn("local_import_review_not_ready", summary["blocker_categories"])
            self.assertFalse(summary["line_index_output_written"])

    def test_rejects_bad_private_db_shape_without_private_leak(self) -> None:
        with _fake_repo() as root:
            db_path, review_path = _prepare_private_db_and_review(root)
            private_db = load_json(root / db_path)
            private_db["schema_version"] = "wrong"
            (root / db_path).write_text(json.dumps(private_db), encoding="utf-8")

            summary = run_m2_line_index(
                db_path,
                review_path,
                Path(PRIVATE_LINE_INDEX_ROOT) / "bad.json",
                root=root,
            )
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual("incompatible", summary["line_index_status"])
            self.assertIn("private_db_schema_version_mismatch", summary["blocker_categories"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertFalse(summary["line_index_output_written"])

    def test_decode_and_non_object_failures_do_not_write_output(self) -> None:
        with _fake_repo() as root:
            _db_path, review_path = _prepare_private_db_and_review(root)
            malformed = root / PRIVATE_DB_ROOT / "malformed.json"
            malformed.write_text("{", encoding="utf-8")
            malformed_summary = run_m2_line_index(
                Path(PRIVATE_DB_ROOT) / "malformed.json",
                review_path,
                Path(PRIVATE_LINE_INDEX_ROOT) / "malformed-index.json",
                root=root,
            )
            self.assertEqual("decode_failed", malformed_summary["line_index_status"])
            self.assertFalse(malformed_summary["line_index_output_written"])

            array_path = root / PRIVATE_DB_ROOT / "array.json"
            array_path.write_text(json.dumps([PRIVATE_MARKER]), encoding="utf-8")
            array_summary = run_m2_line_index(
                Path(PRIVATE_DB_ROOT) / "array.json",
                review_path,
                Path(PRIVATE_LINE_INDEX_ROOT) / "array-index.json",
                root=root,
            )
            self.assertEqual("incompatible", array_summary["line_index_status"])
            self.assertIn("private_db_json_object_required", array_summary["blocker_categories"])

    def test_missing_directory_and_symlink_inputs_are_rejected(self) -> None:
        with _fake_repo() as root:
            _db_path, review_path = _prepare_private_db_and_review(root)
            missing = run_m2_line_index(
                Path(PRIVATE_DB_ROOT) / "missing.json",
                review_path,
                Path(PRIVATE_LINE_INDEX_ROOT) / "missing-index.json",
                root=root,
            )
            self.assertIn("input_missing", missing["blocker_categories"])

            directory = root / PRIVATE_DB_ROOT / "directory.json"
            directory.mkdir(parents=True)
            with self.assertRaises(M2LineIndexError):
                run_m2_line_index(
                    Path(PRIVATE_DB_ROOT) / "directory.json",
                    review_path,
                    Path(PRIVATE_LINE_INDEX_ROOT) / "directory-index.json",
                    root=root,
                )

            target = root / PRIVATE_DB_ROOT / "target.json"
            target.write_text(json.dumps(_private_db_payload()), encoding="utf-8")
            link = root / PRIVATE_DB_ROOT / "link.json"
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(M2LineIndexError):
                resolve_private_db_input_path(Path(PRIVATE_DB_ROOT) / "link.json", root=root)

    def test_rejects_unsafe_input_review_and_output_paths(self) -> None:
        with _fake_repo() as root:
            _prepare_private_db_and_review(root)
            for path in (
                Path("docs/imported-db.json"),
                Path(PRIVATE_DB_ROOT) / "../imported-db.json",
                Path(PRIVATE_DB_ROOT) / "raw-log-db.json",
            ):
                with self.subTest(input_path=path):
                    with self.assertRaises(M2LineIndexError):
                        resolve_private_db_input_path(path, root=root)
            for path in (
                Path("docs/review.json"),
                Path(LOCAL_IMPORT_REVIEW_ROOT) / "../review.json",
                Path(LOCAL_IMPORT_REVIEW_ROOT) / "payload-dump-review.json",
            ):
                with self.subTest(review_path=path):
                    with self.assertRaises(M2LineIndexError):
                        resolve_import_review_input_path(path, root=root)
            valid = resolve_line_index_output_path(
                Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json",
                root=root,
            )
            self.assertEqual(("line-index", "line-index.json"), valid.parts[-2:])
            for path in (
                Path("docs/line-index.json"),
                Path(PRIVATE_LINE_INDEX_ROOT) / "../line-index.json",
                Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.txt",
                Path(PRIVATE_LINE_INDEX_ROOT) / "raw-log-line-index.json",
            ):
                with self.subTest(output_path=path):
                    with self.assertRaises(M2LineIndexError):
                        resolve_line_index_output_path(path, root=root)

    def test_quiet_cli_and_self_test(self) -> None:
        run_self_test()
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_m2_line_index.py",
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

        self.assertIn("scripts/run_m2_line_index.py", text)
        self.assertIn("--self-test", text)


def _prepare_private_db_and_review(root: Path) -> tuple[Path, Path]:
    private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
    private_file.parent.mkdir(parents=True, exist_ok=True)
    private_file.write_text(json.dumps(_private_export()), encoding="utf-8")
    db_path = Path(PRIVATE_DB_ROOT) / "imported-db.json"
    import_summary = run_m2_local_import(
        Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
        db_path,
        root=root,
    )
    summary_path = (
        root / "workspace/local-private/extraction-indexing/import/db-summary/summary.json"
    )
    write_summary(import_summary, summary_path)
    review = build_review(import_summary, summary_path=summary_path, root=root)
    review_path = root / LOCAL_IMPORT_REVIEW_ROOT / "review.json"
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(json.dumps(review, indent=2, sort_keys=True), encoding="utf-8")
    return db_path, Path(LOCAL_IMPORT_REVIEW_ROOT) / "review.json"


def _private_export() -> dict[str, object]:
    return {
        "schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [
            _record(f"{PRIVATE_MARKER}_B"),
            _record(f"{PRIVATE_MARKER}_A"),
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


def _private_db_payload() -> dict[str, object]:
    return {
        "schema_version": "m2-local-import-db.v1",
        "source_schema_version": "m2-local-private-export.v1",
        "source_kind": "private_export",
        "records": [_record(f"{PRIVATE_MARKER}_A")],
        "context_edges": [],
        "metadata": {"nested_marker": PRIVATE_MARKER},
        "line_index_constructed": False,
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
    }


def _record(record_id: str) -> dict[str, object]:
    suffix = record_id.rsplit("_", maxsplit=1)[-1]
    return {
        "record_id": record_id,
        "line_id": f"{PRIVATE_MARKER}_line_{suffix}",
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
