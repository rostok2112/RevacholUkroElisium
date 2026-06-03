from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_m2_explicit_local_import_context_edge_reference_dry_run import (
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    SUMMARY_SCHEMA_VERSION,
    M2ExplicitLocalImportContextEdgeReferenceDryRunError,
    build_m2_explicit_local_import_context_edge_reference_dry_run,
    resolve_output_path,
    run_self_test,
    write_summary,
)
from scripts.run_private_input_adapter_dry_run import PrivateInputAdapterDryRunError


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_MARKER = "PRIVATE_CONTEXT_EDGE_REFERENCE_VALUE_SHOULD_NOT_LEAK"
UNKNOWN_MARKER = "PRIVATE_UNRESOLVED_RECORD_ID_SHOULD_NOT_LEAK"


class M2ExplicitLocalImportContextEdgeReferenceDryRunTests(unittest.TestCase):
    def test_compatible_references_report_counts_without_ids(self) -> None:
        with _fake_repo() as root:
            path = _write_private_json(root, "compatible.json", _compatible_payload())

            summary = _build_for(path, root)
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual(SUMMARY_SCHEMA_VERSION, summary["schema_version"])
            self.assertEqual("compatible", summary["context_edge_reference_status"])
            self.assertTrue(summary["envelope_compatible"])
            self.assertTrue(summary["records_shape_reviewed"])
            self.assertTrue(summary["context_edges_shape_reviewed"])
            self.assertTrue(summary["record_id_set_built"])
            self.assertEqual(3, summary["context_edges_count"])
            self.assertEqual(3, summary["context_edges_references_checked_count"])
            self.assertEqual(3, summary["context_edges_with_resolved_from_count"])
            self.assertEqual(3, summary["context_edges_with_resolved_to_count"])
            self.assertEqual(0, summary["context_edges_with_unresolved_reference_count"])
            self.assertTrue(summary["all_context_edge_references_resolved"])
            self.assertEqual([], summary["blocker_categories"])
            self.assertNotIn(PRIVATE_MARKER, rendered)
            self.assertNotIn(str(root), rendered)

    def test_unresolved_from_and_to_references_are_aggregate_only(self) -> None:
        with _fake_repo() as root:
            payload = _compatible_payload()
            payload["context_edges"] = [
                {
                    "from_record_id": UNKNOWN_MARKER,
                    "to_record_id": "private.record.b",
                    "relation": "previous_visible",
                },
                {
                    "from_record_id": "private.record.a",
                    "to_record_id": UNKNOWN_MARKER,
                    "relation": "nearby_branch",
                },
            ]
            path = _write_private_json(root, "unresolved.json", payload)

            summary = _build_for(path, root)
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual("incompatible", summary["context_edge_reference_status"])
            self.assertEqual(2, summary["context_edges_references_checked_count"])
            self.assertEqual(1, summary["context_edges_with_resolved_from_count"])
            self.assertEqual(1, summary["context_edges_with_resolved_to_count"])
            self.assertEqual(2, summary["context_edges_with_unresolved_reference_count"])
            self.assertFalse(summary["all_context_edge_references_resolved"])
            self.assertIn("context_edge_reference_unresolved", summary["blocker_categories"])
            self.assertNotIn(UNKNOWN_MARKER, rendered)
            self.assertNotIn(PRIVATE_MARKER, rendered)

    def test_empty_context_edges_array_is_compatible(self) -> None:
        with _fake_repo() as root:
            payload = _compatible_payload()
            payload["context_edges"] = []
            path = _write_private_json(root, "empty.json", payload)

            summary = _build_for(path, root)

            self.assertEqual("compatible", summary["context_edge_reference_status"])
            self.assertEqual(0, summary["context_edges_count"])
            self.assertEqual(0, summary["context_edges_references_checked_count"])
            self.assertTrue(summary["all_context_edge_references_resolved"])

    def test_malformed_and_non_object_json_are_redacted(self) -> None:
        with _fake_repo() as root:
            malformed = root / PRIVATE_INPUT_ROOT / "malformed.json"
            malformed.parent.mkdir(parents=True)
            malformed.write_text("{", encoding="utf-8")
            malformed_summary = _build_for(malformed, root)
            self.assertEqual("decode_failed", malformed_summary["context_edge_reference_status"])
            self.assertIn("json_decode_failed", malformed_summary["blocker_categories"])

            array = _write_private_json(root, "array.json", [{"nested": PRIVATE_MARKER}])
            array_summary = _build_for(array, root)
            self.assertEqual("incompatible", array_summary["context_edge_reference_status"])
            self.assertIn("top_level_json_object_required", array_summary["blocker_categories"])
            self.assertNotIn(PRIVATE_MARKER, json.dumps(array_summary, sort_keys=True))

    def test_precondition_failures_block_reference_checks(self) -> None:
        with _fake_repo() as root:
            payload = _compatible_payload()
            payload["schema_version"] = "m2-local-private-export.v0"
            payload["extra"] = PRIVATE_MARKER
            path = _write_private_json(root, "bad-envelope.json", payload)
            summary = _build_for(path, root)
            self.assertFalse(summary["envelope_compatible"])
            self.assertEqual(0, summary["context_edges_references_checked_count"])
            self.assertIn("envelope_fields_mismatch", summary["blocker_categories"])
            self.assertIn("profile_schema_version_mismatch", summary["blocker_categories"])

            bad_records = _compatible_payload()
            bad_records["records"] = [{"record_id": PRIVATE_MARKER}]
            bad_record_path = _write_private_json(root, "bad-records.json", bad_records)
            bad_record_summary = _build_for(bad_record_path, root)
            self.assertTrue(bad_record_summary["envelope_compatible"])
            self.assertFalse(bad_record_summary["records_shape_reviewed"])
            self.assertEqual(0, bad_record_summary["context_edges_references_checked_count"])
            self.assertIn(
                "record_shape_precondition_failed",
                bad_record_summary["blocker_categories"],
            )

            bad_edges = _compatible_payload()
            bad_edges["context_edges"] = [{"from_record_id": PRIVATE_MARKER}]
            bad_edge_path = _write_private_json(root, "bad-edges.json", bad_edges)
            bad_edge_summary = _build_for(bad_edge_path, root)
            self.assertTrue(bad_edge_summary["records_shape_reviewed"])
            self.assertFalse(bad_edge_summary["context_edges_shape_reviewed"])
            self.assertFalse(bad_edge_summary["record_id_set_built"])
            self.assertEqual(0, bad_edge_summary["context_edges_references_checked_count"])
            self.assertIn(
                "context_edge_shape_precondition_failed",
                bad_edge_summary["blocker_categories"],
            )

    def test_duplicate_record_ids_are_blocked_without_emitting_ids(self) -> None:
        with _fake_repo() as root:
            payload = _compatible_payload()
            payload["records"][1]["record_id"] = payload["records"][0]["record_id"]
            path = _write_private_json(root, "duplicate-records.json", payload)

            summary = _build_for(path, root)
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual("incompatible", summary["context_edge_reference_status"])
            self.assertFalse(summary["record_id_set_built"])
            self.assertEqual(0, summary["context_edges_references_checked_count"])
            self.assertIn("duplicate_record_id", summary["blocker_categories"])
            self.assertNotIn("private.record.a", rendered)
            self.assertNotIn(PRIVATE_MARKER, rendered)

    def test_self_and_duplicate_edges_remain_reference_compatible_when_ids_resolve(self) -> None:
        with _fake_repo() as root:
            payload = _compatible_payload()
            payload["context_edges"] = [
                {
                    "from_record_id": "private.record.a",
                    "to_record_id": "private.record.a",
                    "relation": "previous_visible",
                },
                {
                    "from_record_id": "private.record.a",
                    "to_record_id": "private.record.a",
                    "relation": "previous_visible",
                },
            ]
            path = _write_private_json(root, "deferred.json", payload)

            summary = _build_for(path, root)
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual("compatible", summary["context_edge_reference_status"])
            self.assertEqual(2, summary["context_edges_references_checked_count"])
            self.assertFalse(summary["self_edge_check_used"])
            self.assertFalse(summary["duplicate_edge_check_used"])
            self.assertFalse(summary["retrieval_bucket_mapping_used"])
            self.assertNotIn("private.record.a", rendered)

    def test_missing_directory_and_symlink_inputs_are_rejected_safely(self) -> None:
        with _fake_repo() as root:
            missing = build_m2_explicit_local_import_context_edge_reference_dry_run(
                Path(PRIVATE_INPUT_ROOT) / "missing.json",
                root=root,
            )
            self.assertIn("input_missing", missing["blocker_categories"])

            directory = root / PRIVATE_INPUT_ROOT / "directory"
            directory.mkdir(parents=True)
            directory_summary = _build_for(directory, root)
            self.assertIn("directory_input_rejected", directory_summary["blocker_categories"])

            target = _write_private_json(root, "target.json", _compatible_payload())
            link = root / PRIVATE_INPUT_ROOT / "link.json"
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            link_summary = _build_for(link, root)
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
                        build_m2_explicit_local_import_context_edge_reference_dry_run(
                            path,
                            root=root,
                        )

            valid = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "summary.json", root=root)
            self.assertEqual(("context-edge-reference", "summary.json"), valid.parts[-2:])
            for path in (
                Path("docs/summary.json"),
                Path("workspace/local-private/extraction-indexing/import/summary.json"),
                Path(PRIVATE_OUTPUT_ROOT) / "../summary.json",
                Path(PRIVATE_OUTPUT_ROOT) / "summary.txt",
                Path(PRIVATE_OUTPUT_ROOT) / "raw-log-summary.json",
            ):
                with self.subTest(output_path=path):
                    with self.assertRaises(M2ExplicitLocalImportContextEdgeReferenceDryRunError):
                        resolve_output_path(path, root=root)

    def test_written_summary_is_redacted_and_no_ids_are_emitted(self) -> None:
        with _fake_repo() as root:
            private_file = _write_private_json(root, "compatible.json", _compatible_payload())
            summary = _build_for(private_file, root)
            output = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "summary.json", root=root)

            write_summary(summary, output)
            written = output.read_text(encoding="utf-8")
            parsed = json.loads(written)

            self.assertNotIn(PRIVATE_MARKER, written)
            self.assertNotIn("private.record.a", written)
            self.assertNotIn(str(root), written)
            self.assertFalse(parsed["record_ids_included"])
            self.assertFalse(parsed["edge_ids_included"])
            self.assertFalse(parsed["relation_values_included"])
            self.assertFalse(parsed["record_values_inspected"])
            self.assertFalse(parsed["metadata_contents_traversed"])

    def test_self_test_and_quiet_cli_use_temp_workspace_only(self) -> None:
        run_self_test()
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_context_edge_reference_dry_run.py",
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
            "scripts/run_m2_explicit_local_import_context_edge_reference_dry_run.py",
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
            {
                "from_record_id": "private.record.b",
                "to_record_id": "private.record.a",
                "relation": "player_option",
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


def _write_private_json(root: Path, name: str, payload: object) -> Path:
    path = root / PRIVATE_INPUT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _relative_private_path(path: Path, root: Path) -> Path:
    return path.relative_to(root)


def _build_for(path: Path, root: Path) -> dict[str, object]:
    return build_m2_explicit_local_import_context_edge_reference_dry_run(
        _relative_private_path(path, root),
        root=root,
    )


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
