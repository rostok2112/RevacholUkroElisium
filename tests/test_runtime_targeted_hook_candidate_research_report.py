from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.check_runtime_targeted_hook_candidate_research_report import (
    FIXTURE_PATH,
    READY_NEXT_STEP,
    REPEAT_NEXT_STEP,
    REPORT_ROOT,
    RuntimeTargetedHookCandidateResearchReportError,
    collect_targeted_hook_candidate_research_report_errors,
    default_report_template,
    ensure_safe_report_path,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class RuntimeTargetedHookCandidateResearchReportTests(unittest.TestCase):
    def test_committed_fixture_validates(self) -> None:
        self.assertEqual([], collect_targeted_hook_candidate_research_report_errors(FIXTURE_PATH))
        fixture = load_json(FIXTURE_PATH)
        self.assertEqual(REPEAT_NEXT_STEP, fixture["recommended_next_step"])

    def test_valid_private_report_advances_to_review_gate(self) -> None:
        report = _ready_report()
        self.assertEqual([], _errors_for(report))

    def test_report_path_bounds(self) -> None:
        self.assertEqual(
            REPORT_ROOT / "report.json",
            ensure_safe_report_path(REPORT_ROOT / "report.json", must_exist=False),
        )
        with self.assertRaises(RuntimeTargetedHookCandidateResearchReportError):
            ensure_safe_report_path(Path("docs/hook-report.json"), must_exist=False)
        with self.assertRaises(RuntimeTargetedHookCandidateResearchReportError):
            ensure_safe_report_path(REPORT_ROOT / "report.txt", must_exist=False)

    def test_rejects_forbidden_flags_true(self) -> None:
        for field in (
            "hook_implementation_used",
            "real_text_capture_used",
            "ui_inspection_used",
            "log_parsing_used",
            "candidate_identifiers_included",
            "method_names_included",
            "method_signatures_included",
            "class_names_included",
            "decompiled_identifiers_included",
            "raw_logs_included",
            "screenshots_included",
            "source_text_included",
            "payload_dumps_included",
            "private_paths_included",
            "provider_data_included",
            "real_runtime_evidence_included",
            "ocr_used",
            "broad_unity_scanning_used",
            "game_file_reads_used",
            "bepinex_log_parsing_used",
            "provider_execution_used",
            "companion_contract_change_used",
            "committed_runtime_artifacts_included",
        ):
            with self.subTest(field=field):
                report = _ready_report()
                report[field] = True
                self.assertNotEqual([], _errors_for(report))

    def test_rejects_unsafe_markers(self) -> None:
        report = _ready_report()
        report["notes_redacted"] = (
            "HarmonyPatch public void Candidate(string source_text) LogOutput.log "
            "C:\\Users\\local\\secret screenshot request payload Candidate.Controller"
        )

        errors = "\n".join(_errors_for(report))

        self.assertIn("HarmonyPatch", errors)
        self.assertIn("method-signature-looking", errors)
        self.assertIn("private absolute path", errors)
        self.assertIn("qualified identifier-looking", errors)

    def test_recommended_next_step_consistency(self) -> None:
        not_run = default_report_template()
        self.assertEqual(REPEAT_NEXT_STEP, not_run["recommended_next_step"])
        self.assertEqual([], _errors_for(not_run))

        ready = _ready_report()
        ready["recommended_next_step"] = REPEAT_NEXT_STEP
        self.assertNotEqual([], _errors_for(ready))

    def test_template_write_stays_private_and_self_test(self) -> None:
        private_output = REPORT_ROOT / "template-unit-test.json"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/check_runtime_targeted_hook_candidate_research_report.py",
                "--write-template",
                str(private_output),
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(private_output.exists())
            self.assertEqual(
                [], collect_targeted_hook_candidate_research_report_errors(private_output)
            )
        finally:
            private_output.unlink(missing_ok=True)

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/check_runtime_targeted_hook_candidate_research_report.py",
                "--self-test",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_check_all_registration(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        self.assertIn(
            "scripts/check_runtime_targeted_hook_candidate_research_report.py",
            text,
        )


def _ready_report() -> dict[str, object]:
    report = copy.deepcopy(default_report_template())
    report.update(
        {
            "research_status": "pass",
            "research_performed_locally": True,
            "candidate_count": 2,
            "candidate_categories_count": 1,
            "evidence_summary": "Local targeted research was summarized as aggregate counts.",
            "recommended_next_step": READY_NEXT_STEP,
        }
    )
    return report


def _errors_for(report: dict[str, object]) -> list[str]:
    path = REPORT_ROOT / "unit-test-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(copy.deepcopy(report), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    try:
        return collect_targeted_hook_candidate_research_report_errors(path)
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
