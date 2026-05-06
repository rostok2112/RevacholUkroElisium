from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.run_provider_contract_regression import (
    DEFAULT_OUTPUT_ROOT,
    SUCCESS_RESPONSE,
    render_markdown_summary,
    resolve_output_path,
    run_provider_contract_regression,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class ProviderContractRegressionTests(unittest.TestCase):
    def test_runner_passes_with_current_fixtures(self) -> None:
        summary = run_provider_contract_regression()

        self.assertTrue(summary["ok"])
        self.assertEqual("provider-contract-regression.v1", summary["schema_version"])
        self.assertTrue(summary["mode"]["offline"])
        self.assertTrue(summary["mode"]["mock"])
        self.assertTrue(summary["mode"]["synthetic_only"])
        self.assertFalse(summary["mode"]["external_services"])
        self.assertTrue(summary["server"]["started"])
        self.assertTrue(summary["server"]["shutdown"])
        self.assertEqual(["fake_event", "context_packet"], _case_ids(summary))
        self.assertTrue(all(case["ok"] for case in summary["cases"]))
        self.assertTrue(all(not case["stable_diffs"] for case in summary["cases"]))

    def test_runner_exercises_both_request_fixture_shapes(self) -> None:
        summary = run_provider_contract_regression()

        cases = {case["case_id"]: case for case in summary["cases"]}
        self.assertEqual("fake_event", cases["fake_event"]["input_type"])
        self.assertEqual("context_packet", cases["context_packet"]["input_type"])
        self.assertEqual(200, cases["fake_event"]["http_status"])
        self.assertEqual(200, cases["context_packet"]["http_status"])

    def test_drift_detection_catches_missing_stable_provider_metadata(self) -> None:
        expected = load_json(SUCCESS_RESPONSE)
        expected["data"]["annotation_card"]["provider_debug"].pop("provider_name")

        with tempfile.TemporaryDirectory() as temp_dir:
            success_path = Path(temp_dir) / "provider_annotate.success_response.synthetic.json"
            success_path.write_text(
                json.dumps(expected, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            summary = run_provider_contract_regression(success_response_path=success_path)

        self.assertFalse(summary["ok"])
        diff_paths = _diff_paths(summary)
        self.assertIn("data.annotation_card.provider_debug", diff_paths)

    def test_schema_validation_failure_is_reported_clearly(self) -> None:
        expected = load_json(SUCCESS_RESPONSE)
        expected["data"]["annotation_card"]["quality"] = "not an object"

        with tempfile.TemporaryDirectory() as temp_dir:
            success_path = Path(temp_dir) / "provider_annotate.success_response.synthetic.json"
            success_path.write_text(
                json.dumps(expected, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            summary = run_provider_contract_regression(success_response_path=success_path)

        self.assertFalse(summary["ok"])
        errors = "\n".join(summary["fixture_validation"]["errors"])
        self.assertIn("success fixture annotation_card schema errors", errors)
        self.assertIn("quality", errors)

    def test_unsafe_output_paths_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_path(Path("docs/provider-contract-summary.json"))

    def test_safe_output_paths_resolve_under_provider_contract_workspace(self) -> None:
        path = resolve_output_path(
            Path("workspace/synthetic-slice/provider-contract/summary-test.json")
        )

        self.assertTrue(_is_relative_to(path, DEFAULT_OUTPUT_ROOT))

    def test_cli_writes_json_markdown_and_review_outputs(self) -> None:
        output = DEFAULT_OUTPUT_ROOT / "summary-test.json"
        markdown = DEFAULT_OUTPUT_ROOT / "summary-test.md"
        review_fake = DEFAULT_OUTPUT_ROOT / "review.fake_event.html"
        review_context = DEFAULT_OUTPUT_ROOT / "review.context_packet.html"
        for path in (output, markdown, review_fake, review_context):
            if path.exists():
                path.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_contract_regression.py",
                "--output",
                "workspace/synthetic-slice/provider-contract/summary-test.json",
                "--markdown",
                "workspace/synthetic-slice/provider-contract/summary-test.md",
                "--write-review-html",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("", completed.stdout)
        written_summary = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(written_summary["ok"])
        self.assertIn("Status: PASS", markdown.read_text(encoding="utf-8"))
        self.assertIn("Revachol Synthetic Review", review_fake.read_text(encoding="utf-8"))
        self.assertIn("Revachol Synthetic Review", review_context.read_text(encoding="utf-8"))
        for path in (output, markdown, review_fake, review_context):
            self.assertTrue(_is_relative_to(path, DEFAULT_OUTPUT_ROOT))
            path.unlink()

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_contract_regression.py",
                "--output",
                "docs/provider-contract-summary.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)

    def test_default_cli_stdout_is_json_summary(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_provider_contract_regression.py"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual("provider-contract-regression.v1", payload["schema_version"])

    def test_markdown_summary_is_deterministic_and_compact(self) -> None:
        summary = run_provider_contract_regression()
        first = render_markdown_summary(summary)
        second = render_markdown_summary(summary)

        self.assertEqual(first, second)
        self.assertIn("Status: PASS", first)
        self.assertIn("`fake_event`: PASS", first)
        self.assertIn("`context_packet`: PASS", first)

    def test_runner_summary_contains_no_external_service_or_secret_markers(self) -> None:
        summary = run_provider_contract_regression()
        rendered = json.dumps(summary, ensure_ascii=True).lower()

        for forbidden in (
            "http://",
            "https://",
            "steamapps",
            "openai",
            "deepl",
            "anthropic",
            "api_key",
            "api-key",
            "secret",
            "token",
            "password",
            "data/extracted",
            "data/local",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, rendered)


def _case_ids(summary: dict[str, object]) -> list[str]:
    return [case["case_id"] for case in summary["cases"]]  # type: ignore[index]


def _diff_paths(summary: dict[str, object]) -> list[str]:
    paths: list[str] = []
    for case in summary["cases"]:  # type: ignore[index]
        for diff in case["stable_diffs"]:
            paths.append(diff["path"])
    return paths


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
