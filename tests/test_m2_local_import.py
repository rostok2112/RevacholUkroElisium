from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_m2_local_import import (
    PRIVATE_DB_SCHEMA_VERSION,
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    SUMMARY_SCHEMA_VERSION,
    M2LocalImportError,
    resolve_output_path,
    run_m2_local_import,
    run_self_test,
)
from scripts.run_private_input_adapter_dry_run import PrivateInputAdapterDryRunError


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKER = "PRIVATE_LOCAL_IMPORT_VALUE_SHOULD_NOT_LEAK"
PRIVATE_RECORD_A = "private.local.import.record.a"
PRIVATE_RECORD_B = "private.local.import.record.b"


class M2LocalImportTests(unittest.TestCase):
    def test_import_writes_private_db_and_redacted_summary(self) -> None:
        with _fake_repo() as root:
            input_path = _write_private_json(root, "export.json", _compatible_payload())
            output_path = Path(PRIVATE_OUTPUT_ROOT) / "imported-db.json"

            summary = run_m2_local_import(_relative(input_path, root), output_path, root=root)
            rendered = json.dumps(summary, sort_keys=True)
            private_db = json.loads((root / output_path).read_text(encoding="utf-8"))

            self.assertEqual(SUMMARY_SCHEMA_VERSION, summary["schema_version"])
            self.assertEqual("imported", summary["import_status"])
            self.assertTrue(summary["private_db_output_written"])
            self.assertTrue(summary["m2_import_locally_extracted_db_implemented"])
            self.assertTrue(summary["ready_for_line_index_contract"])
            self.assertEqual(2, summary["records_count"])
            self.assertEqual(1, summary["context_edges_count"])
            self.assertFalse(summary["line_index_constructed"])
            self.assertFalse(summary["context_graph_constructed"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn(PRIVATE_RECORD_A, rendered)
            self.assertNotIn("previous_visible", rendered)
            self.assertNotIn(str(root), rendered)

            self.assertEqual(PRIVATE_DB_SCHEMA_VERSION, private_db["schema_version"])
            self.assertEqual("m2-local-private-export.v1", private_db["source_schema_version"])
            self.assertTrue(private_db["imported_from_explicit_private_export"])
            self.assertEqual(_compatible_payload()["records"], private_db["records"])
            self.assertEqual(_compatible_payload()["context_edges"], private_db["context_edges"])
            self.assertIn(PRIVATE_MARKER, json.dumps(private_db, sort_keys=True))
            self.assertNotIn("input_path", private_db)
            self.assertNotIn("output_path", private_db)
            self.assertFalse(private_db["line_index_constructed"])
            self.assertFalse(private_db["context_graph_constructed"])

    def test_decode_and_shape_failures_do_not_write_output(self) -> None:
        with _fake_repo() as root:
            malformed = root / PRIVATE_INPUT_ROOT / "malformed.json"
            malformed.parent.mkdir(parents=True)
            malformed.write_text("{", encoding="utf-8")
            malformed_summary = run_m2_local_import(
                _relative(malformed, root),
                Path(PRIVATE_OUTPUT_ROOT) / "malformed-db.json",
                root=root,
            )
            self.assertEqual("decode_failed", malformed_summary["import_status"])
            self.assertFalse(malformed_summary["private_db_output_written"])
            self.assertFalse((root / PRIVATE_OUTPUT_ROOT / "malformed-db.json").exists())

            bad_record = _compatible_payload()
            bad_record["records"] = [{"record_id": PRIVATE_RECORD_A}]
            bad_record_path = _write_private_json(root, "bad-record.json", bad_record)
            bad_record_summary = run_m2_local_import(
                _relative(bad_record_path, root),
                Path(PRIVATE_OUTPUT_ROOT) / "bad-record-db.json",
                root=root,
            )
            self.assertEqual("incompatible", bad_record_summary["import_status"])
            self.assertIn(
                "record_shape_precondition_failed", bad_record_summary["blocker_categories"]
            )
            self.assertFalse(bad_record_summary["private_db_output_written"])

            bad_edge = _compatible_payload()
            bad_edge["context_edges"] = [{"from_record_id": PRIVATE_RECORD_A}]
            bad_edge_path = _write_private_json(root, "bad-edge.json", bad_edge)
            bad_edge_summary = run_m2_local_import(
                _relative(bad_edge_path, root),
                Path(PRIVATE_OUTPUT_ROOT) / "bad-edge-db.json",
                root=root,
            )
            self.assertEqual("incompatible", bad_edge_summary["import_status"])
            self.assertIn(
                "context_edge_shape_precondition_failed",
                bad_edge_summary["blocker_categories"],
            )
            self.assertFalse(bad_edge_summary["private_db_output_written"])

    def test_reference_and_integrity_failures_block_import(self) -> None:
        with _fake_repo() as root:
            unresolved = _compatible_payload()
            unresolved["context_edges"][0]["to_record_id"] = "private.local.import.unknown"
            unresolved_path = _write_private_json(root, "unresolved.json", unresolved)
            unresolved_summary = run_m2_local_import(
                _relative(unresolved_path, root),
                Path(PRIVATE_OUTPUT_ROOT) / "unresolved-db.json",
                root=root,
            )
            self.assertEqual("incompatible", unresolved_summary["import_status"])
            self.assertIn(
                "context_edge_reference_precondition_failed",
                unresolved_summary["blocker_categories"],
            )
            self.assertFalse(unresolved_summary["private_db_output_written"])

            duplicate = _compatible_payload()
            duplicate["context_edges"].append(dict(duplicate["context_edges"][0]))
            duplicate_path = _write_private_json(root, "duplicate-edge.json", duplicate)
            duplicate_summary = run_m2_local_import(
                _relative(duplicate_path, root),
                Path(PRIVATE_OUTPUT_ROOT) / "duplicate-edge-db.json",
                root=root,
            )
            self.assertEqual("incompatible", duplicate_summary["import_status"])
            self.assertIn("duplicate_edges_found", duplicate_summary["blocker_categories"])
            self.assertFalse(duplicate_summary["private_db_output_written"])

            self_edge = _compatible_payload()
            self_edge["context_edges"] = [
                {
                    "from_record_id": PRIVATE_RECORD_A,
                    "to_record_id": PRIVATE_RECORD_A,
                    "relation": "previous_visible",
                }
            ]
            self_edge_path = _write_private_json(root, "self-edge.json", self_edge)
            self_edge_summary = run_m2_local_import(
                _relative(self_edge_path, root),
                Path(PRIVATE_OUTPUT_ROOT) / "self-edge-db.json",
                root=root,
            )
            self.assertEqual("incompatible", self_edge_summary["import_status"])
            self.assertIn("self_edges_found", self_edge_summary["blocker_categories"])
            self.assertFalse(self_edge_summary["private_db_output_written"])

    def test_duplicate_record_id_blocks_import_without_id_leak(self) -> None:
        with _fake_repo() as root:
            payload = _compatible_payload()
            payload["records"][1]["record_id"] = PRIVATE_RECORD_A
            input_path = _write_private_json(root, "duplicate-records.json", payload)

            summary = run_m2_local_import(
                _relative(input_path, root),
                Path(PRIVATE_OUTPUT_ROOT) / "duplicate-records-db.json",
                root=root,
            )
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual("incompatible", summary["import_status"])
            self.assertIn("duplicate_record_id", summary["blocker_categories"])
            self.assertFalse(summary["private_db_output_written"])
            self.assertNotIn(PRIVATE_RECORD_A, rendered)

    def test_missing_directory_and_symlink_inputs_do_not_import(self) -> None:
        with _fake_repo() as root:
            missing = run_m2_local_import(
                Path(PRIVATE_INPUT_ROOT) / "missing.json",
                Path(PRIVATE_OUTPUT_ROOT) / "missing-db.json",
                root=root,
            )
            self.assertIn("input_missing", missing["blocker_categories"])
            self.assertFalse(missing["private_db_output_written"])

            directory = root / PRIVATE_INPUT_ROOT / "directory"
            directory.mkdir(parents=True)
            directory_summary = run_m2_local_import(
                _relative(directory, root),
                Path(PRIVATE_OUTPUT_ROOT) / "directory-db.json",
                root=root,
            )
            self.assertIn("directory_input_rejected", directory_summary["blocker_categories"])

            target = _write_private_json(root, "target.json", _compatible_payload())
            link = root / PRIVATE_INPUT_ROOT / "link.json"
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            link_summary = run_m2_local_import(
                _relative(link, root),
                Path(PRIVATE_OUTPUT_ROOT) / "link-db.json",
                root=root,
            )
            self.assertIn("symlink_input_rejected", link_summary["blocker_categories"])

    def test_rejects_unsafe_input_and_output_paths(self) -> None:
        with _fake_repo() as root:
            for path in (
                Path("workspace/local-private/elsewhere/export.json"),
                Path(PRIVATE_INPUT_ROOT) / "BepInEx/LogOutput.log",
                Path(PRIVATE_INPUT_ROOT) / "screenshots/export.json",
                Path(PRIVATE_INPUT_ROOT) / "decompiled/export.json",
            ):
                with self.subTest(input_path=path):
                    with self.assertRaises(PrivateInputAdapterDryRunError):
                        run_m2_local_import(
                            path,
                            Path(PRIVATE_OUTPUT_ROOT) / "db.json",
                            root=root,
                        )

            valid = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "db.json", root=root)
            self.assertEqual(("db", "db.json"), valid.parts[-2:])
            for path in (
                Path("docs/db.json"),
                Path("workspace/local-private/extraction-indexing/import/db.txt"),
                Path("workspace/local-private/extraction-indexing/import/record-shape/db.json"),
                Path(PRIVATE_OUTPUT_ROOT) / "../db.json",
                Path(PRIVATE_OUTPUT_ROOT) / "raw-log-db.json",
            ):
                with self.subTest(output_path=path):
                    with self.assertRaises(M2LocalImportError):
                        resolve_output_path(path, root=root)

    def test_cli_requires_output_and_quiet_output_stays_redacted(self) -> None:
        with _fake_repo() as root:
            input_path = _write_private_json(root, "export.json", _compatible_payload())
            missing_output = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/run_m2_local_import.py"),
                    "--input",
                    str(_relative(input_path, root)),
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, missing_output.returncode)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/run_m2_local_import.py"),
                    "--input",
                    str(_relative(input_path, root)),
                    "--output",
                    str(Path(PRIVATE_OUTPUT_ROOT) / "db.json"),
                    "--quiet",
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("passed", completed.stdout.lower())
            self.assertNotIn(PRIVATE_MARKER, completed.stdout)
            self.assertNotIn(str(root), completed.stdout)

    def test_self_test_and_check_all_registration(self) -> None:
        run_self_test()
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_m2_local_import.py",
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

        check_all = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        self.assertIn("scripts/run_m2_local_import.py", check_all)
        self.assertIn("--self-test", check_all)


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
            }
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


def _write_private_json(root: Path, name: str, payload: object) -> Path:
    path = root / PRIVATE_INPUT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _relative(path: Path, root: Path) -> Path:
    return path.relative_to(root)


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
