from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_m0_closeout import collect_m0_closeout_errors
from scripts.check_m1_closeout import collect_m1_closeout_errors
from scripts.check_milestone_completion_status import (
    FIXTURE_PATH,
    collect_milestone_completion_status_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class MilestoneCompletionStatusTests(unittest.TestCase):
    def test_m0_m1_and_matrix_validate(self) -> None:
        self.assertEqual([], collect_m0_closeout_errors())
        self.assertEqual([], collect_m1_closeout_errors())
        self.assertEqual([], collect_milestone_completion_status_errors())

    def test_matrix_blocks_m5_until_manual_completion(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertFalse(fixture["m5_planning_allowed"])
        self.assertEqual("m2_manual_private_export_verification", fixture["recommended_next_step"])
        self.assertTrue(fixture["milestones"][0]["manual_verification_complete"])
        self.assertTrue(fixture["milestones"][0]["fully_complete"])
        self.assertTrue(fixture["milestones"][1]["manual_verification_complete"])
        self.assertTrue(fixture["milestones"][1]["fully_complete"])
        for entry in fixture["milestones"][2:]:
            self.assertTrue(entry["automated_complete"])
            self.assertTrue(entry["manual_verification_required"])
            self.assertFalse(entry["manual_verification_complete"])
            self.assertFalse(entry["fully_complete"])

    def test_rejects_fully_complete_without_manual_verification(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = copy.deepcopy(fixture)
        mutated["milestones"][2]["fully_complete"] = True

        self.assertNotEqual([], _matrix_errors_for(mutated))

    def test_accepts_m0_complete_and_advances_to_m1_manual_review(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        self.assertEqual([], _matrix_errors_for(copy.deepcopy(fixture)))

    def test_accepts_m1_complete_and_advances_to_m2_manual_review(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = copy.deepcopy(fixture)
        mutated["recommended_next_step"] = "m2_manual_private_export_verification"
        mutated["milestones"][1]["manual_verification_complete"] = True
        mutated["milestones"][1]["fully_complete"] = True

        self.assertEqual([], _matrix_errors_for(mutated))

    def test_accepts_m2_complete_and_advances_to_m3_manual_review(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = copy.deepcopy(fixture)
        mutated["recommended_next_step"] = "m3_manual_runtime_verification"
        mutated["milestones"][2]["manual_verification_complete"] = True
        mutated["milestones"][2]["fully_complete"] = True

        self.assertEqual([], _matrix_errors_for(mutated))

    def test_rejects_m5_planning_approval(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = copy.deepcopy(fixture)
        mutated["m5_planning_allowed"] = True

        self.assertNotEqual([], _matrix_errors_for(mutated))

    def test_rejects_unsafe_markers(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = copy.deepcopy(fixture)
        mutated["unsafe_note"] = "C:\\Users\\local\\secret screenshot raw payload"

        self.assertNotEqual([], _matrix_errors_for(mutated))

    def test_check_all_registers_completion_checks(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_m0_closeout.py", text)
        self.assertIn("scripts/review_m0_manual_verification.py", text)
        self.assertIn("scripts/check_m1_closeout.py", text)
        self.assertIn("scripts/check_milestone_completion_status.py", text)


def _matrix_errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "milestone-completion.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_milestone_completion_status_errors(path)


if __name__ == "__main__":
    unittest.main()
