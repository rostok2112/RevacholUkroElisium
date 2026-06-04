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


FIXTURE_PATH = ROOT / "tests/fixtures/m0_closeout.synthetic.json"
DOC_PATH = ROOT / "docs/m0-closeout.md"
MANUAL_DOC_PATH = ROOT / "docs/m0-manual-verification.md"
STANDARD_PATH = ROOT / "docs/milestone-completion-standard.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SCHEMA_VERSION = "m0-closeout.v1"
PENDING_NEXT_STEP = "m0_manual_verification"
COMPLETE_NEXT_STEP = "m1_manual_synthetic_slice_review"
REQUIRED_TRUE_FIELDS = (
    "automated_complete",
    "agents_docs_done",
    "json_schemas_done",
    "safety_checks_done",
)
ALWAYS_FALSE_FIELDS = (
    "private_artifact_commit_allowed",
    "real_game_text_commit_allowed",
    "generated_artifact_commit_allowed",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate M0 strict closeout status.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    errors = collect_m0_closeout_errors()
    if errors:
        print("M0 closeout check failed." if args.quiet else "\n".join(errors))
        return 1
    if args.quiet:
        print("M0 closeout check passed.")
    else:
        print(json.dumps({"ok": True, "schema_version": "m0-closeout-check.v1"}, indent=2))
    return 0


def collect_m0_closeout_errors(path: Path = FIXTURE_PATH) -> list[str]:
    payload_or_errors = load_fixture(path)
    if isinstance(payload_or_errors, list):
        return payload_or_errors
    payload = payload_or_errors
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(
        unsafe_value_errors(payload, label="M0 closeout", allowed_values=_allowed_values())
    )
    if path == FIXTURE_PATH:
        errors.extend(
            doc_reference_errors(
                (DOC_PATH, STANDARD_PATH),
                (
                    "tests/fixtures/m0_closeout.synthetic.json",
                    "scripts/check_m0_closeout.py",
                    PENDING_NEXT_STEP,
                ),
            )
        )
        errors.extend(
            doc_reference_errors(
                (MANUAL_DOC_PATH,),
                (
                    "tests/fixtures/m0_manual_verification_report.synthetic.json",
                    "scripts/review_m0_manual_verification.py",
                    COMPLETE_NEXT_STEP,
                ),
            )
        )
        tasks = TASKS_PATH.read_text(encoding="utf-8")
        for criterion in ("AGENTS.md, skills, agents, docs.", "JSON schemas.", "Safety checks."):
            if criterion not in tasks:
                errors.append(f"tasks/milestones.md must keep M0 criterion {criterion!r}.")
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors = strict_status_errors(payload, label="M0 closeout")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "roadmap_milestone": "M0",
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            errors.append(f"M0 closeout {field} must be {value!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M0 closeout must set {field}=true.")
    errors.extend(forbidden_boolean_errors(payload, ALWAYS_FALSE_FIELDS, label="M0 closeout"))
    if payload.get("manual_verification_required") is not True:
        errors.append("M0 closeout must require manual verification.")
    manual_complete = payload.get("manual_verification_complete")
    fully_complete = payload.get("fully_complete")
    owner_confirmed = payload.get("owner_confirms_repo_contracts_and_safety_policy")
    if manual_complete is False:
        if payload.get("scope_status") != "strict_completion_pending_manual_verification":
            errors.append("Pending M0 closeout must keep pending scope_status.")
        if fully_complete is not False:
            errors.append("Pending M0 closeout must keep fully_complete=false.")
        if owner_confirmed is not False:
            errors.append("Pending M0 closeout must keep owner confirmation false.")
        if payload.get("recommended_next_step") != PENDING_NEXT_STEP:
            errors.append(f"Pending M0 closeout next step must be {PENDING_NEXT_STEP!r}.")
    elif manual_complete is True:
        if payload.get("scope_status") != "strict_completion_verified":
            errors.append("Verified M0 closeout must use strict_completion_verified scope_status.")
        if fully_complete is not True:
            errors.append("Verified M0 closeout must set fully_complete=true.")
        if owner_confirmed is not True:
            errors.append("Verified M0 closeout must set owner confirmation true.")
        if payload.get("recommended_next_step") != COMPLETE_NEXT_STEP:
            errors.append(f"Verified M0 closeout next step must be {COMPLETE_NEXT_STEP!r}.")
    else:
        errors.append("M0 closeout must set manual_verification_complete to a boolean.")
    return errors


def _allowed_values() -> set[str]:
    return {
        SCHEMA_VERSION,
        "M0",
        "strict_completion_pending_manual_verification",
        "strict_completion_verified",
        PENDING_NEXT_STEP,
        COMPLETE_NEXT_STEP,
    }


if __name__ == "__main__":
    raise SystemExit(main())
