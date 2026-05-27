from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.check_extraction_index_contract import collect_extraction_index_contract_errors
from scripts.run_synthetic_extraction_indexer import (
    DEFAULT_OUTPUT_ROOT,
    EXPECTED_INDEX_FIXTURE,
    INDEX_SCHEMA_VERSION,
    PRIVATE_INDEX_ROOT,
    SOURCE_FIXTURE,
    build_extraction_index,
    build_summary,
    load_source_records,
    resolve_output_path,
    validate_extraction_index,
    validate_source_records,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class SyntheticExtractionIndexerTests(unittest.TestCase):
    def test_source_fixture_validates(self) -> None:
        source = load_source_records(SOURCE_FIXTURE)

        self.assertEqual("extraction-index-source-records.v1", source["schema_version"])
        self.assertTrue(source["generated_from_synthetic_fixture"])
        self.assertEqual(3, len(source["records"]))

    def test_expected_index_fixture_matches_generated_output(self) -> None:
        source = load_source_records(SOURCE_FIXTURE)
        generated = build_extraction_index(source, source_path=SOURCE_FIXTURE)
        expected = load_json(EXPECTED_INDEX_FIXTURE)

        self.assertEqual(expected, generated)
        validate_extraction_index(generated, source)

    def test_index_fixture_shape_is_private_and_synthetic(self) -> None:
        index = load_json(EXPECTED_INDEX_FIXTURE)

        self.assertEqual(INDEX_SCHEMA_VERSION, index["schema_version"])
        self.assertTrue(index["generated_from_synthetic_fixture"])
        self.assertEqual(PRIVATE_INDEX_ROOT, index["private_index_root"])
        self.assertEqual(index["record_count"], len(index["records"]))
        self.assertGreater(len(index["terms"]), 0)
        self.assertFalse(index["safety_flags"]["real_game_text_included"])
        self.assertFalse(index["safety_flags"]["automatic_game_install_scanning"])
        self.assertFalse(index["safety_flags"]["provider_called"])

    def test_summary_is_redacted(self) -> None:
        source = load_source_records(SOURCE_FIXTURE)
        index = build_extraction_index(source, source_path=SOURCE_FIXTURE)
        summary = build_summary(index, output_written=False)
        rendered = json.dumps(summary, ensure_ascii=False)

        self.assertNotIn("brass kettle", rendered)
        self.assertFalse(summary["real_game_text_included"])
        self.assertFalse(summary["raw_payloads_included"])
        self.assertFalse(summary["game_files_read"])

    def test_output_path_allows_private_workspace_root(self) -> None:
        output = resolve_output_path(Path("workspace/local-private/extraction-indexing/test.json"))

        self.assertTrue(_is_relative_to(output, DEFAULT_OUTPUT_ROOT))

    def test_output_path_rejects_public_or_wrong_paths(self) -> None:
        for path in (
            Path("docs/extraction-index.json"),
            Path("workspace/synthetic-slice/extraction-indexing/index.json"),
            Path("../workspace/local-private/extraction-indexing/index.json"),
        ):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    resolve_output_path(path)

    def test_source_rejects_unsafe_markers(self) -> None:
        for marker in (
            "LogOutput.log",
            "raw payload dump",
            "https://example.invalid",
            "api_key=secret",
            "C:\\Users\\local\\secret",
            "current-line capture approved",
        ):
            with self.subTest(marker=marker):
                source = _source_copy()
                source["records"][0]["source_text"] = marker

                with self.assertRaisesRegex(Exception, "contains"):
                    validate_source_records(source)

    def test_index_rejects_unsafe_markers(self) -> None:
        source = load_source_records(SOURCE_FIXTURE)
        index = build_extraction_index(source, source_path=SOURCE_FIXTURE)
        index["records"][0]["context_tags"].append("raw log")

        with self.assertRaisesRegex(Exception, "forbidden marker"):
            validate_extraction_index(index, source)

    def test_contract_checker_passes(self) -> None:
        self.assertEqual([], collect_extraction_index_contract_errors())

    def test_check_all_registers_contract_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_extraction_index_contract.py", text)

    def test_cli_check_fixture_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_synthetic_extraction_indexer.py",
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
        self.assertNotIn("brass kettle", completed.stdout.lower())

    def test_cli_writes_only_private_workspace_output(self) -> None:
        output = ROOT / "workspace/local-private/extraction-indexing/unit-test-index.json"
        if output.exists():
            output.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_synthetic_extraction_indexer.py",
                "--output",
                "workspace/local-private/extraction-indexing/unit-test-index.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(output.exists())
        written = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(INDEX_SCHEMA_VERSION, written["schema_version"])
        output.unlink()

    def test_cli_rejects_unsafe_output(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_synthetic_extraction_indexer.py",
                "--output",
                "docs/index.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)

    def test_contract_checker_cli_quiet(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/check_extraction_index_contract.py", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout.lower())


def _source_copy() -> dict[str, object]:
    return copy.deepcopy(load_json(SOURCE_FIXTURE))


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
