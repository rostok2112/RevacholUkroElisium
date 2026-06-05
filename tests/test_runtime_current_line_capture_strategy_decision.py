from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_runtime_current_line_capture_strategy_decision import (
    FIXTURE_PATH,
    RECOMMENDED_NEXT_STEP,
    SELECTED_STRATEGY,
    collect_runtime_current_line_capture_strategy_decision_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class RuntimeCurrentLineCaptureStrategyDecisionTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_runtime_current_line_capture_strategy_decision_errors())
        fixture = load_json(FIXTURE_PATH)
        self.assertEqual(SELECTED_STRATEGY, fixture["selected_strategy"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])

    def test_rejects_strategy_or_next_step_drift(self) -> None:
        for mutation in (
            {"selected_strategy": "manual_runtime_first"},
            {"recommended_next_step": "runtime_hook_implementation"},
            {"targeted_hook_candidate_research_contract_allowed_next": True},
        ):
            with self.subTest(mutation=mutation):
                payload = load_json(FIXTURE_PATH)
                payload.update(mutation)
                self.assertNotEqual([], _errors_for_payload(payload))

    def test_rejects_enabled_implementation_and_capture_flags(self) -> None:
        for field in (
            "implementation_allowed_next",
            "hook_implementation_allowed_next",
            "real_text_capture_allowed_next",
            "broad_unity_scanning_allowed_next",
            "ocr_allowed_next",
            "screenshots_allowed_next",
            "save_file_reads_allowed_next",
            "game_file_reads_allowed_next",
            "bepinex_log_parsing_allowed_next",
            "provider_execution_allowed_next",
            "companion_contract_change_allowed_next",
            "decompiled_identifiers_in_tracked_docs_allowed",
            "raw_logs_allowed",
            "payload_dumps_allowed",
            "private_paths_allowed",
            "committed_runtime_evidence_allowed",
        ):
            with self.subTest(field=field):
                payload = load_json(FIXTURE_PATH)
                payload[field] = True
                self.assertNotEqual([], _errors_for_payload(payload))

    def test_rejects_unsafe_root_and_markers(self) -> None:
        payload = load_json(FIXTURE_PATH)
        payload["allowed_private_research_roots"] = ["workspace/hook-research/"]
        self.assertNotEqual([], _errors_for_payload(payload))

        payload = load_json(FIXTURE_PATH)
        payload["notes"] = (
            "HarmonyPatch public void Candidate(string source_text) LogOutput.log "
            "C:\\Users\\local\\secret screenshot request payload"
        )
        errors = "\n".join(_errors_for_payload(payload))
        self.assertIn("HarmonyPatch", errors)
        self.assertIn("method-signature-looking", errors)
        self.assertIn("private absolute path", errors)

    def test_docs_and_check_all_references_exist(self) -> None:
        self.assertEqual([], collect_runtime_current_line_capture_strategy_decision_errors())
        for path in (
            ROOT / "docs/runtime-current-line-capture-strategy-decision.md",
            ROOT / "docs/adr/0008-current-line-capture-research.md",
            ROOT / "docs/devlog/SESSION_SUMMARY.md",
            ROOT / "docs/devlog/NEXT_ACTIONS.md",
            ROOT / "docs/devlog/KNOWN_RISKS.md",
            ROOT / "docs/devlog/DECISIONS_PENDING.md",
        ):
            text = path.read_text(encoding="utf-8")
            self.assertIn(SELECTED_STRATEGY, text)
            self.assertIn(RECOMMENDED_NEXT_STEP, text)

        check_all = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        self.assertIn("scripts/check_runtime_current_line_capture_strategy_decision.py", check_all)


def _errors_for_payload(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "runtime-capture-strategy.json"
        path.write_text(json.dumps(copy.deepcopy(payload), indent=2), encoding="utf-8")
        return collect_runtime_current_line_capture_strategy_decision_errors(path)


if __name__ == "__main__":
    unittest.main()
