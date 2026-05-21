from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.check_bepinex_runtime_smoke_report import (
        REPORT_ROOT,
        canonical_json,
        collect_runtime_smoke_report_errors,
        ensure_safe_report_path,
    )
    from scripts.schema_validator import load_json
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_bepinex_runtime_smoke_report import (
        REPORT_ROOT,
        canonical_json,
        collect_runtime_smoke_report_errors,
        ensure_safe_report_path,
    )
    from schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = REPORT_ROOT / "review"
SCHEMA_VERSION = "bepinex-bridge-runtime-smoke-review.v1"

READY_NEXT_STEP = (
    "Review ADR 0008 before scoping a metadata-only current-line probe; "
    "this does not approve capture."
)
NOT_READY_NEXT_STEP = (
    "Complete or repeat the synthetic/manual runtime smoke and update a redacted workspace report."
)

NO_SIDE_EFFECT_FLAGS = {
    "logs_read": False,
    "game_files_read": False,
    "screenshots_read": False,
    "companion_called": False,
    "provider_called": False,
}


class BepInExRuntimeSmokeReviewError(RuntimeError):
    """Raised when a runtime smoke report review cannot be built safely."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review a redacted BepInEx runtime smoke report without reading logs."
    )
    parser.add_argument("--report", required=True, help="Report JSON under the runtime-smoke root.")
    parser.add_argument("--output", help="Optional JSON review under runtime-smoke/review/.")
    parser.add_argument(
        "--markdown-output", help="Optional Markdown review under runtime-smoke/review/."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short readiness line.")
    args = parser.parse_args(argv)

    try:
        review = build_runtime_smoke_review(Path(args.report))
        if args.output:
            output = ensure_safe_review_output_path(Path(args.output), ".json")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(canonical_json(review), encoding="utf-8")
        if args.markdown_output:
            markdown_output = ensure_safe_review_output_path(Path(args.markdown_output), ".md")
            markdown_output.parent.mkdir(parents=True, exist_ok=True)
            markdown_output.write_text(render_markdown_review(review), encoding="utf-8")
    except Exception as exc:
        if args.quiet:
            print("BepInEx runtime smoke review failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        status = "ready" if review["ready_for_next_phase"] else "not ready"
        print(f"BepInEx runtime smoke review {status}.")
    else:
        print(canonical_json(review), end="")
    return 0


def build_runtime_smoke_review(report_path: Path) -> dict[str, object]:
    safe_report_path = ensure_safe_report_path(report_path)
    validation_errors = collect_runtime_smoke_report_errors(safe_report_path)
    if validation_errors:
        raise BepInExRuntimeSmokeReviewError("; ".join(validation_errors))

    report = load_json(safe_report_path)
    if not isinstance(report, dict):
        raise BepInExRuntimeSmokeReviewError("Runtime smoke report must be a JSON object.")

    blockers = _readiness_blockers(report)
    ready = not blockers
    review: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "source_report": _safe_report_path(safe_report_path),
        "source_report_status": report["smoke_status"],
        "bridge_runtime_smoke_status": report["smoke_status"],
        "plugin_loaded_observed": report["plugin_loaded_observed"],
        "health_check_observed": report["health_check_observed"],
        "companion_available_observed": report["companion_available_observed"],
        "companion_unavailable_observed": report["companion_unavailable_observed"],
        "synthetic_send_enabled": report["synthetic_send_enabled"],
        "synthetic_send_observed": report["synthetic_send_observed"],
        "companion_received_synthetic_event": report["companion_received_synthetic_event"],
        "game_continued_when_companion_unavailable": report[
            "game_continued_when_companion_unavailable"
        ],
        "warning_count": report["warnings_count"],
        "msb3277_warning_count": report["msb3277_warning_count"],
        "evidence_summary_redacted": True,
        "ready_for_next_phase": ready,
        "blockers": blockers,
        "recommended_next_step": READY_NEXT_STEP if ready else NOT_READY_NEXT_STEP,
        **NO_SIDE_EFFECT_FLAGS,
    }
    return review


def ensure_safe_review_output_path(path: Path, expected_suffix: str) -> Path:
    resolved_root = REVIEW_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise BepInExRuntimeSmokeReviewError(
            f"Review output path must stay under {REVIEW_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != expected_suffix:
        raise BepInExRuntimeSmokeReviewError(f"Review output path must end in {expected_suffix}")
    return resolved


def render_markdown_review(review: dict[str, object]) -> str:
    blockers = review["blockers"]
    blocker_lines = "\n".join(f"- `{item}`" for item in blockers) if blockers else "- None"
    return (
        "# BepInEx Runtime Smoke Review\n\n"
        f"- Schema version: `{review['schema_version']}`\n"
        f"- Source report status: `{review['source_report_status']}`\n"
        f"- Ready for next phase: `{str(review['ready_for_next_phase']).lower()}`\n"
        f"- Warning count: `{review['warning_count']}`\n"
        f"- MSB3277 warning count: `{review['msb3277_warning_count']}`\n"
        "- Evidence summary redacted: `true`\n"
        "- Logs read: `false`\n"
        "- Game files read: `false`\n"
        "- Companion called: `false`\n"
        "- Provider called: `false`\n\n"
        "## Blockers\n\n"
        f"{blocker_lines}\n\n"
        "## Recommended Next Step\n\n"
        f"{review['recommended_next_step']}\n"
    )


def _readiness_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    status = report.get("smoke_status")
    if status != "pass":
        blockers.append(f"report_status_not_pass:{status}")
    if report.get("plugin_loaded_observed") is not True:
        blockers.append("plugin_loaded_not_observed")
    if report.get("health_check_observed") is not True:
        blockers.append("health_check_not_observed")

    companion_available = report.get("companion_available_observed") is True
    companion_unavailable = report.get("companion_unavailable_observed") is True
    if not companion_available and not companion_unavailable:
        blockers.append("companion_availability_not_observed")
    if (
        companion_unavailable
        and report.get("game_continued_when_companion_unavailable") is not True
    ):
        blockers.append("game_continued_when_companion_unavailable_not_observed")
    if not companion_unavailable and not _has_safe_reason(
        report, "unavailable_case_not_run_reason"
    ):
        blockers.append("unavailable_case_not_observed_or_explained")

    synthetic_send_enabled = report.get("synthetic_send_enabled") is True
    synthetic_send_observed = report.get("synthetic_send_observed") is True
    if synthetic_send_enabled and not synthetic_send_observed:
        blockers.append("synthetic_send_enabled_but_not_observed")
    if not synthetic_send_observed and not _has_safe_reason(
        report, "synthetic_send_not_run_reason"
    ):
        blockers.append("synthetic_send_not_observed_or_explained")
    return blockers


def _has_safe_reason(report: dict[str, Any], field: str) -> bool:
    value = report.get(field)
    return isinstance(value, str) and bool(value.strip())


def _safe_report_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve()))
    except ValueError:
        return f"<local:{path.name}>"


if __name__ == "__main__":
    sys.exit(main())
