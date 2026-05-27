from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_private_input_adapter_dry_run import (
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    SUMMARY_SCHEMA_VERSION,
    PrivateInputAdapterDryRunError,
    build_dry_run_summary,
    resolve_input_path,
    resolve_output_path,
    run_self_test,
    write_summary,
)


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_CONTENT = "PRIVATE_CONTENT_SHOULD_NOT_LEAK"


class PrivateInputAdapterDryRunTests(unittest.TestCase):
    def test_valid_file_input_summarizes_metadata_only(self) -> None:
        with _fake_repo() as root:
            private_file = root / PRIVATE_INPUT_ROOT / "selected.txt"
            private_file.parent.mkdir(parents=True)
            private_file.write_text(PRIVATE_CONTENT, encoding="utf-8")

            summary = build_dry_run_summary(
                Path(PRIVATE_INPUT_ROOT) / "selected.txt",
                root=root,
                verbose=False,
            )
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual(SUMMARY_SCHEMA_VERSION, summary["schema_version"])
            self.assertTrue(summary["input_exists"])
            self.assertEqual("file", summary["input_kind"])
            self.assertEqual(1, summary["file_count"])
            self.assertEqual(0, summary["directory_count"])
            self.assertEqual(len(PRIVATE_CONTENT), summary["total_size_bytes"])
            self.assertTrue(summary["dry_run"])
            self.assertFalse(summary["hashes_computed"])
            self.assertFalse(summary["file_contents_read"])
            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)

    def test_valid_directory_input_counts_metadata_without_contents(self) -> None:
        with _fake_repo() as root:
            selected = root / PRIVATE_INPUT_ROOT / "selected"
            nested = selected / "nested"
            nested.mkdir(parents=True)
            (selected / "one.txt").write_text(PRIVATE_CONTENT, encoding="utf-8")
            (nested / "two.txt").write_text("another private line", encoding="utf-8")

            summary = build_dry_run_summary(
                Path(PRIVATE_INPUT_ROOT) / "selected",
                root=root,
                verbose=False,
            )
            rendered = json.dumps(summary, sort_keys=True)

            self.assertEqual("directory", summary["input_kind"])
            self.assertEqual(2, summary["file_count"])
            self.assertEqual(1, summary["directory_count"])
            self.assertGreater(summary["total_size_bytes"], 0)
            self.assertFalse(summary["traversal_truncated"])
            self.assertNotIn(PRIVATE_CONTENT, rendered)

    def test_missing_input_under_allowed_root_returns_redacted_summary(self) -> None:
        with _fake_repo() as root:
            summary = build_dry_run_summary(
                Path(PRIVATE_INPUT_ROOT) / "missing.txt",
                root=root,
                verbose=False,
            )

            self.assertFalse(summary["input_exists"])
            self.assertEqual("missing", summary["input_kind"])
            self.assertEqual(0, summary["file_count"])
            self.assertIn("input_missing", summary["blocker_categories"])

    def test_rejects_input_outside_allowed_root(self) -> None:
        with _fake_repo() as root:
            outside = root / "workspace/local-private/elsewhere/input.txt"
            outside.parent.mkdir(parents=True)
            outside.write_text(PRIVATE_CONTENT, encoding="utf-8")

            with self.assertRaises(PrivateInputAdapterDryRunError):
                resolve_input_path(Path("workspace/local-private/elsewhere/input.txt"), root=root)

    def test_rejects_absolute_external_paths(self) -> None:
        with _fake_repo() as root:
            external = root.parent / "external.txt"
            external.write_text(PRIVATE_CONTENT, encoding="utf-8")

            with self.assertRaises(PrivateInputAdapterDryRunError):
                resolve_input_path(external, root=root)

    def test_rejects_forbidden_path_markers(self) -> None:
        with _fake_repo() as root:
            for path in (
                Path(PRIVATE_INPUT_ROOT) / "BepInEx/LogOutput.log",
                Path(PRIVATE_INPUT_ROOT) / "steamapps/common/file.txt",
                Path(PRIVATE_INPUT_ROOT) / "screenshots/frame.png",
                Path(PRIVATE_INPUT_ROOT) / "ocr-output.txt",
                Path(PRIVATE_INPUT_ROOT) / "slot.sav",
                Path(PRIVATE_INPUT_ROOT) / "decompiled/methods.txt",
                Path(PRIVATE_INPUT_ROOT) / "raw-payload-dump.txt",
                Path(PRIVATE_INPUT_ROOT) / "raw-log.txt",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(PrivateInputAdapterDryRunError):
                        resolve_input_path(path, root=root)

    def test_rejects_output_outside_private_output_root(self) -> None:
        with _fake_repo() as root:
            for path in (
                Path("docs/private-input-summary.json"),
                Path("workspace/synthetic-slice/private-input-summary.json"),
                Path("../workspace/local-private/extraction-indexing/summary.json"),
            ):
                with self.subTest(path=path):
                    with self.assertRaises(PrivateInputAdapterDryRunError):
                        resolve_output_path(path, root=root)

    def test_writes_report_only_under_private_output_root(self) -> None:
        with _fake_repo() as root:
            private_file = root / PRIVATE_INPUT_ROOT / "selected.txt"
            private_file.parent.mkdir(parents=True)
            private_file.write_text(PRIVATE_CONTENT, encoding="utf-8")
            summary = build_dry_run_summary(
                Path(PRIVATE_INPUT_ROOT) / "selected.txt",
                root=root,
                verbose=False,
            )
            output = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "summary.json", root=root)

            write_summary(summary, output)
            written = output.read_text(encoding="utf-8")

            self.assertTrue(output.exists())
            self.assertNotIn(PRIVATE_CONTENT, written)
            self.assertNotIn(str(root), written)

    def test_verbose_summary_may_include_paths_but_not_contents(self) -> None:
        with _fake_repo() as root:
            private_file = root / PRIVATE_INPUT_ROOT / "selected.txt"
            private_file.parent.mkdir(parents=True)
            private_file.write_text(PRIVATE_CONTENT, encoding="utf-8")

            summary = build_dry_run_summary(
                Path(PRIVATE_INPUT_ROOT) / "selected.txt",
                root=root,
                verbose=True,
            )
            rendered = json.dumps(summary, sort_keys=True)

            self.assertTrue(summary["input_path"].startswith(str(root)))
            self.assertTrue(summary["allowed_root_path"].startswith(str(root)))
            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertFalse(summary["paths_redacted"])

    def test_directory_traversal_is_bounded(self) -> None:
        with _fake_repo() as root:
            selected = root / PRIVATE_INPUT_ROOT / "selected"
            selected.mkdir(parents=True)
            for index in range(3):
                (selected / f"{index}.txt").write_text("private", encoding="utf-8")

            summary = build_dry_run_summary(
                Path(PRIVATE_INPUT_ROOT) / "selected",
                root=root,
                verbose=False,
                traversal_limit=2,
            )

            self.assertTrue(summary["traversal_truncated"])
            self.assertIn("traversal_limit_reached", summary["blocker_categories"])

    def test_self_test_uses_temp_workspace_only(self) -> None:
        run_self_test()

    def test_cli_self_test_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_private_input_adapter_dry_run.py",
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

    def test_check_all_registers_private_input_adapter_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_private_input_adapter_dry_run.py", text)
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
