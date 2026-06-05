from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from scripts.check_runtime_current_line_capture_spike_report import (
        REPORT_ROOT,
        canonical_json,
        collect_capture_spike_report_errors,
        default_report_template,
        ensure_safe_report_path,
    )
    from scripts.schema_validator import load_json
except ModuleNotFoundError:  # pragma: no cover
    from check_runtime_current_line_capture_spike_report import (
        REPORT_ROOT,
        canonical_json,
        collect_capture_spike_report_errors,
        default_report_template,
        ensure_safe_report_path,
    )
    from schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = REPORT_ROOT / "review"
SCHEMA_VERSION = "runtime-current-line-capture-spike-review.v1"
READY_NEXT_STEP = "runtime_current_line_capture_strategy_decision"
NOT_READY_NEXT_STEP = "repeat_runtime_current_line_capture_spike"


class RuntimeCurrentLineCaptureSpikeReviewError(RuntimeError):
    """Raised when a runtime capture-spike review cannot be built safely."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review redacted runtime current-line capture-spike evidence."
    )
    parser.add_argument("--report", help=f"Report JSON under {REPORT_ROOT}.")
    parser.add_argument("--output", help=f"Optional JSON review under {REVIEW_ROOT}.")
    parser.add_argument("--markdown-output", help=f"Optional Markdown review under {REVIEW_ROOT}.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Runtime current-line capture spike review self-test passed.")
            else:
                print(
                    canonical_json(
                        {
                            "ok": True,
                            "schema_version": "runtime-current-line-capture-spike-self-test.v1",
                        }
                    ),
                    end="",
                )
            return 0
        if not args.report:
            parser.error("--report is required unless --self-test is used.")
        review = build_review(Path(args.report))
        if args.output:
            output = ensure_safe_review_output_path(Path(args.output), ".json")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(canonical_json(review), encoding="utf-8")
        if args.markdown_output:
            output = ensure_safe_review_output_path(Path(args.markdown_output), ".md")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(render_markdown_review(review), encoding="utf-8")
    except Exception as exc:
        if args.quiet:
            print("Runtime current-line capture spike review failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        status = "ready" if review["ready_for_capture_strategy_decision"] else "not ready"
        print(f"Runtime current-line capture spike review {status}.")
    else:
        print(canonical_json(review), end="")
    return 0


def build_review(report_path: Path) -> dict[str, object]:
    safe_report = ensure_safe_report_path(report_path)
    errors = collect_capture_spike_report_errors(safe_report)
    if errors:
        raise RuntimeCurrentLineCaptureSpikeReviewError("; ".join(errors))
    report = load_json(safe_report)
    if not isinstance(report, dict):
        raise RuntimeCurrentLineCaptureSpikeReviewError("Report must be a JSON object.")
    blockers = _readiness_blockers(report)
    ready = not blockers
    return {
        "schema_version": SCHEMA_VERSION,
        "source_report_status": report["spike_status"],
        "plugin_loaded_observed": report["plugin_loaded_observed"],
        "companion_health_checked": report["companion_health_checked"],
        "companion_available": report["companion_available"],
        "runtime_transport_enabled": report["runtime_transport_enabled"],
        "synthetic_runtime_send_configured": report["synthetic_runtime_send_configured"],
        "synthetic_runtime_event_sent_observed": report["synthetic_runtime_event_sent_observed"],
        "companion_received_runtime_event": report["companion_received_runtime_event"],
        "translation_memory_checked": report["translation_memory_checked"],
        "provider_called": False,
        "real_text_capture_implementation_allowed_next": False,
        "hooks_allowed_next": False,
        "ui_text_reading_allowed_next": False,
        "unity_scanning_allowed_next": False,
        "ocr_allowed_next": False,
        "ready_for_capture_strategy_decision": ready,
        "blockers": blockers,
        "recommended_next_step": READY_NEXT_STEP if ready else NOT_READY_NEXT_STEP,
        "logs_read": False,
        "game_files_read": False,
        "screenshots_read": False,
        "provider_called_during_review": False,
    }


def ensure_safe_review_output_path(path: Path, expected_suffix: str) -> Path:
    resolved_root = REVIEW_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeCurrentLineCaptureSpikeReviewError(
            f"Review output path must stay under {REVIEW_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != expected_suffix:
        raise RuntimeCurrentLineCaptureSpikeReviewError(
            f"Review output path must end in {expected_suffix}"
        )
    return resolved


def render_markdown_review(review: dict[str, object]) -> str:
    blockers = review["blockers"]
    blocker_lines = "\n".join(f"- `{item}`" for item in blockers) if blockers else "- None"
    return (
        "# Runtime Current-Line Capture Spike Review\n\n"
        f"- Schema version: `{review['schema_version']}`\n"
        f"- Source report status: `{review['source_report_status']}`\n"
        f"- Ready for strategy decision: "
        f"`{str(review['ready_for_capture_strategy_decision']).lower()}`\n"
        "- Provider called during review: `false`\n"
        "- Logs read: `false`\n"
        "- Game files read: `false`\n"
        "- Screenshots read: `false`\n\n"
        "## Blockers\n\n"
        f"{blocker_lines}\n\n"
        "## Recommended Next Step\n\n"
        f"`{review['recommended_next_step']}`\n"
    )


def run_self_test() -> None:
    report = default_report_template()
    report.update(
        {
            "spike_status": "pass",
            "plugin_loaded_observed": True,
            "companion_health_checked": True,
            "companion_available": True,
            "runtime_transport_enabled": True,
            "synthetic_runtime_send_configured": True,
            "synthetic_runtime_event_sent_observed": True,
            "companion_received_runtime_event": True,
            "translation_memory_checked": True,
            "provider_call_required_observed": True,
            "recommended_next_step": READY_NEXT_STEP,
            "notes_redacted": "Synthetic self-test evidence only.",
            "evidence_summary": "Runtime transport and cache lookup were observed as booleans.",
        }
    )
    path = REPORT_ROOT / "self-test-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(report), encoding="utf-8")
    try:
        review = build_review(path)
        if review["ready_for_capture_strategy_decision"] is not True:
            raise RuntimeCurrentLineCaptureSpikeReviewError("Self-test review was not ready.")
        rendered = canonical_json(review)
        for marker in ("source_text", "LogOutput.log", "HarmonyPatch", "OCR"):
            if marker in rendered:
                raise RuntimeCurrentLineCaptureSpikeReviewError(
                    "Self-test review leaked forbidden evidence."
                )
    finally:
        path.unlink(missing_ok=True)


def _readiness_blockers(report: dict[str, object]) -> list[str]:
    blockers: list[str] = []
    if report.get("spike_status") != "pass":
        blockers.append(f"spike_status_not_pass:{report.get('spike_status')}")
    for field in (
        "plugin_loaded_observed",
        "companion_health_checked",
        "companion_available",
        "runtime_transport_enabled",
        "synthetic_runtime_send_configured",
        "synthetic_runtime_event_sent_observed",
        "companion_received_runtime_event",
        "translation_memory_checked",
    ):
        if report.get(field) is not True:
            blockers.append(f"{field}_not_true")
    if report.get("provider_called") is not False:
        blockers.append("provider_called_not_false")
    if report.get("runtime_current_line_capture_enabled") is not False:
        blockers.append("runtime_current_line_capture_enabled_not_false")
    if report.get("real_text_captured") is not False:
        blockers.append("real_text_captured_not_false")
    return blockers


if __name__ == "__main__":
    sys.exit(main())
