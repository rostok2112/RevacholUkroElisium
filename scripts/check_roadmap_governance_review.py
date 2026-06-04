from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.milestone_completion_common import (
        doc_reference_errors,
        forbidden_boolean_errors,
        load_fixture,
        unsafe_value_errors,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from milestone_completion_common import (
        doc_reference_errors,
        forbidden_boolean_errors,
        load_fixture,
        unsafe_value_errors,
    )
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/roadmap_governance_review.synthetic.json"
DOC_PATH = ROOT / "docs/roadmap-governance-review.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SCHEMA_VERSION = "roadmap-governance-review.v1"
RECOMMENDED_NEXT_STEP = "m0_manual_verification"
MILESTONES = (
    ("M0", "Repo and contracts"),
    ("M1", "Synthetic vertical slice"),
    ("M2", "Local extraction import"),
    ("M3", "BepInEx bridge"),
    ("M4", "Real overlay"),
    ("M5", "Maximum quality pipeline"),
    ("M6", "Voice/audio context"),
    ("M7", "Review studio"),
)
REQUIRED_TRUE_FIELDS = (
    "roadmap_is_current_canonical_source",
    "roadmap_may_be_amended_during_development",
    "amendment_requires_tasks_milestones_update",
    "amendment_requires_docs_update",
    "amendment_requires_checker_or_fixture_update",
    "strict_completion_required_after_amendment",
)
FORBIDDEN_FALSE_FIELDS = (
    "roadmap_is_immutable",
    "private_artifact_commit_allowed",
    "real_game_text_commit_allowed",
    "generated_artifact_commit_allowed",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate roadmap governance review.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    errors = collect_roadmap_governance_review_errors()
    if errors:
        print("Roadmap governance review check failed." if args.quiet else "\n".join(errors))
        return 1
    if args.quiet:
        print("Roadmap governance review check passed.")
    else:
        print(json.dumps({"ok": True, "schema_version": "roadmap-governance-review-check.v1"}))
    return 0


def collect_roadmap_governance_review_errors(path: Path = FIXTURE_PATH) -> list[str]:
    payload_or_errors = load_fixture(path)
    if isinstance(payload_or_errors, list):
        return payload_or_errors
    payload = payload_or_errors
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(
        unsafe_value_errors(
            payload,
            label="roadmap governance review",
            allowed_values=_allowed_values(payload),
        )
    )
    if path == FIXTURE_PATH:
        errors.extend(
            doc_reference_errors(
                (DOC_PATH,),
                (
                    "tasks/milestones.md",
                    "roadmap criteria may be amended",
                    "M0 - Repo and contracts",
                    "M7 - Review studio",
                ),
            )
        )
        tasks = TASKS_PATH.read_text(encoding="utf-8")
        for milestone, title in MILESTONES:
            if f"## {milestone}" not in tasks or title not in tasks:
                errors.append(f"tasks/milestones.md must keep {milestone} - {title}.")
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = {
        "schema_version": SCHEMA_VERSION,
        "roadmap_source": "tasks/milestones.md",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            errors.append(f"Roadmap governance {field} must be {value!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"Roadmap governance must set {field}=true.")
    errors.extend(
        forbidden_boolean_errors(payload, FORBIDDEN_FALSE_FIELDS, label="roadmap governance")
    )
    reviewed = payload.get("milestones_reviewed")
    if not isinstance(reviewed, list):
        return errors + ["Roadmap governance must include milestones_reviewed."]
    if [
        (item.get("roadmap_milestone"), item.get("title"))
        for item in reviewed
        if isinstance(item, dict)
    ] != list(MILESTONES):
        errors.append("Roadmap governance must review M0-M7 in order with exact titles.")
    for item in reviewed:
        if not isinstance(item, dict):
            errors.append("Roadmap governance milestone entries must be objects.")
            continue
        for field in ("criteria_are_high_level", "criteria_may_expand_if_insufficient"):
            if item.get(field) is not True:
                errors.append(f"{item.get('roadmap_milestone', 'unknown')} must set {field}=true.")
    return errors


def _allowed_values(payload: dict[str, Any]) -> set[str]:
    values = {
        SCHEMA_VERSION,
        "tasks/milestones.md",
        RECOMMENDED_NEXT_STEP,
    }
    reviewed = payload.get("milestones_reviewed")
    if isinstance(reviewed, list):
        for item in reviewed:
            if isinstance(item, dict):
                for field in ("roadmap_milestone", "title"):
                    value = item.get(field)
                    if isinstance(value, str):
                        values.add(value)
    return values


if __name__ == "__main__":
    raise SystemExit(main())
