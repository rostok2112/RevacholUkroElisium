from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_m2_explicit_local_import_adapter_dry_run import (
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    SUMMARY_SCHEMA_VERSION,
    M2ExplicitLocalImportAdapterDryRunError,
    build_m2_explicit_local_import_adapter_dry_run,
    resolve_output_path,
    run_self_test,
    write_summary,
)
from scripts.run_private_input_adapter_dry_run import (
    PrivateInputAdapterDryRunError,
)


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_CONTENT = "PRIVATE_EXPORT_CONTENT_SHOULD_NOT_LEAK"


class M2ExplicitLocalImportAdapterDryRunTests(unittest.TestCase):
    def test_valid_file_input_summarizes_metadata_only(self) -> None:
        with _fake_repo() as root:
            private_file = root / PRIVATE_INPUT_ROOT / "selected.json"
            private_file.parent.mkdir(parents=True)
            private_file.write_text(PRIVATE_CONTENT, encoding="utf-8")

            summary = build_m2_explicit_local_import_adapter_dry_run(
                Path(PRIVATE_INPUT_ROOT) / "selected.json",
                root=root,
            )
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual(SUMMARY_SCHEMA_VERSION, summary["schema_version"])
            self.assertTrue(summary["input_exists"])
            self.assertEqual("file", summary["input_kind"])
            self.assertEqual(len(PRIVATE_CONTENT), summary["byte_count"])
            self.assertEqual("deferred", summary["schema_status"])
            self.assertEqual([], summary["blocker_categories"])
            self.assertTrue(summary["dry_run"])
            self.assertTrue(summary["metadata_only"])
            self.assertFalse(summary["file_contents_read"])
            self.assertFalse(summary["private_content_parsed"])
            self.assertFalse(summary["real_db_imported"])
            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)

    def test_missing_input_returns_redacted_blocker(self) -> None:
        with _fake_repo() as root:
            summary = build_m2_explicit_local_import_adapter_dry_run(
                Path(PRIVATE_INPUT_ROOT) / "missing.json",
                root=root,
            )

            self.assertFalse(summary["input_exists"])
            self.assertEqual("missing", summary["input_kind"])
            self.assertIn("input_missing", summary["blocker_categories"])

    def test_directory_input_is_rejected_as_metadata_only_blocker(self) -> None:
        with _fake_repo() as root:
            directory = root / PRIVATE_INPUT_ROOT / "selected"
            directory.mkdir(parents=True)

            summary = build_m2_explicit_local_import_adapter_dry_run(
                Path(PRIVATE_INPUT_ROOT) / "selected",
                root=root,
            )

            self.assertEqual("unsupported", summary["input_kind"])
            self.assertIn("directory_input_rejected", summary["blocker_categories"])

    def test_rejects_input_outside_allowed_root_and_forbidden_markers(self) -> None:
        with _fake_repo() as root:
            for path in (
                Path("workspace/local-private/elsewhere/export.json"),
                Path(PRIVATE_INPUT_ROOT) / "BepInEx/LogOutput.log",
                Path(PRIVATE_INPUT_ROOT) / "screenshots/export.json",
                Path(PRIVATE_INPUT_ROOT) / "decompiled/export.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(PrivateInputAdapterDryRunError):
                        build_m2_explicit_local_import_adapter_dry_run(path, root=root)

    def test_output_is_restricted_to_private_adapter_dry_run_root(self) -> None:
        with _fake_repo() as root:
            valid = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "summary.json", root=root)
            self.assertEqual(("adapter-dry-run", "summary.json"), valid.parts[-2:])

            for path in (
                Path("docs/summary.json"),
                Path("workspace/local-private/extraction-indexing/import/summary.json"),
                Path(PRIVATE_OUTPUT_ROOT) / "../summary.json",
                Path(PRIVATE_OUTPUT_ROOT) / "summary.txt",
                Path(PRIVATE_OUTPUT_ROOT) / "raw-log-summary.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M2ExplicitLocalImportAdapterDryRunError):
                        resolve_output_path(path, root=root)

    def test_written_summary_never_contains_contents_or_private_paths(self) -> None:
        with _fake_repo() as root:
            private_file = root / PRIVATE_INPUT_ROOT / "selected.json"
            private_file.parent.mkdir(parents=True)
            private_file.write_text(PRIVATE_CONTENT, encoding="utf-8")
            summary = build_m2_explicit_local_import_adapter_dry_run(
                Path(PRIVATE_INPUT_ROOT) / "selected.json",
                root=root,
            )
            output = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "summary.json", root=root)

            write_summary(summary, output)
            written = output.read_text(encoding="utf-8")

            self.assertNotIn(PRIVATE_CONTENT, written)
            self.assertNotIn(str(root), written)
            self.assertFalse(json.loads(written)["file_contents_read"])

    def test_self_test_uses_temp_workspace_only(self) -> None:
        run_self_test()

    def test_cli_self_test_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_m2_explicit_local_import_adapter_dry_run.py",
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
        self.assertNotIn(PRIVATE_CONTENT, completed.stdout)

    def test_check_all_registers_m2_explicit_adapter_dry_run_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_m2_explicit_local_import_adapter_dry_run.py", text)
        self.assertIn("--self-test", text)


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
