from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.check_bepinex_metadata_probe_report import (
        REPORT_ROOT,
        canonical_json,
        collect_metadata_probe_report_errors,
        ensure_safe_metadata_probe_report_path,
    )
    from scripts.schema_validator import load_json
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_bepinex_metadata_probe_report import (
        REPORT_ROOT,
        canonical_json,
        collect_metadata_probe_report_errors,
        ensure_safe_metadata_probe_report_path,
    )
    from schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = REPORT_ROOT / "review"
SCHEMA_VERSION = "bepinex-bridge-metadata-probe-review.v1"

READY_NEXT_STEP = (
    "Safe to discuss a later metadata-only extension; this does not approve current-line "
    "capture or real text capture."
)
NOT_READY_NEXT_STEP = (
    "Complete or repeat the metadata-only manual smoke and update a redacted workspace report."
)

NO_SIDE_EFFECT_FLAGS = {
    "logs_read": False,
    "game_files_read": False,
    "screenshots_read": False,
    "companion_called": False,
    "provider_called": False,
}


class BepInExMetadataProbeReviewError(RuntimeError):
    """Raised when a metadata probe report review cannot be built safely."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review a redacted BepInEx metadata probe report without reading logs."
    )
    parser.add_argument(
        "--report", required=True, help="Report JSON under the metadata-probe root."
    )
    parser.add_argument("--output", help="Optional JSON review under metadata-probe/review/.")
    parser.add_argument(
        "--markdown-output", help="Optional Markdown review under metadata-probe/review/."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short readiness line.")
    args = parser.parse_args(argv)

    try:
        review = build_metadata_probe_review(Path(args.report))
        if args.output:
            output = ensure_safe_metadata_probe_review_output_path(Path(args.output), ".json")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(canonical_json(review), encoding="utf-8")
        if args.markdown_output:
            markdown_output = ensure_safe_metadata_probe_review_output_path(
                Path(args.markdown_output), ".md"
            )
            markdown_output.parent.mkdir(parents=True, exist_ok=True)
            markdown_output.write_text(render_markdown_review(review), encoding="utf-8")
    except Exception as exc:
        if args.quiet:
            print("BepInEx metadata probe review failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        print(f"BepInEx metadata probe review {review['readiness_status']}.")
    else:
        print(canonical_json(review), end="")
    return 0


def build_metadata_probe_review(report_path: Path) -> dict[str, object]:
    safe_report_path = ensure_safe_metadata_probe_report_path(report_path)
    validation_errors = collect_metadata_probe_report_errors(safe_report_path)
    if validation_errors:
        raise BepInExMetadataProbeReviewError("; ".join(validation_errors))

    report = load_json(safe_report_path)
    if not isinstance(report, dict):
        raise BepInExMetadataProbeReviewError("Metadata probe report must be a JSON object.")

    blockers = _readiness_blockers(report)
    ready = not blockers
    review: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "source_report": _safe_report_path(safe_report_path),
        "report_status": report["probe_status"],
        "metadata_only": report["metadata_only"],
        "real_text_captured": report["real_text_captured"],
        "current_line_capture_enabled": report["current_line_capture_enabled"],
        "ui_probe_attempted": report["ui_probe_attempted"],
        "scene_probe_attempted": report["scene_probe_attempted"],
        "probe_enabled": report["probe_enabled"],
        "probe_attempted": report["probe_attempted"],
        "probe_completed": report["probe_completed"],
        "counters_summary": _counter_summary(report),
        "readiness_status": "ready" if ready else "not_ready",
        "blockers": blockers,
        "recommended_next_step": READY_NEXT_STEP if ready else NOT_READY_NEXT_STEP,
        "evidence_summary_redacted": True,
        **NO_SIDE_EFFECT_FLAGS,
    }
    return review


def ensure_safe_metadata_probe_review_output_path(path: Path, expected_suffix: str) -> Path:
    resolved_root = REVIEW_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise BepInExMetadataProbeReviewError(
            f"Review output path must stay under {REVIEW_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != expected_suffix:
        raise BepInExMetadataProbeReviewError(f"Review output path must end in {expected_suffix}")
    return resolved


def render_markdown_review(review: dict[str, object]) -> str:
    blockers = review["blockers"]
    blocker_lines = "\n".join(f"- `{item}`" for item in blockers) if blockers else "- None"
    counters = review["counters_summary"]
    counter_lines = (
        "\n".join(f"- `{key}`: `{value}`" for key, value in counters.items())
        if isinstance(counters, dict)
        else "- None"
    )
    return (
        "# BepInEx Metadata Probe Review\n\n"
        f"- Schema version: `{review['schema_version']}`\n"
        f"- Report status: `{review['report_status']}`\n"
        f"- Readiness status: `{review['readiness_status']}`\n"
        f"- Metadata only: `{str(review['metadata_only']).lower()}`\n"
        f"- Real text captured: `{str(review['real_text_captured']).lower()}`\n"
        f"- Current-line capture enabled: `{str(review['current_line_capture_enabled']).lower()}`\n"
        "- Evidence summary redacted: `true`\n"
        "- Logs read: `false`\n"
        "- Game files read: `false`\n"
        "- Screenshots read: `false`\n"
        "- Companion called: `false`\n"
        "- Provider called: `false`\n\n"
        "## Counters\n\n"
        f"{counter_lines}\n\n"
        "## Blockers\n\n"
        f"{blocker_lines}\n\n"
        "## Recommended Next Step\n\n"
        f"{review['recommended_next_step']}\n"
    )


def _readiness_blockers(report: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    status = report.get("probe_status")
    if status != "pass":
        blockers.append(f"report_status_not_pass:{status}")
    if report.get("metadata_only") is not True:
        blockers.append("metadata_only_not_true")
    if report.get("probe_enabled") is not True:
        blockers.append("probe_not_enabled")
    if report.get("probe_attempted") is not True:
        blockers.append("probe_not_attempted")
    if report.get("probe_completed") is not True:
        blockers.append("probe_not_completed")
    if report.get("real_text_captured") is not False:
        blockers.append("real_text_captured_not_false")
    if report.get("current_line_capture_enabled") is not False:
        blockers.append("current_line_capture_enabled_not_false")
    if report.get("ui_probe_attempted") is not False:
        blockers.append("ui_probe_attempted_not_false")
    if report.get("scene_probe_attempted") is not False:
        blockers.append("scene_probe_attempted_not_false")
    return blockers


def _counter_summary(report: dict[str, Any]) -> dict[str, int]:
    counters = report.get("counters")
    if not isinstance(counters, dict):
        return {}
    return {
        key: value
        for key, value in sorted(counters.items())
        if isinstance(key, str) and isinstance(value, int) and not isinstance(value, bool)
    }


def _safe_report_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve()))
    except ValueError:
        return f"<local:{path.name}>"


if __name__ == "__main__":
    sys.exit(main())
