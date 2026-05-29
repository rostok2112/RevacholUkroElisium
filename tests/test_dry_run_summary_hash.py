from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_dry_run_summary_hash import (
    FALSE_OUTPUT_FIELDS,
    HASH_INPUT_KIND,
    HASH_OUTPUT_ROOT,
    HASH_SCHEMA_VERSION,
    DryRunSummaryHashError,
    build_hash_summary,
    canonical_summary_json,
    canonicalize_summary,
    collect_hash_source_errors,
    resolve_hash_output_path,
    resolve_summary_path,
    run_self_test,
    write_hash_summary,
)
from scripts.run_private_input_adapter_dry_run import PRIVATE_OUTPUT_ROOT, write_summary
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FIXTURE = ROOT / "tests/fixtures/dry_run_summary_hash.synthetic.json"
PRIVATE_CONTENT = "PRIVATE_CONTENT_SHOULD_NOT_LEAK"


class DryRunSummaryHashTests(unittest.TestCase):
    def test_valid_dry_run_summary_hashes_deterministically(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_summary(root, _fixture_summary())
            first = build_hash_summary(
                load_json(summary_path), summary_path=summary_path, root=root
            )
            second = build_hash_summary(
                load_json(summary_path), summary_path=summary_path, root=root
            )

            self.assertEqual(first, second)
            self.assertEqual(HASH_SCHEMA_VERSION, first["schema_version"])
            self.assertEqual("sha256", first["hash_algorithm"])
            self.assertEqual(HASH_INPUT_KIND, first["hash_input_kind"])
            self.assertTrue(first["summary_hash_computed"])
            self.assertEqual(64, len(first["digest"]))
            for field in FALSE_OUTPUT_FIELDS:
                with self.subTest(field=field):
                    self.assertIs(first[field], False)

    def test_expected_fixture_matches_synthetic_summary(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_summary(root, _fixture_summary())
            output = build_hash_summary(
                load_json(summary_path), summary_path=summary_path, root=root
            )

            self.assertEqual(load_json(EXPECTED_FIXTURE), output)

    def test_field_order_does_not_affect_hash(self) -> None:
        with _fake_repo() as root:
            summary = _fixture_summary()
            reversed_summary = dict(reversed(list(summary.items())))
            first_path = _write_summary(root, summary, name="first.json")
            second_path = _write_summary(root, reversed_summary, name="second.json")

            first = build_hash_summary(load_json(first_path), summary_path=first_path, root=root)
            second = build_hash_summary(load_json(second_path), summary_path=second_path, root=root)

            self.assertEqual(first["digest"], second["digest"])

    def test_blocker_categories_are_sorted_before_hashing(self) -> None:
        summary = _fixture_summary()
        summary["blocker_categories"] = ["zeta", "alpha"]
        reversed_summary = dict(summary)
        reversed_summary["blocker_categories"] = ["alpha", "zeta"]

        self.assertEqual(
            canonical_summary_json(canonicalize_summary(summary)),
            canonical_summary_json(canonicalize_summary(reversed_summary)),
        )

    def test_rejects_hashes_computed_true_in_source_summary(self) -> None:
        with _fake_repo() as root:
            summary = _fixture_summary()
            summary["hashes_computed"] = True
            path = _write_summary(root, summary)

            with self.assertRaises(DryRunSummaryHashError):
                build_hash_summary(load_json(path), summary_path=path, root=root)

    def test_rejects_excluded_or_unknown_fields(self) -> None:
        with _fake_repo() as root:
            for field, value in (
                ("input_path", "workspace/local-private/extraction-indexing/input/private"),
                ("filename", "private-name.txt"),
                ("raw_payload", "redacted but still forbidden"),
                ("unexpected_note", "extra data"),
            ):
                with self.subTest(field=field):
                    summary = _fixture_summary()
                    summary[field] = value
                    path = _write_summary(root, summary, name=f"{field}.json")

                    errors = collect_hash_source_errors(
                        load_json(path), summary_path=path, root=root
                    )

                    self.assertNotEqual([], errors)

    def test_rejects_raw_marker_values(self) -> None:
        with _fake_repo() as root:
            for marker in ("raw payload dump", "LogOutput.log", "screenshot archive"):
                with self.subTest(marker=marker):
                    summary = _fixture_summary()
                    summary["blocker_categories"] = [marker]
                    path = _write_summary(root, summary, name="marker.json")

                    errors = collect_hash_source_errors(
                        load_json(path), summary_path=path, root=root
                    )

                    self.assertNotEqual([], errors)

    def test_summary_outside_private_root_rejected(self) -> None:
        with _fake_repo() as root:
            outside = root / "workspace/synthetic-slice/summary.json"
            outside.parent.mkdir(parents=True)
            outside.write_text(json.dumps(_fixture_summary()), encoding="utf-8")

            with self.assertRaises(DryRunSummaryHashError):
                resolve_summary_path(outside, root=root)

    def test_hash_output_path_outside_hash_root_rejected(self) -> None:
        with _fake_repo() as root:
            for output in (
                Path(PRIVATE_OUTPUT_ROOT) / "hash.json",
                Path("workspace/synthetic-slice/hash.json"),
                Path("../workspace/local-private/extraction-indexing/hash/hash.json"),
            ):
                with self.subTest(output=output):
                    with self.assertRaises(DryRunSummaryHashError):
                        resolve_hash_output_path(output, root=root)

    def test_output_is_redacted_and_written_only_under_hash_root(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_summary(root, _fixture_summary())
            output = build_hash_summary(
                load_json(summary_path), summary_path=summary_path, root=root
            )
            output_path = resolve_hash_output_path(
                Path(HASH_OUTPUT_ROOT) / "hash.json",
                root=root,
            )

            write_hash_summary(output, output_path)
            rendered = output_path.read_text(encoding="utf-8")

            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)
            self.assertNotIn("input_path", rendered)

    def test_file_contents_are_never_read(self) -> None:
        with _fake_repo() as root:
            summary_path = _write_summary(root, _fixture_summary())
            output = build_hash_summary(
                load_json(summary_path), summary_path=summary_path, root=root
            )

            rendered = json.dumps(output, sort_keys=True)

            self.assertFalse(output["file_contents_read"])
            self.assertFalse(output["original_private_input_read"])
            self.assertNotIn(PRIVATE_CONTENT, rendered)

    def test_self_test_uses_temp_workspace_only(self) -> None:
        run_self_test()

    def test_cli_self_test_quiet(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_dry_run_summary_hash.py", "--self-test", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn(PRIVATE_CONTENT, completed.stdout)

    def test_cli_self_test_output_is_redacted(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_dry_run_summary_hash.py", "--self-test"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("dry-run-summary-hash-self-test.v1", completed.stdout)
        self.assertNotIn(PRIVATE_CONTENT, completed.stdout)

    def test_check_all_registers_hash_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_dry_run_summary_hash.py", text)
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


def _write_summary(root: Path, summary: dict[str, object], *, name: str = "summary.json") -> Path:
    summary_path = root / PRIVATE_OUTPUT_ROOT / name
    write_summary(summary, summary_path)
    return summary_path


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
