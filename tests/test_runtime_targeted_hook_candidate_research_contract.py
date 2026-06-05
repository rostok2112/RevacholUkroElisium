from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_runtime_targeted_hook_candidate_research_contract import (
    FIXTURE_PATH,
    RECOMMENDED_NEXT_STEP,
    SELECTED_STRATEGY,
    collect_runtime_targeted_hook_candidate_research_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class RuntimeTargetedHookCandidateResearchContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_runtime_targeted_hook_candidate_research_contract_errors())
        fixture = load_json(FIXTURE_PATH)
        self.assertEqual(SELECTED_STRATEGY, fixture["selected_strategy"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])

    def test_rejects_contract_or_next_step_drift(self) -> None:
        for mutation in (
            {"contract_status": "implementation_ready"},
            {"selected_strategy": "manual_runtime_first"},
            {"recommended_next_step": "runtime_hook_implementation"},
            {"local_research_report_allowed_next": "hook_implementation"},
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
            "tracked_candidate_identifiers_allowed",
            "tracked_method_names_allowed",
            "tracked_method_signatures_allowed",
            "tracked_class_names_allowed",
            "tracked_decompiled_identifiers_allowed",
            "tracked_raw_logs_allowed",
            "screenshots_allowed",
            "source_text_allowed",
            "payload_dumps_allowed",
            "private_paths_allowed",
            "provider_data_allowed",
            "real_runtime_evidence_allowed",
            "ocr_allowed",
            "broad_unity_scanning_allowed",
            "game_file_reads_allowed",
            "bepinex_log_parsing_allowed",
            "provider_execution_allowed",
            "companion_contract_change_allowed",
            "committed_runtime_artifacts_allowed",
        ):
            with self.subTest(field=field):
                payload = load_json(FIXTURE_PATH)
                payload[field] = True
                self.assertNotEqual([], _errors_for_payload(payload))

    def test_rejects_unsafe_root_and_markers(self) -> None:
        payload = load_json(FIXTURE_PATH)
        payload["allowed_private_research_roots"] = ["workspace/runtime-capture/hook-research/"]
        self.assertNotEqual([], _errors_for_payload(payload))

        payload = load_json(FIXTURE_PATH)
        payload["notes"] = (
            "HarmonyPatch public void Candidate(string source_text) LogOutput.log "
            "C:\\Users\\local\\secret screenshot request payload Candidate.Controller"
        )
        errors = "\n".join(_errors_for_payload(payload))
        self.assertIn("HarmonyPatch", errors)
        self.assertIn("method-signature-looking", errors)
        self.assertIn("private absolute path", errors)
        self.assertIn("qualified identifier-looking", errors)

    def test_docs_and_check_all_references_exist(self) -> None:
        self.assertEqual([], collect_runtime_targeted_hook_candidate_research_contract_errors())
        for path in (
            ROOT / "docs/runtime-targeted-hook-candidate-research-contract.md",
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
        self.assertIn(
            "scripts/check_runtime_targeted_hook_candidate_research_contract.py",
            check_all,
        )


def _errors_for_payload(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "runtime-targeted-hook-research-contract.json"
        path.write_text(json.dumps(copy.deepcopy(payload), indent=2), encoding="utf-8")
        return collect_runtime_targeted_hook_candidate_research_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
