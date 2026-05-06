from pathlib import Path
import json
import subprocess
import sys
import unittest

from scripts.run_synthetic_eval import ROOT, resolve_output_path
from scripts.synthetic_eval import (
    SCORE_KEYS,
    get_synthetic_eval_cases,
    run_eval_case,
    run_synthetic_eval,
    score_slice_result,
    validate_eval_case,
)
from scripts.synthetic_review_renderer import render_review_html
from scripts.synthetic_slice import run_synthetic_slice


class SyntheticEvalTests(unittest.TestCase):
    def test_eval_cases_load_and_validate(self) -> None:
        cases = get_synthetic_eval_cases()

        self.assertGreaterEqual(len(cases), 6)
        for case in cases:
            with self.subTest(case=case.case_id):
                validate_eval_case(case)
                self.assertTrue(case.case_id.startswith("synthetic.eval."))
                self.assertTrue(case.fake_event["event_id"].startswith("synthetic.event."))
                self.assertIn("synthetic", json.dumps(case.to_dict()).lower())

    def test_eval_cases_do_not_require_private_paths_or_network(self) -> None:
        forbidden_markers = [
            "data/extracted",
            "data/local",
            ".local-game",
            "private-data",
            "llm-cache",
            "http://",
            "https://",
            "steamapps",
            "database.json",
        ]
        payload = json.dumps([case.to_dict() for case in get_synthetic_eval_cases()]).lower()

        for marker in forbidden_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, payload)

    def test_eval_harness_runs_multiple_cases(self) -> None:
        summary = run_synthetic_eval()

        self.assertTrue(summary["passed"])
        self.assertGreaterEqual(summary["case_count"], 6)
        self.assertEqual(list(SCORE_KEYS), summary["score_keys"])
        self.assertEqual(summary["case_count"], len(summary["results"]))

    def test_scores_are_present_and_deterministic(self) -> None:
        first = run_synthetic_eval()
        second = run_synthetic_eval()

        self.assertEqual(first, second)
        for result in first["results"]:
            with self.subTest(case=result["case_id"]):
                self.assertEqual(set(SCORE_KEYS), set(result["scores"]))
                self.assertEqual(1.0, result["scores"]["section_coverage"])
                self.assertEqual(1.0, result["scores"]["spoiler_safety"])

    def test_missing_sections_and_glossary_reduce_scores(self) -> None:
        case = get_synthetic_eval_cases()[0]
        slice_result = run_synthetic_slice(case.fake_event)
        slice_result["overlay_demo"]["modes"]["deep_explanation"]["sections"] = []
        slice_result["overlay_demo"]["modes"]["deep_explanation"]["glossary_terms"] = []
        slice_result["annotation_card"]["glossary_terms"] = []
        review_html = render_review_html(slice_result)

        result = score_slice_result(case, slice_result, review_html)

        self.assertFalse(result.passed)
        self.assertLess(result.scores["section_coverage"], 1.0)
        self.assertLess(result.scores["glossary_coverage"], 1.0)
        self.assertTrue(any("section_coverage" in failure for failure in result.failures))
        self.assertTrue(any("glossary_coverage" in failure for failure in result.failures))

    def test_each_case_generates_review_html(self) -> None:
        for case in get_synthetic_eval_cases():
            with self.subTest(case=case.case_id):
                result = run_eval_case(case)
                self.assertTrue(result.passed)
                self.assertIn("Revachol Synthetic Review", result.review_html)
                self.assertIn("Compact Mode", result.review_html)
                self.assertIn("Deep Explanation Mode", result.review_html)

    def test_output_path_allows_workspace_synthetic_slice(self) -> None:
        output = resolve_output_path(Path("workspace/synthetic-slice/eval-summary-test.json"))

        self.assertTrue(_is_relative_to(output, ROOT / "workspace/synthetic-slice"))

    def test_output_path_rejects_public_repo_path(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_path(Path("docs/eval-summary.json"))

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_synthetic_eval.py",
                "--output",
                "docs/eval-summary.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)

    def test_cli_writes_summary_under_workspace(self) -> None:
        output = ROOT / "workspace/synthetic-slice/eval-summary-test.json"
        if output.exists():
            output.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_synthetic_eval.py",
                "--output",
                "workspace/synthetic-slice/eval-summary-test.json",
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
        self.assertTrue(written["passed"])
        output.unlink()


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
