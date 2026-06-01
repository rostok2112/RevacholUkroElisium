from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_m2_synthetic_line_index_builder_dry_run import (
    EXPECTED_INDEX_FIXTURE,
    PRIVATE_OUTPUT_ROOT,
    SOURCE_FIXTURE,
    M2SyntheticLineIndexBuilderDryRunError,
    assert_valid_m2_synthetic_line_index,
    build_m2_synthetic_line_index,
    build_summary,
    resolve_output_path,
    write_m2_synthetic_line_index,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M2SyntheticLineIndexBuilderDryRunTests(unittest.TestCase):
    def test_generated_index_matches_contract_fixture(self) -> None:
        source = load_json(SOURCE_FIXTURE)

        generated = build_m2_synthetic_line_index(source)

        self.assertEqual(load_json(EXPECTED_INDEX_FIXTURE), generated)
        assert_valid_m2_synthetic_line_index(generated, source)

    def test_source_order_does_not_change_output(self) -> None:
        source = load_json(SOURCE_FIXTURE)
        reversed_source = copy.deepcopy(source)
        reversed_source["records"].reverse()

        self.assertEqual(
            build_m2_synthetic_line_index(source),
            build_m2_synthetic_line_index(reversed_source),
        )

    def test_output_is_metadata_only(self) -> None:
        source = load_json(SOURCE_FIXTURE)
        output = build_m2_synthetic_line_index(source)
        summary = build_summary(output, output_written=False)
        rendered_entries = json.dumps(output["entries"], sort_keys=True).lower()

        for forbidden in (
            "the paper umbrella requested",
            "context_edges",
            "source_text",
            "filename",
            '"paths_included": true',
            '"hashes_included": true',
            "raw payload",
            "logoutput.log",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered_entries)
        self.assertFalse(summary["private_input_read"])
        self.assertFalse(summary["game_files_read"])

    def test_tampered_index_is_rejected(self) -> None:
        source = load_json(SOURCE_FIXTURE)
        output = build_m2_synthetic_line_index(source)
        output["entries"][0]["context_tags"].append("unexpected")

        with self.assertRaises(M2SyntheticLineIndexBuilderDryRunError):
            assert_valid_m2_synthetic_line_index(output, source)

    def test_invalid_explicit_source_is_rejected_by_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source_path = Path(tmp_dir) / "invalid.json"
            source_path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_m2_synthetic_line_index_builder_dry_run.py",
                    "--source",
                    str(source_path),
                    "--quiet",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(0, completed.returncode)
        self.assertNotIn(str(source_path), completed.stderr)

    def test_output_path_allows_only_private_line_index_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            allowed = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "index.json", root=root)
            self.assertEqual(root / PRIVATE_OUTPUT_ROOT / "index.json", allowed)

            for unsafe in (
                Path("docs/index.json"),
                Path("workspace/local-private/extraction-indexing/import/index.json"),
                Path("../workspace/local-private/extraction-indexing/import/line-index/index.json"),
            ):
                with self.subTest(unsafe=unsafe):
                    with self.assertRaises(M2SyntheticLineIndexBuilderDryRunError):
                        resolve_output_path(unsafe, root=root)

    def test_write_uses_private_temp_output_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            output_path = resolve_output_path(Path(PRIVATE_OUTPUT_ROOT) / "index.json", root=root)
            write_m2_synthetic_line_index(
                build_m2_synthetic_line_index(load_json(SOURCE_FIXTURE)),
                output_path,
            )

            written = output_path.read_text(encoding="utf-8")
            self.assertNotIn("The paper umbrella requested", written)
            self.assertNotIn('"context_edges":', written)

    def test_cli_check_fixture_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_m2_synthetic_line_index_builder_dry_run.py",
                "--check-fixture",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())
        self.assertNotIn("paper umbrella", completed.stdout.lower())

    def test_check_all_registers_builder_smoke(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_m2_synthetic_line_index_builder_dry_run.py", text)
        self.assertIn("--check-fixture", text)


if __name__ == "__main__":
    unittest.main()
