from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.review_m2_explicit_local_import_adapter_dry_run import (
    DECISION_FALSE_FIELDS,
    DECISION_FIXTURE_PATH,
    RECOMMENDED_REPEAT_DRY_RUN_STEP,
    RECOMMENDED_SCHEMA_CONTRACT_STEP,
    REVIEW_OUTPUT_ROOT,
    REVIEW_SCHEMA_VERSION,
    M2ExplicitLocalImportAdapterDryRunReviewError,
    build_review,
    collect_decision_fixture_errors,
    collect_summary_errors,
    resolve_review_output_path,
    resolve_summary_input_path,
    run_self_test,
    write_json_review,
    write_markdown_review,
)
from scripts.run_m2_explicit_local_import_adapter_dry_run import (
    PRIVATE_INPUT_ROOT,
    PRIVATE_OUTPUT_ROOT,
    build_m2_explicit_local_import_adapter_dry_run,
    write_summary,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_CONTENT = "PRIVATE_EXPORT_CONTENT_SHOULD_NOT_LEAK"


class M2ExplicitLocalImportAdapterDryRunReviewTests(unittest.TestCase):
    def test_valid_summary_reviews_after_private_export_is_removed(self) -> None:
        with _fake_repo() as root:
            summary_path, private_file = _write_valid_summary(root)
            private_file.unlink()

            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            rendered = json.dumps(review, sort_keys=True)

            self.assertEqual(REVIEW_SCHEMA_VERSION, review["schema_version"])
            self.assertTrue(review["summary_valid"])
            self.assertTrue(review["input_exists"])
            self.assertEqual("file", review["input_kind"])
            self.assertTrue(review["metadata_only"])
            self.assertTrue(review["ready_for_schema_compatibility_contract_decision"])
            self.assertFalse(review["schema_compatibility_inspection_allowed_next"])
            self.assertFalse(review["private_export_reopened"])
            self.assertEqual(RECOMMENDED_SCHEMA_CONTRACT_STEP, review["recommended_next_step"])
            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)

    def test_malformed_summary_is_rejected_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path, _private_file = _write_valid_summary(root)
            payload = load_json(summary_path)
            payload["schema_version"] = "wrong"

            review = build_review(payload, summary_path=summary_path, root=root)

            self.assertFalse(review["summary_valid"])
            self.assertFalse(review["ready_for_schema_compatibility_contract_decision"])
            self.assertIn("malformed_summary", review["blockers"])

    def test_missing_input_summary_is_safe_but_not_ready(self) -> None:
        with _fake_repo() as root:
            summary = build_m2_explicit_local_import_adapter_dry_run(
                Path(PRIVATE_INPUT_ROOT) / "missing.json",
                root=root,
            )
            summary_path = root / PRIVATE_OUTPUT_ROOT / "missing-summary.json"
            write_summary(summary, summary_path)

            review = build_review(summary, summary_path=summary_path, root=root)

            self.assertTrue(review["summary_valid"])
            self.assertFalse(review["input_exists"])
            self.assertIn("input_missing", review["blockers"])
            self.assertFalse(review["ready_for_schema_compatibility_contract_decision"])
            self.assertEqual(RECOMMENDED_REPEAT_DRY_RUN_STEP, review["recommended_next_step"])

    def test_directory_blocker_is_safe_but_not_ready(self) -> None:
        with _fake_repo() as root:
            selected = root / PRIVATE_INPUT_ROOT / "directory"
            selected.mkdir(parents=True)
            summary = build_m2_explicit_local_import_adapter_dry_run(
                Path(PRIVATE_INPUT_ROOT) / "directory",
                root=root,
            )
            summary_path = root / PRIVATE_OUTPUT_ROOT / "directory-summary.json"
            write_summary(summary, summary_path)

            review = build_review(summary, summary_path=summary_path, root=root)

            self.assertTrue(review["summary_valid"])
            self.assertIn("directory_input_rejected", review["blockers"])
            self.assertFalse(review["ready_for_schema_compatibility_contract_decision"])

    def test_summary_outside_private_root_rejected(self) -> None:
        with _fake_repo() as root:
            outside = root / "workspace/synthetic-slice/summary.json"
            outside.parent.mkdir(parents=True)
            outside.write_text("{}", encoding="utf-8")

            with self.assertRaises(M2ExplicitLocalImportAdapterDryRunReviewError):
                resolve_summary_input_path(outside, root=root)

    def test_review_output_outside_review_root_rejected(self) -> None:
        with _fake_repo() as root:
            for path in (
                Path(PRIVATE_OUTPUT_ROOT) / "review.json",
                Path("workspace/synthetic-slice/review.json"),
                Path(REVIEW_OUTPUT_ROOT) / "../review.json",
            ):
                with self.subTest(path=path):
                    with self.assertRaises(M2ExplicitLocalImportAdapterDryRunReviewError):
                        resolve_review_output_path(path, root=root)

    def test_json_and_markdown_reviews_are_redacted(self) -> None:
        with _fake_repo() as root:
            summary_path, private_file = _write_valid_summary(root)
            private_file.unlink()
            review = build_review(load_json(summary_path), summary_path=summary_path, root=root)
            json_path = resolve_review_output_path(
                Path(REVIEW_OUTPUT_ROOT) / "review.json",
                root=root,
            )
            markdown_path = resolve_review_output_path(
                Path(REVIEW_OUTPUT_ROOT) / "review.md",
                root=root,
            )

            write_json_review(review, json_path)
            write_markdown_review(review, markdown_path)
            rendered = json_path.read_text(encoding="utf-8") + markdown_path.read_text(
                encoding="utf-8"
            )

            self.assertNotIn(PRIVATE_CONTENT, rendered)
            self.assertNotIn(str(root), rendered)
            self.assertNotIn("selected-export.json", rendered)
            self.assertIn("schema_compatibility_inspection_allowed_next: no", rendered)

    def test_unsafe_marker_and_true_safety_flag_are_rejected(self) -> None:
        with _fake_repo() as root:
            summary_path, _private_file = _write_valid_summary(root)
            for field, value in (
                ("unsafe_note", "raw payload dump"),
                ("private_content_parsed", True),
                ("schema_status", "compatible"),
            ):
                with self.subTest(field=field):
                    payload = load_json(summary_path)
                    payload[field] = value
                    errors = collect_summary_errors(payload, summary_path=summary_path, root=root)
                    self.assertNotEqual([], errors)

    def test_decision_fixture_is_safe(self) -> None:
        payload = load_json(DECISION_FIXTURE_PATH)

        self.assertEqual([], collect_decision_fixture_errors())
        self.assertEqual("M2", payload["roadmap_milestone"])
        self.assertEqual(RECOMMENDED_SCHEMA_CONTRACT_STEP, payload["recommended_next_step"])
        for field in DECISION_FALSE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(payload[field], False)

    def test_decision_fixture_rejects_forbidden_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "decision.json"
            payload = load_json(DECISION_FIXTURE_PATH)
            for field in DECISION_FALSE_FIELDS:
                with self.subTest(field=field):
                    mutated = copy.deepcopy(payload)
                    mutated[field] = True
                    path.write_text(json.dumps(mutated), encoding="utf-8")
                    self.assertNotEqual([], collect_decision_fixture_errors(path))

    def test_self_test_uses_temp_workspace_only(self) -> None:
        run_self_test()

    def test_cli_self_test_quiet(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/review_m2_explicit_local_import_adapter_dry_run.py",
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

    def test_check_all_registers_review_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/review_m2_explicit_local_import_adapter_dry_run.py", text)
        self.assertIn("--self-test", text)


def _write_valid_summary(root: Path) -> tuple[Path, Path]:
    private_file = root / PRIVATE_INPUT_ROOT / "selected-export.json"
    private_file.parent.mkdir(parents=True)
    private_file.write_text(PRIVATE_CONTENT, encoding="utf-8")
    summary = build_m2_explicit_local_import_adapter_dry_run(
        Path(PRIVATE_INPUT_ROOT) / "selected-export.json",
        root=root,
    )
    summary_path = root / PRIVATE_OUTPUT_ROOT / "summary.json"
    write_summary(summary, summary_path)
    return summary_path, private_file


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
