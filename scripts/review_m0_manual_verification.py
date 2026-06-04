from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

try:
    from scripts.milestone_completion_common import unsafe_value_errors
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from milestone_completion_common import unsafe_value_errors
    from schema_validator import load_json
    from synthetic_slice import ROOT


REPORT_SCHEMA_VERSION = "m0-manual-verification-report.v1"
REVIEW_SCHEMA_VERSION = "m0-manual-verification-review.v1"
SELF_TEST_SCHEMA_VERSION = "m0-manual-verification-self-test.v1"
PRIVATE_REPORT_ROOT = "workspace/local-private/milestone-verification/m0/"
PRIVATE_REVIEW_ROOT = "workspace/local-private/milestone-verification/m0/review/"
RECOMMENDED_NEXT_STEP = "m1_manual_synthetic_slice_review"

REQUIRED_TRUE_FIELDS = (
    "owner_chat_attestation_recorded",
    "agents_md_reviewed",
    "tasks_milestones_reviewed",
    "milestone_completion_standard_reviewed",
    "m0_closeout_reviewed",
    "gitignore_policy_reviewed",
    "project_mission_and_safety_policy_accepted",
    "canonical_roadmap_accepted",
    "copyright_and_private_artifact_policy_accepted",
    "json_schema_and_safety_check_approach_accepted",
    "m0_strict_completion_approved",
)
FALSE_SAFETY_FIELDS = (
    "private_paths_included",
    "real_game_text_included",
    "extracted_db_included",
    "screenshots_included",
    "logs_included",
    "provider_payloads_included",
    "generated_private_artifacts_included",
)


class M0ManualVerificationError(RuntimeError):
    """Raised when M0 manual verification evidence is unsafe or invalid."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review redacted M0 manual verification evidence.")
    parser.add_argument("--report", type=Path, help="Report JSON under the ignored M0 report root.")
    parser.add_argument(
        "--output", type=Path, help="Optional review JSON under the ignored review root."
    )
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            result = run_self_test()
        else:
            if args.report is None:
                raise M0ManualVerificationError("--report is required unless --self-test is used.")
            report_path = resolve_report_path(args.report)
            report = load_json(report_path)
            review = build_review(report)
            if args.output:
                output_path = resolve_review_output_path(args.output)
                write_json(output_path, review)
            result = {
                "schema_version": REVIEW_SCHEMA_VERSION,
                "report_valid": review["report_valid"],
                "manual_verification_complete": review["manual_verification_complete"],
                "recommended_next_step": review["recommended_next_step"],
            }
        if not args.quiet:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("M0 manual verification review passed.")
        return 0
    except Exception as exc:
        if args.quiet:
            print("M0 manual verification review failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1


def build_review(report: dict[str, Any]) -> dict[str, Any]:
    errors = collect_report_errors(report)
    report_valid = not errors
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "roadmap_milestone": "M0",
        "report_valid": report_valid,
        "evidence_kind": "chat_attestation",
        "manual_verification_complete": report_valid,
        "owner_confirms_repo_contracts_and_safety_policy": report_valid,
        "private_paths_included": False,
        "real_game_text_included": False,
        "extracted_db_included": False,
        "screenshots_included": False,
        "logs_included": False,
        "provider_payloads_included": False,
        "generated_private_artifacts_included": False,
        "blockers": sorted(errors),
        "recommended_next_step": RECOMMENDED_NEXT_STEP
        if report_valid
        else "repeat_m0_manual_verification",
    }


def collect_report_errors(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["M0 manual verification report must be a JSON object."]
    errors: list[str] = []
    expected = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "roadmap_milestone": "M0",
        "evidence_kind": "chat_attestation",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, value in expected.items():
        if report.get(field) != value:
            errors.append(f"M0 manual verification report {field} must be {value!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if report.get(field) is not True:
            errors.append(f"M0 manual verification report must set {field}=true.")
    for field in FALSE_SAFETY_FIELDS:
        if report.get(field) is not False:
            errors.append(f"M0 manual verification report must keep {field}=false.")
    errors.extend(
        unsafe_value_errors(
            report,
            label="M0 manual verification report",
            allowed_values={
                REPORT_SCHEMA_VERSION,
                "M0",
                "chat_attestation",
                RECOMMENDED_NEXT_STEP,
            },
        )
    )
    return errors


def resolve_report_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_under_root(path, PRIVATE_REPORT_ROOT, root=root)


def resolve_review_output_path(path: Path, *, root: Path = ROOT) -> Path:
    return _resolve_under_root(path, PRIVATE_REVIEW_ROOT, root=root)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_self_test() -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        report_path = root / PRIVATE_REPORT_ROOT / "report.json"
        output_path = root / PRIVATE_REVIEW_ROOT / "review.json"
        report = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "roadmap_milestone": "M0",
            "evidence_kind": "chat_attestation",
            **{field: True for field in REQUIRED_TRUE_FIELDS},
            **{field: False for field in FALSE_SAFETY_FIELDS},
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
        }
        write_json(report_path, report)
        resolved_report = resolve_report_path(report_path, root=root)
        resolved_output = resolve_review_output_path(output_path, root=root)
        review = build_review(load_json(resolved_report))
        write_json(resolved_output, review)
        if not review["manual_verification_complete"]:
            raise M0ManualVerificationError("Self-test report did not validate.")
        return {
            "schema_version": SELF_TEST_SCHEMA_VERSION,
            "ok": True,
            "manual_verification_complete": True,
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
        }


def _resolve_under_root(path: Path, allowed_root: str, *, root: Path) -> Path:
    candidate = path if path.is_absolute() else root / path
    resolved = candidate.resolve(strict=False)
    allowed = (root / allowed_root).resolve(strict=False)
    try:
        resolved.relative_to(allowed)
    except ValueError as exc:
        raise M0ManualVerificationError(f"Path must stay under {allowed_root}.") from exc
    name = resolved.name.lower()
    if any(marker in name for marker in ("raw", "payload", "log", "screenshot", "secret")):
        raise M0ManualVerificationError("Path name contains an unsafe marker.")
    return resolved


if __name__ == "__main__":
    raise SystemExit(main())
