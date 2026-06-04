from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_roadmap_governance_review import (
    FIXTURE_PATH,
    collect_roadmap_governance_review_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class RoadmapGovernanceReviewTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_roadmap_governance_review_errors())

    def test_reviews_all_top_level_milestones(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        self.assertEqual(
            [f"M{i}" for i in range(8)],
            [m["roadmap_milestone"] for m in fixture["milestones_reviewed"]],
        )
        self.assertTrue(fixture["roadmap_may_be_amended_during_development"])
        self.assertFalse(fixture["roadmap_is_immutable"])

    def test_rejects_immutable_or_uncontrolled_amendments(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for mutation in (
            {"roadmap_is_immutable": True},
            {"roadmap_may_be_amended_during_development": False},
            {"amendment_requires_tasks_milestones_update": False},
            {"amendment_requires_docs_update": False},
            {"amendment_requires_checker_or_fixture_update": False},
        ):
            with self.subTest(mutation=mutation):
                mutated = copy.deepcopy(fixture)
                mutated.update(mutation)
                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_missing_milestones_and_unsafe_markers(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        missing = copy.deepcopy(fixture)
        missing["milestones_reviewed"] = missing["milestones_reviewed"][:-1]
        self.assertNotEqual([], _errors_for(missing))

        unsafe = copy.deepcopy(fixture)
        unsafe["note"] = "C:\\Users\\local\\secret raw payload"
        self.assertNotEqual([], _errors_for(unsafe))

    def test_check_all_registration(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        self.assertIn("scripts/check_roadmap_governance_review.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "roadmap-governance.json"
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return collect_roadmap_governance_review_errors(path)


if __name__ == "__main__":
    unittest.main()
