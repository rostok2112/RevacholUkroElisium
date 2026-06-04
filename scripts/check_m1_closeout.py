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
        strict_status_errors,
        unsafe_value_errors,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from milestone_completion_common import (
        doc_reference_errors,
        forbidden_boolean_errors,
        load_fixture,
        strict_status_errors,
        unsafe_value_errors,
    )
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/m1_closeout.synthetic.json"
DOC_PATH = ROOT / "docs/m1-closeout.md"
STANDARD_PATH = ROOT / "docs/milestone-completion-standard.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SCHEMA_VERSION = "m1-closeout.v1"
RECOMMENDED_NEXT_STEP = "m1_manual_synthetic_slice_review"
REQUIRED_TRUE_FIELDS = (
    "automated_complete",
    "fake_game_event_done",
    "context_packet_done",
    "translation_orchestrator_mock_done",
    "overlay_mock_done",
)
FORBIDDEN_FALSE_FIELDS = (
    "manual_verification_complete",
    "fully_complete",
    "user_reviews_synthetic_slice_and_overlay_mock",
    "private_artifact_commit_allowed",
    "real_game_text_commit_allowed",
    "screenshots_commit_allowed",
    "provider_payload_commit_allowed",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate M1 strict closeout status.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    errors = collect_m1_closeout_errors()
    if errors:
        print("M1 closeout check failed." if args.quiet else "\n".join(errors))
        return 1
    if args.quiet:
        print("M1 closeout check passed.")
    else:
        print(json.dumps({"ok": True, "schema_version": "m1-closeout-check.v1"}, indent=2))
    return 0


def collect_m1_closeout_errors(path: Path = FIXTURE_PATH) -> list[str]:
    payload_or_errors = load_fixture(path)
    if isinstance(payload_or_errors, list):
        return payload_or_errors
    payload = payload_or_errors
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(
        unsafe_value_errors(payload, label="M1 closeout", allowed_values=_allowed_values())
    )
    if path == FIXTURE_PATH:
        errors.extend(
            doc_reference_errors(
                (DOC_PATH, STANDARD_PATH),
                (
                    "tests/fixtures/m1_closeout.synthetic.json",
                    "scripts/check_m1_closeout.py",
                    RECOMMENDED_NEXT_STEP,
                ),
            )
        )
        tasks = TASKS_PATH.read_text(encoding="utf-8")
        for criterion in (
            "Fake game event.",
            "Context packet.",
            "Translation orchestrator mock.",
            "Overlay mock.",
        ):
            if criterion not in tasks:
                errors.append(f"tasks/milestones.md must keep M1 criterion {criterion!r}.")
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors = strict_status_errors(payload, label="M1 closeout")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "roadmap_milestone": "M1",
        "scope_status": "strict_completion_pending_manual_verification",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            errors.append(f"M1 closeout {field} must be {value!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M1 closeout must set {field}=true.")
    errors.extend(forbidden_boolean_errors(payload, FORBIDDEN_FALSE_FIELDS, label="M1 closeout"))
    if payload.get("manual_verification_required") is not True:
        errors.append("M1 closeout must require manual verification.")
    return errors


def _allowed_values() -> set[str]:
    return {
        SCHEMA_VERSION,
        "M1",
        "strict_completion_pending_manual_verification",
        RECOMMENDED_NEXT_STEP,
    }


if __name__ == "__main__":
    raise SystemExit(main())
