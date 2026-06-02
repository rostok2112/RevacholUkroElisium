from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_m2_explicit_local_import_schema_compatibility_dry_run import (
    FUTURE_PROFILE_SCHEMA_VERSION,
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    SUMMARY_SCHEMA_VERSION,
    M2ExplicitLocalImportSchemaCompatibilityDryRunError,
    build_m2_explicit_local_import_schema_compatibility_dry_run,
    resolve_output_path,
    run_self_test,
    write_summary,
)
from scripts.run_private_input_adapter_dry_run import PrivateInputAdapterDryRunError


ROOT = Path(__file__).resolve().parents[1]
NESTED_MARKER = "PRIVATE_NESTED_VALUE_SHOULD_NOT_LEAK"


class M2ExplicitLocalImportSchemaCompatibilityDryRunTests(unittest.TestCase):
    def test_compatible_envelope_reports_counts_without_nested_values(self) -> None:
        with _fake_repo() as root:
            path = _write_private_json(root, "compatible.json", _compatible_payload())

            summary = build_m2_explicit_local_import_schema_compatibility_dry_run(
                _relative_private_path(path, root),
                root=root,
            )
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual(SUMMARY_SCHEMA_VERSION, summary["schema_version"])
            self.assertEqual("compatible", summary["schema_status"])
            self.assertTrue(summary["json_object_decoded"])
            self.assertTrue(summary["profile_schema_version_matches"])
            self.assertTrue(summary["required_envelope_fields_present"])
            self.assertTrue(summary["required_envelope_types_match"])
            self.assertEqual(2, summary["records_count"])
            self.assertEqual(1, summary["context_edges_count"])
            self.assertEqual([], summary["blocker_categories"])
            self.assertFalse(summary["nested_values_traversed"])
            self.assertFalse(summary["nested_values_included"])
            self.assertNotIn(NESTED_MARKER, rendered)
            self.assertNotIn(str(root), rendered)

    def test_wrong_schema_version_is_redacted_incompatible_result(self) -> None:
        with _fake_repo() as root:
            payload = _compatible_payload()
            payload["schema_version"] = "m2-local-private-export.v0"
            path = _write_private_json(root, "wrong-version.json", payload)

            summary = _build_for(path, root)

            self.assertEqual("incompatible", summary["schema_status"])
            self.assertFalse(summary["profile_schema_version_matches"])
            self.assertIn("profile_schema_version_mismatch", summary["blocker_categories"])

    def test_missing_or_extra_top_level_fields_are_incompatible(self) -> None:
        with _fake_repo() as root:
            for label, mutate, blocker in (
                (
                    "missing",
                    lambda payload: payload.pop("metadata"),
                    "required_envelope_fields_missing",
                ),
                (
                    "extra",
                    lambda payload: payload.update({"extra": "redacted"}),
                    "unexpected_top_level_envelope_fields",
                ),
            ):
                with self.subTest(label=label):
                    payload = _compatible_payload()
                    mutate(payload)
                    path = _write_private_json(root, f"{label}.json", payload)
                    summary = _build_for(path, root)
                    self.assertEqual("incompatible", summary["schema_status"])
                    self.assertIn(blocker, summary["blocker_categories"])

    def test_wrong_top_level_types_are_incompatible_without_traversal(self) -> None:
        with _fake_repo() as root:
            payload = _compatible_payload()
            payload["records"] = {"nested": NESTED_MARKER}
            payload["context_edges"] = "not-an-array"
            payload["metadata"] = []
            path = _write_private_json(root, "wrong-types.json", payload)

            summary = _build_for(path, root)
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual("incompatible", summary["schema_status"])
            self.assertIn("required_envelope_types_mismatch", summary["blocker_categories"])
            self.assertEqual(0, summary["records_count"])
            self.assertEqual(0, summary["context_edges_count"])
            self.assertNotIn(NESTED_MARKER, rendered)

    def test_malformed_and_non_object_json_are_redacted(self) -> None:
        with _fake_repo() as root:
            malformed = root / PRIVATE_INPUT_ROOT / "malformed.json"
            malformed.parent.mkdir(parents=True)
            malformed.write_text("{", encoding="utf-8")
            malformed_summary = _build_for(malformed, root)
            self.assertEqual("decode_failed", malformed_summary["schema_status"])
            self.assertIn("json_decode_failed", malformed_summary["blocker_categories"])

            array = _write_private_json(root, "array.json", [{"nested": NESTED_MARKER}])
            array_summary = _build_for(array, root)
            self.assertEqual("incompatible", array_summary["schema_status"])
            self.assertIn("top_level_json_object_required", array_summary["blocker_categories"])

    def test_missing_directory_and_symlink_inputs_are_rejected_safely(self) -> None:
        with _fake_repo() as root:
            missing = build_m2_explicit_local_import_schema_compatibility_dry_run(
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
                        build_m2_explicit_local_import_schema_compatibility_dry_run(
                            path,
                            root=root,
                        )

            valid = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "summary.json", root=root)
            self.assertEqual(("schema-compatibility", "summary.json"), valid.parts[-2:])
            for path in (
                Path("docs/summary.json"),
                Path("workspace/local-private/extraction-indexing/import/summary.json"),
                Path(PRIVATE_OUTPUT_ROOT) / "../summary.json",
                Path(PRIVATE_OUTPUT_ROOT) / "summary.txt",
                Path(PRIVATE_OUTPUT_ROOT) / "raw-log-summary.json",
            ):
                with self.subTest(output_path=path):
                    with self.assertRaises(M2ExplicitLocalImportSchemaCompatibilityDryRunError):
                        resolve_output_path(path, root=root)

    def test_written_summary_is_redacted(self) -> None:
        with _fake_repo() as root:
            private_file = _write_private_json(root, "compatible.json", _compatible_payload())
            summary = _build_for(private_file, root)
            output = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "summary.json", root=root)

            write_summary(summary, output)
            written = output.read_text(encoding="utf-8")

            self.assertNotIn(NESTED_MARKER, written)
            self.assertNotIn(str(root), written)
            self.assertFalse(json.loads(written)["nested_values_traversed"])

    def test_self_test_and_quiet_cli_use_temp_workspace_only(self) -> None:
        run_self_test()
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_schema_compatibility_dry_run.py",
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
        self.assertNotIn(NESTED_MARKER, completed.stdout)

    def test_check_all_registers_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn(
            "scripts/run_m2_explicit_local_import_schema_compatibility_dry_run.py",
            text,
        )
        self.assertIn("--self-test", text)


def _compatible_payload() -> dict[str, object]:
    return {
        "schema_version": FUTURE_PROFILE_SCHEMA_VERSION,
        "source_kind": "private_export",
        "records": [{"source_text": NESTED_MARKER}, {"nested": NESTED_MARKER}],
        "context_edges": [{"nested": NESTED_MARKER}],
        "metadata": {"nested": NESTED_MARKER},
    }


def _write_private_json(root: Path, name: str, payload: object) -> Path:
    path = root / PRIVATE_INPUT_ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _relative_private_path(path: Path, root: Path) -> Path:
    return path.relative_to(root)


def _build_for(path: Path, root: Path) -> dict[str, object]:
    return build_m2_explicit_local_import_schema_compatibility_dry_run(
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
