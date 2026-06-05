from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.milestone_completion_common import (
        doc_reference_errors,
        load_fixture,
        strict_status_errors,
        unsafe_value_errors,
    )
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from milestone_completion_common import (
        doc_reference_errors,
        load_fixture,
        strict_status_errors,
        unsafe_value_errors,
    )
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/milestone_completion_status.synthetic.json"
STANDARD_PATH = ROOT / "docs/milestone-completion-standard.md"
M0_DOC_PATH = ROOT / "docs/m0-closeout.md"
M1_DOC_PATH = ROOT / "docs/m1-closeout.md"
M2_DOC_PATH = ROOT / "docs/m2-closeout-review-gate.md"
M3_DOC_PATH = ROOT / "docs/m3-closeout.md"
M4_DOC_PATH = ROOT / "docs/m4-closeout.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SCHEMA_VERSION = "milestone-completion-status.v1"
RECOMMENDED_NEXT_STEP = "m0_manual_verification"
M1_RECOMMENDED_NEXT_STEP = "m1_manual_synthetic_slice_review"
M2_RECOMMENDED_NEXT_STEP = "m2_manual_private_export_verification"
M3_RECOMMENDED_NEXT_STEP = "m3_manual_runtime_verification"
RUNTIME_RECOMMENDED_NEXT_STEP = "runtime_current_line_capture_contract"
RUNTIME_TRANSPORT_RECOMMENDED_NEXT_STEP = "runtime_current_line_capture_spike"
RUNTIME_CAPTURE_SPIKE_RECOMMENDED_NEXT_STEP = "runtime_current_line_capture_strategy_decision"
RUNTIME_CAPTURE_STRATEGY_RECOMMENDED_NEXT_STEP = "runtime_targeted_hook_candidate_research_contract"
RUNTIME_TARGETED_HOOK_CONTRACT_RECOMMENDED_NEXT_STEP = (
    "runtime_targeted_hook_candidate_research_local_report"
)
RUNTIME_TARGETED_HOOK_REPORT_RECOMMENDED_NEXT_STEP = (
    "runtime_targeted_hook_candidate_research_review_gate"
)
RUNTIME_TARGETED_HOOK_REVIEW_RECOMMENDED_NEXT_STEP = (
    "runtime_targeted_hook_candidate_decision_contract"
)
RUNTIME_TARGETED_HOOK_DECISION_RECOMMENDED_NEXT_STEP = "runtime_private_hook_descriptor_contract"
RUNTIME_PRIVATE_HOOK_DESCRIPTOR_RECOMMENDED_NEXT_STEP = (
    "runtime_private_hook_descriptor_local_validation"
)
RUNTIME_PRIVATE_HOOK_DESCRIPTOR_LOCAL_VALIDATION_RECOMMENDED_NEXT_STEP = (
    "runtime_private_hook_descriptor_local_validation_review_gate"
)
MILESTONES = ("M0", "M1", "M2", "M3", "M4")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate strict milestone completion status.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    errors = collect_milestone_completion_status_errors()
    if errors:
        print("Milestone completion status check failed." if args.quiet else "\n".join(errors))
        return 1
    if args.quiet:
        print("Milestone completion status check passed.")
    else:
        payload_or_errors = load_fixture(FIXTURE_PATH)
        payload = payload_or_errors if isinstance(payload_or_errors, dict) else {}
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "milestone-completion-status-check.v1",
                    "recommended_next_step": _expected_next_step(payload),
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_milestone_completion_status_errors(path: Path = FIXTURE_PATH) -> list[str]:
    payload_or_errors = load_fixture(path)
    if isinstance(payload_or_errors, list):
        return payload_or_errors
    payload = payload_or_errors
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(
        unsafe_value_errors(
            payload,
            label="milestone completion status",
            allowed_values=_allowed_values(payload),
        )
    )
    if path == FIXTURE_PATH:
        errors.extend(
            doc_reference_errors(
                (
                    STANDARD_PATH,
                    M0_DOC_PATH,
                    M1_DOC_PATH,
                    M2_DOC_PATH,
                    M3_DOC_PATH,
                    M4_DOC_PATH,
                ),
                (
                    "automated_complete",
                    "manual_verification_required",
                    "manual_verification_complete",
                    "fully_complete",
                ),
            )
        )
        tasks = TASKS_PATH.read_text(encoding="utf-8")
        for milestone in MILESTONES:
            if f"## {milestone}" not in tasks:
                errors.append(f"tasks/milestones.md must keep {milestone}.")
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Milestone completion schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("roadmap_source") != "tasks/milestones.md":
        errors.append("Milestone completion status must point to tasks/milestones.md.")
    if payload.get("strict_completion_standard") != "docs/milestone-completion-standard.md":
        errors.append("Milestone completion status must point to the strict standard doc.")
    expected_next_step = _expected_next_step(payload)
    if payload.get("recommended_next_step") != expected_next_step:
        errors.append(f"Milestone completion next step must be {expected_next_step!r}.")
    milestones = payload.get("milestones")
    if not isinstance(milestones, list):
        return errors + ["Milestone completion status must include a milestones array."]
    if [item.get("roadmap_milestone") for item in milestones if isinstance(item, dict)] != list(
        MILESTONES
    ):
        errors.append("Milestone completion status must list M0-M4 in order.")
    all_fully_complete = True
    for item in milestones:
        if not isinstance(item, dict):
            errors.append("Milestone entries must be JSON objects.")
            all_fully_complete = False
            continue
        label = f"{item.get('roadmap_milestone', 'unknown')} status"
        errors.extend(strict_status_errors(item, label=label))
        if item.get("automated_complete") is not True:
            errors.append(f"{label} must keep automated_complete=true for recovered work.")
        if item.get("manual_verification_required") is not True:
            errors.append(f"{label} must require manual verification.")
        if item.get("manual_verification_complete") is not item.get("fully_complete"):
            errors.append(f"{label} manual_verification_complete must match fully_complete.")
        if (
            item.get("fully_complete") is True
            and item.get("manual_verification_complete") is not True
        ):
            errors.append(f"{label} cannot be fully complete without manual verification.")
        if (
            not isinstance(item.get("blocking_manual_step"), str)
            or not item["blocking_manual_step"]
        ):
            errors.append(f"{label} must name a blocking_manual_step.")
        all_fully_complete = all_fully_complete and item.get("fully_complete") is True
    if payload.get("m5_planning_allowed") is not all_fully_complete:
        errors.append(
            "m5_planning_allowed must equal whether all M0-M4 entries are fully complete."
        )
    if payload.get("m5_planning_allowed") is not False:
        errors.append("M5 planning must remain blocked until M0-M4 strict completion is true.")
    if payload.get("runtime_first_path_active") is True:
        if payload.get("m2_private_export_source_available") is not False:
            errors.append(
                "Runtime-first status must record m2_private_export_source_available=false."
            )
        if payload.get("runtime_translation_memory_done") is not True:
            errors.append("Runtime-first status must record runtime_translation_memory_done=true.")
        if payload.get("runtime_current_line_transport_done") is not True:
            errors.append(
                "Runtime-first status must record runtime_current_line_transport_done=true."
            )
        if payload.get("runtime_current_line_capture_spike_done") is not True:
            errors.append(
                "Runtime-first status must record runtime_current_line_capture_spike_done=true."
            )
        if payload.get("runtime_current_line_capture_strategy_decision_done") is not True:
            errors.append(
                "Runtime-first status must record "
                "runtime_current_line_capture_strategy_decision_done=true."
            )
        if payload.get("runtime_targeted_hook_candidate_research_contract_done") is not True:
            errors.append(
                "Runtime-first status must record "
                "runtime_targeted_hook_candidate_research_contract_done=true."
            )
        if payload.get("runtime_targeted_hook_candidate_research_local_report_done") is not True:
            errors.append(
                "Runtime-first status must record "
                "runtime_targeted_hook_candidate_research_local_report_done=true."
            )
        if payload.get("runtime_targeted_hook_candidate_research_review_gate_done") is not True:
            errors.append(
                "Runtime-first status must record "
                "runtime_targeted_hook_candidate_research_review_gate_done=true."
            )
        if payload.get("runtime_targeted_hook_candidate_decision_contract_done") is not True:
            errors.append(
                "Runtime-first status must record "
                "runtime_targeted_hook_candidate_decision_contract_done=true."
            )
        if payload.get("runtime_private_hook_descriptor_contract_done") is not True:
            errors.append(
                "Runtime-first status must record "
                "runtime_private_hook_descriptor_contract_done=true."
            )
        if payload.get("runtime_private_hook_descriptor_local_validation_done") is not True:
            errors.append(
                "Runtime-first status must record "
                "runtime_private_hook_descriptor_local_validation_done=true."
            )
    return errors


def _expected_next_step(payload: dict[str, Any]) -> str:
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("runtime_current_line_capture_spike_done") is True
        and payload.get("runtime_current_line_capture_strategy_decision_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_contract_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_local_report_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_review_gate_done") is True
        and payload.get("runtime_targeted_hook_candidate_decision_contract_done") is True
        and payload.get("runtime_private_hook_descriptor_contract_done") is True
        and payload.get("runtime_private_hook_descriptor_local_validation_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_PRIVATE_HOOK_DESCRIPTOR_LOCAL_VALIDATION_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("runtime_current_line_capture_spike_done") is True
        and payload.get("runtime_current_line_capture_strategy_decision_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_contract_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_local_report_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_review_gate_done") is True
        and payload.get("runtime_targeted_hook_candidate_decision_contract_done") is True
        and payload.get("runtime_private_hook_descriptor_contract_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_PRIVATE_HOOK_DESCRIPTOR_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("runtime_current_line_capture_spike_done") is True
        and payload.get("runtime_current_line_capture_strategy_decision_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_contract_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_local_report_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_review_gate_done") is True
        and payload.get("runtime_targeted_hook_candidate_decision_contract_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_TARGETED_HOOK_DECISION_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("runtime_current_line_capture_spike_done") is True
        and payload.get("runtime_current_line_capture_strategy_decision_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_contract_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_local_report_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_review_gate_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_TARGETED_HOOK_REVIEW_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("runtime_current_line_capture_spike_done") is True
        and payload.get("runtime_current_line_capture_strategy_decision_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_contract_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_local_report_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_TARGETED_HOOK_REPORT_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("runtime_current_line_capture_spike_done") is True
        and payload.get("runtime_current_line_capture_strategy_decision_done") is True
        and payload.get("runtime_targeted_hook_candidate_research_contract_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_TARGETED_HOOK_CONTRACT_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("runtime_current_line_capture_spike_done") is True
        and payload.get("runtime_current_line_capture_strategy_decision_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_CAPTURE_STRATEGY_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("runtime_current_line_capture_spike_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_CAPTURE_SPIKE_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("runtime_current_line_transport_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_TRANSPORT_RECOMMENDED_NEXT_STEP
    if (
        payload.get("runtime_first_path_active") is True
        and payload.get("runtime_translation_memory_done") is True
        and payload.get("m2_private_export_source_available") is False
    ):
        return RUNTIME_RECOMMENDED_NEXT_STEP
    milestones = payload.get("milestones")
    if not isinstance(milestones, list) or not milestones:
        return RECOMMENDED_NEXT_STEP
    first = milestones[0]
    if (
        isinstance(first, dict)
        and first.get("roadmap_milestone") == "M0"
        and first.get("fully_complete") is True
    ):
        second = milestones[1] if len(milestones) > 1 else None
        if (
            isinstance(second, dict)
            and second.get("roadmap_milestone") == "M1"
            and second.get("fully_complete") is True
        ):
            third = milestones[2] if len(milestones) > 2 else None
            if (
                isinstance(third, dict)
                and third.get("roadmap_milestone") == "M2"
                and third.get("fully_complete") is True
            ):
                return M3_RECOMMENDED_NEXT_STEP
            return M2_RECOMMENDED_NEXT_STEP
        return M1_RECOMMENDED_NEXT_STEP
    return RECOMMENDED_NEXT_STEP


def _allowed_values(payload: dict[str, Any]) -> set[str]:
    values = {
        SCHEMA_VERSION,
        "tasks/milestones.md",
        "docs/milestone-completion-standard.md",
        RECOMMENDED_NEXT_STEP,
        M1_RECOMMENDED_NEXT_STEP,
        M2_RECOMMENDED_NEXT_STEP,
        M3_RECOMMENDED_NEXT_STEP,
        RUNTIME_RECOMMENDED_NEXT_STEP,
        RUNTIME_TRANSPORT_RECOMMENDED_NEXT_STEP,
        RUNTIME_CAPTURE_SPIKE_RECOMMENDED_NEXT_STEP,
        RUNTIME_CAPTURE_STRATEGY_RECOMMENDED_NEXT_STEP,
        RUNTIME_TARGETED_HOOK_CONTRACT_RECOMMENDED_NEXT_STEP,
        RUNTIME_TARGETED_HOOK_REPORT_RECOMMENDED_NEXT_STEP,
        RUNTIME_TARGETED_HOOK_REVIEW_RECOMMENDED_NEXT_STEP,
        RUNTIME_TARGETED_HOOK_DECISION_RECOMMENDED_NEXT_STEP,
        RUNTIME_PRIVATE_HOOK_DESCRIPTOR_RECOMMENDED_NEXT_STEP,
        RUNTIME_PRIVATE_HOOK_DESCRIPTOR_LOCAL_VALIDATION_RECOMMENDED_NEXT_STEP,
        *MILESTONES,
    }
    milestones = payload.get("milestones")
    if isinstance(milestones, list):
        for item in milestones:
            if isinstance(item, dict) and isinstance(item.get("blocking_manual_step"), str):
                values.add(item["blocking_manual_step"])
    return values


if __name__ == "__main__":
    raise SystemExit(main())
