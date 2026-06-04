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


REPORT_SCHEMA_VERSION = "m2-manual-private-export-verification-report.v1"
REVIEW_SCHEMA_VERSION = "m2-manual-private-export-verification-review.v1"
SELF_TEST_SCHEMA_VERSION = "m2-manual-private-export-verification-self-test.v1"
PRIVATE_REPORT_ROOT = "workspace/local-private/milestone-verification/m2/"
PRIVATE_REVIEW_ROOT = "workspace/local-private/milestone-verification/m2/review/"
RECOMMENDED_NEXT_STEP = "m3_manual_runtime_verification"
REPEAT_NEXT_STEP = "repeat_m2_manual_private_export_verification"

REQUIRED_TRUE_FIELDS = (
    "owner_chat_attestation_recorded",
    "explicit_private_export_selected",
    "local_import_run_reviewed",
    "line_index_run_reviewed",
    "context_graph_run_reviewed",
    "m2_closeout_review_run_reviewed",
    "import_locally_extracted_db_criterion_verified",
    "line_index_criterion_verified",
    "context_graph_criterion_verified",
    "m2_strict_completion_approved",
)
FALSE_SAFETY_FIELDS = (
    "private_paths_included",
    "filenames_included",
    "record_ids_included",
    "line_ids_included",
    "edge_ids_included",
    "relation_values_included",
    "source_text_included",
    "real_game_text_included",
    "extracted_db_included",
    "generated_private_db_included",
    "generated_line_index_included",
    "generated_context_graph_included",
    "screenshots_included",
    "logs_included",
    "provider_payloads_included",
    "generated_private_artifacts_included",
)
FORBIDDEN_M2_MARKERS = (
    "record id",
    "line id",
    "edge id",
    "relation value",
    "source text",
    "generated db",
    "context graph artifact",
)


class M2ManualPrivateExportVerificationError(RuntimeError):
    """Raised when M2 manual private-export verification evidence is unsafe or invalid."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review redacted M2 manual private-export verification evidence."
    )
    parser.add_argument("--report", type=Path, help="Report JSON under the ignored M2 report root.")
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
                raise M2ManualPrivateExportVerificationError(
                    "--report is required unless --self-test is used."
                )
            report = load_json(resolve_report_path(args.report))
            review = build_review(report)
            if args.output:
                write_json(resolve_review_output_path(args.output), review)
            result = {
                "schema_version": REVIEW_SCHEMA_VERSION,
                "report_valid": review["report_valid"],
                "manual_verification_complete": review["manual_verification_complete"],
                "recommended_next_step": review["recommended_next_step"],
            }
        if args.quiet:
            print("M2 manual private-export verification review passed.")
        else:
            print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        if args.quiet:
            print("M2 manual private-export verification review failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1


def build_review(report: dict[str, Any]) -> dict[str, Any]:
    errors = collect_report_errors(report)
    report_valid = not errors
    return {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "roadmap_milestone": "M2",
        "report_valid": report_valid,
        "evidence_kind": "chat_attestation",
        "manual_verification_complete": report_valid,
        "manual_private_export_verified": report_valid,
        "import_locally_extracted_db_done": report_valid,
        "line_index_done": report_valid,
        "context_graph_done": report_valid,
        "private_paths_included": False,
        "filenames_included": False,
        "record_ids_included": False,
        "line_ids_included": False,
        "edge_ids_included": False,
        "relation_values_included": False,
        "source_text_included": False,
        "real_game_text_included": False,
        "logs_included": False,
        "provider_payloads_included": False,
        "generated_private_artifacts_included": False,
        "blockers": sorted(errors),
        "recommended_next_step": RECOMMENDED_NEXT_STEP if report_valid else REPEAT_NEXT_STEP,
    }


def collect_report_errors(report: Any) -> list[str]:
    if not isinstance(report, dict):
        return ["M2 manual private-export verification report must be a JSON object."]
    errors: list[str] = []
    expected = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "roadmap_milestone": "M2",
        "evidence_kind": "chat_attestation",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, value in expected.items():
        if report.get(field) != value:
            errors.append(
                f"M2 manual private-export verification report {field} must be {value!r}."
            )
    for field in REQUIRED_TRUE_FIELDS:
        if report.get(field) is not True:
            errors.append(f"M2 manual private-export verification report must set {field}=true.")
    for field in FALSE_SAFETY_FIELDS:
        if report.get(field) is not False:
            errors.append(f"M2 manual private-export verification report must keep {field}=false.")
    errors.extend(
        unsafe_value_errors(
            report,
            label="M2 manual private-export verification report",
            allowed_values={
                REPORT_SCHEMA_VERSION,
                "M2",
                "chat_attestation",
                RECOMMENDED_NEXT_STEP,
            },
        )
    )
    for value in _iter_string_values(report):
        lowered = value.lower()
        for marker in FORBIDDEN_M2_MARKERS:
            if marker in lowered:
                errors.append(
                    f"M2 manual private-export verification report contains forbidden marker {marker!r}."
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
            "roadmap_milestone": "M2",
            "evidence_kind": "chat_attestation",
            **{field: True for field in REQUIRED_TRUE_FIELDS},
            **{field: False for field in FALSE_SAFETY_FIELDS},
            "recommended_next_step": RECOMMENDED_NEXT_STEP,
        }
        write_json(report_path, report)
        review = build_review(load_json(resolve_report_path(report_path, root=root)))
        write_json(resolve_review_output_path(output_path, root=root), review)
        if not review["manual_verification_complete"]:
            raise M2ManualPrivateExportVerificationError("Self-test report did not validate.")
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
        raise M2ManualPrivateExportVerificationError(
            f"Path must stay under {allowed_root}."
        ) from exc
    name = resolved.name.lower()
    if any(marker in name for marker in ("raw", "payload", "log", "screenshot", "secret")):
        raise M2ManualPrivateExportVerificationError("Path name contains an unsafe marker.")
    return resolved


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_string_values(nested)


if __name__ == "__main__":
    raise SystemExit(main())
