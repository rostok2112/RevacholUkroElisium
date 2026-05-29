from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_dry_run_summary_hash import (
    HASH_OUTPUT_ROOT,
    build_hash_summary,
    write_hash_summary,
)
from scripts.run_private_index_builder_dry_run import (
    FALSE_SAFETY_FIELDS,
    INDEX_DRY_RUN_SCHEMA_VERSION,
    PRIVATE_INDEX_OUTPUT_ROOT,
    PrivateIndexBuilderDryRunError,
    build_private_index_dry_run,
    collect_index_source_errors,
    resolve_hash_input_path,
    resolve_output_path,
    resolve_summary_input_path,
    run_self_test,
    write_private_index_dry_run,
)
from scripts.run_private_input_adapter_dry_run import PRIVATE_OUTPUT_ROOT, write_summary
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FIXTURE = ROOT / "tests/fixtures/private_index_dry_run.synthetic.json"
PRIVATE_CONTENT = "PRIVATE_CONTENT_SHOULD_NOT_LEAK"


class PrivateIndexBuilderDryRunTests(unittest.TestCase):
    def test_valid_summary_and_hash_build_deterministically(self) -> None:
        with _fake_repo() as root:
            summary_path, hash_path = _write_valid_inputs(root)
            first = build_private_index_dry_run(
                load_json(summary_path),
                load_json(hash_path),
                summary_path=summary_path,
                hash_path=hash_path,
                root=root,
            )
            second = build_private_index_dry_run(
                load_json(summary_path),
                load_json(hash_path),
                summary_path=summary_path,
                hash_path=hash_path,
                root=root,
            )

            self.assertEqual(first, second)
            self.assertEqual(INDEX_DRY_RUN_SCHEMA_VERSION, first["schema_version"])
            self.assertEqual("dry_run", first["private_index_construction_mode"])
            self.assertEqual(1, first["record_count"])
            self.assertTrue(first["summary_digest_present"])
            for field in FALSE_SAFETY_FIELDS:
                with self.subTest(field=field):
                    self.assertIs(first[field], False)

    def test_expected_fixture_matches_synthetic_inputs(self) -> None:
        with _fake_repo() as root:
            summary_path, hash_path = _write_valid_inputs(root)
            output = build_private_index_dry_run(
                load_json(summary_path),
                load_json(hash_path),
                summary_path=summary_path,
                hash_path=hash_path,
                root=root,
            )

            self.assertEqual(load_json(EXPECTED_FIXTURE), output)

    def test_invalid_summary_rejected(self) -> None:
        with _fake_repo() as root:
            summary = _fixture_summary()
            summary["schema_version"] = "wrong"
            summary_path, hash_path = _write_valid_inputs(root)
            write_summary(summary, summary_path)

            with self.assertRaises(PrivateIndexBuilderDryRunError):
                build_private_index_dry_run(
                    load_json(summary_path),
                    load_json(hash_path),
                    summary_path=summary_path,
                    hash_path=hash_path,
                    root=root,
                )

    def test_missing_or_blocked_summary_rejected(self) -> None:
        with _fake_repo() as root:
            for field, value in (
                ("input_exists", False),
                ("input_kind", "missing"),
                ("blocker_categories", ["manual_blocker"]),
            ):
                with self.subTest(field=field):
                    summary = _fixture_summary()
                    summary[field] = value
                    summary_path, hash_path = _write_valid_inputs(root)
                    write_summary(summary, summary_path)
                    errors = collect_index_source_errors(
                        load_json(summary_path),
                        load_json(hash_path),
                        summary_path=summary_path,
                        hash_path=hash_path,
                        root=root,
                    )

                    self.assertNotEqual([], errors)

    def test_invalid_hash_rejected(self) -> None:
        with _fake_repo() as root:
            summary_path, hash_path = _write_valid_inputs(root)
            hash_output = load_json(hash_path)
            hash_output["digest"] = "not-a-sha"
            write_hash_summary(hash_output, hash_path)

            with self.assertRaises(PrivateIndexBuilderDryRunError):
                build_private_index_dry_run(
                    load_json(summary_path),
                    load_json(hash_path),
                    summary_path=summary_path,
                    hash_path=hash_path,
                    root=root,
                )

    def test_input_paths_outside_private_roots_rejected(self) -> None:
        with _fake_repo() as root:
            outside_summary = root / "workspace/synthetic-slice/summary.json"
            outside_summary.parent.mkdir(parents=True)
            outside_summary.write_text(json.dumps(_fixture_summary()), encoding="utf-8")
            outside_hash = root / "workspace/local-private/extraction-indexing/hashish/hash.json"
            outside_hash.parent.mkdir(parents=True)
            outside_hash.write_text("{}", encoding="utf-8")

            with self.assertRaises(PrivateIndexBuilderDryRunError):
                resolve_summary_input_path(outside_summary, root=root)
            with self.assertRaises(PrivateIndexBuilderDryRunError):
                resolve_hash_input_path(outside_hash, root=root)

    def test_output_path_outside_index_root_rejected(self) -> None:
        with _fake_repo() as root:
            for output in (
                Path(PRIVATE_OUTPUT_ROOT) / "index.json",
                Path("workspace/synthetic-slice/index.json"),
                Path("../workspace/local-private/extraction-indexing/index/index.json"),
            ):
                with self.subTest(output=output):
                    with self.assertRaises(PrivateIndexBuilderDryRunError):
                        resolve_output_path(output, root=root)

    def test_raw_markers_and_private_fields_are_rejected(self) -> None:
        with _fake_repo() as root:
            for field, value in (
                ("filename", "private-name.txt"),
                ("raw_payload", "payload dump"),
                ("free_text_evidence", "LogOutput.log"),
            ):
                with self.subTest(field=field):
                    summary = _fixture_summary()
                    summary[field] = value
                    summary_path, hash_path = _write_valid_inputs(root)
                    write_summary(summary, summary_path)
                    errors = collect_index_source_errors(
                        load_json(summary_path),
                        load_json(hash_path),
                        summary_path=summary_path,
                        hash_path=hash_path,
                        root=root,
                    )

                    self.assertNotEqual([], errors)

    def test_no_file_contents_or_private_paths_in_output(self) -> None:
        with _fake_repo() as root:
            summary_path, hash_path = _write_valid_inputs(root)
            output = build_private_index_dry_run(
                load_json(summary_path),
                load_json(hash_path),
                summary_path=summary_path,
                hash_path=hash_path,
                root=root,
            )
            output_path = resolve_output_path(
                Path(PRIVATE_INDEX_OUTPUT_ROOT) / "index.json",
                root=root,
            )

            write_private_index_dry_run(output, output_path)
            rendered = output_path.read_text(encoding="utf-8")

            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)
            self.assertNotIn('"digest":', rendered)
            self.assertNotIn(
                "407ab5f9a273570973268c05c89ffa825cb580623e07eea1a41987f474c16367", rendered
            )
            self.assertNotIn("private-name.txt", rendered)

    def test_self_test_uses_temp_workspace_only(self) -> None:
        run_self_test()

    def test_cli_self_test_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_private_index_builder_dry_run.py",
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

    def test_check_all_registers_private_index_builder_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_private_index_builder_dry_run.py", text)
        self.assertIn("--self-test", text)


def _fixture_summary() -> dict[str, object]:
    return {
        "schema_version": "private-input-adapter-dry-run-summary.v1",
        "input_exists": True,
        "input_kind": "file",
        "file_count": 1,
        "directory_count": 0,
        "total_size_bytes": 12,
        "allowed_root": "workspace/local-private/extraction-indexing/input/",
        "private_output_root": "workspace/local-private/extraction-indexing/",
        "dry_run": True,
        "hashes_computed": False,
        "traversal_limit": 1000,
        "traversal_truncated": False,
        "blocker_categories": [],
        "output_written": False,
        "paths_redacted": True,
        "file_contents_read": False,
        "real_text_included": False,
        "raw_payloads_included": False,
        "raw_logs_included": False,
        "automatic_game_install_scanning": False,
        "game_files_read": False,
        "bepinex_logs_read": False,
        "game_logs_read": False,
        "screenshots_read": False,
        "ocr_used": False,
        "save_files_read": False,
        "hooks_used": False,
        "unity_scanning_used": False,
        "current_line_capture_used": False,
        "ui_text_reading_used": False,
        "decompiled_code_used": False,
        "companion_contract_changed": False,
        "provider_called": False,
    }


def _write_valid_inputs(
    root: Path,
    *,
    summary: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    summary_path = root / PRIVATE_OUTPUT_ROOT / "summary.json"
    write_summary(summary or _fixture_summary(), summary_path)
    hash_output = build_hash_summary(load_json(summary_path), summary_path=summary_path, root=root)
    hash_path = root / HASH_OUTPUT_ROOT / "hash.json"
    write_hash_summary(hash_output, hash_path)
    return summary_path, hash_path


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
