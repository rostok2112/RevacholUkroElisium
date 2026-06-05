from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.check_runtime_targeted_hook_candidate_research_report import (
        ALLOWED_STATUSES,
        FORBIDDEN_TRUE_FIELDS,
        READY_NEXT_STEP as REPORT_READY_NEXT_STEP,
        REPORT_ROOT,
        canonical_json,
        collect_targeted_hook_candidate_research_report_errors,
        default_report_template,
        ensure_safe_report_path,
    )
    from scripts.schema_validator import load_json
except ModuleNotFoundError:  # pragma: no cover
    from check_runtime_targeted_hook_candidate_research_report import (
        ALLOWED_STATUSES,
        FORBIDDEN_TRUE_FIELDS,
        READY_NEXT_STEP as REPORT_READY_NEXT_STEP,
        REPORT_ROOT,
        canonical_json,
        collect_targeted_hook_candidate_research_report_errors,
        default_report_template,
        ensure_safe_report_path,
    )
    from schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = REPORT_ROOT / "review"
DECISION_FIXTURE_PATH = (
    ROOT / "tests/fixtures/runtime_targeted_hook_candidate_research_review_decision.synthetic.json"
)
REVIEW_SCHEMA_VERSION = "runtime-targeted-hook-candidate-research-review.v1"
DECISION_SCHEMA_VERSION = "runtime-targeted-hook-candidate-research-review-decision.v1"
READY_NEXT_STEP = "runtime_targeted_hook_candidate_decision_contract"
REPEAT_NEXT_STEP = "repeat_runtime_targeted_hook_candidate_research_local_report"

FORBIDDEN_REVIEW_MARKERS = (
    "HarmonyPatch",
    "LogOutput.log",
    "Player.log",
    "output_log.txt",
    "source_text",
    "captured text",
    "private runtime text",
    "request payload",
    "response payload",
    "provider payload",
    "screenshot",
    "screen capture",
    "steamapps",
    "decompiled",
    "FindObjectOfType",
    "FindObjectsOfType",
    "GameObject.Find",
    "Resources.FindObjectsOfTypeAll",
    "SceneManager",
    "OCR",
    "Tesseract",
    "api.openai",
    "deepl",
    "anthropic",
)


class RuntimeTargetedHookCandidateResearchReviewError(RuntimeError):
    """Raised when a targeted hook research review cannot be built safely."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review a redacted runtime targeted hook candidate research report."
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
                print("Runtime targeted hook candidate research review self-test passed.")
            else:
                print(
                    canonical_json(
                        {
                            "ok": True,
                            "schema_version": "runtime-targeted-hook-review-self-test.v1",
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
            print("Runtime targeted hook candidate research review failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        status = "ready" if review["ready_for_hook_candidate_decision"] else "not ready"
        print(f"Runtime targeted hook candidate research review {status}.")
    else:
        print(canonical_json(review), end="")
    return 0


def build_review(report_path: Path) -> dict[str, object]:
    safe_report = ensure_safe_report_path(report_path, must_exist=True)
    report_errors = collect_targeted_hook_candidate_research_report_errors(safe_report)
    report = _load_report_or_empty(safe_report)
    blockers = _review_blockers(report, report_errors)
    ready = _is_ready(report, report_errors, blockers)
    review = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "source_report_valid": not report_errors,
        "source_research_status": _safe_status(report.get("research_status")),
        "research_performed_locally": report.get("research_performed_locally") is True,
        "candidate_count": _safe_count(report.get("candidate_count")),
        "candidate_categories_count": _safe_count(report.get("candidate_categories_count")),
        "ready_for_hook_candidate_decision": ready,
        "hook_implementation_allowed_next": False,
        "real_text_capture_allowed_next": False,
        "ui_inspection_allowed_next": False,
        "log_parsing_allowed_next": False,
        "ocr_allowed_next": False,
        "broad_unity_scanning_allowed_next": False,
        "game_file_reads_allowed_next": False,
        "provider_execution_allowed_next": False,
        "companion_contract_change_allowed_next": False,
        "candidate_identifiers_included": False,
        "method_names_included": False,
        "method_signatures_included": False,
        "class_names_included": False,
        "decompiled_identifiers_included": False,
        "raw_logs_included": False,
        "screenshots_included": False,
        "source_text_included": False,
        "payload_dumps_included": False,
        "private_paths_included": False,
        "provider_data_included": False,
        "real_runtime_evidence_included": False,
        "committed_runtime_artifacts_included": False,
        "blockers": blockers,
        "recommended_next_step": READY_NEXT_STEP if ready else REPEAT_NEXT_STEP,
        "source_report_path_redacted": True,
        "review_output_private_only": True,
    }
    _assert_review_redacted(review)
    return review


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load targeted hook research review decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["Targeted hook research review decision fixture must be a JSON object."]
    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("selected_strategy") != "targeted_hook_research_first":
        errors.append("selected_strategy must remain targeted_hook_research_first.")
    if payload.get("review_gate_done") is not True:
        errors.append("review_gate_done must be true.")
    if payload.get("hook_candidate_decision_contract_allowed_next") != "decision_pending":
        errors.append("hook candidate decision contract must remain pending.")
    if payload.get("recommended_next_step") != READY_NEXT_STEP:
        errors.append(f"recommended_next_step must be {READY_NEXT_STEP!r}.")
    for field in (
        "hook_implementation_allowed_next",
        "real_text_capture_allowed_next",
        "ui_inspection_allowed_next",
        "log_parsing_allowed_next",
        "ocr_allowed_next",
        "broad_unity_scanning_allowed_next",
        "game_file_reads_allowed_next",
        "provider_execution_allowed_next",
        "companion_contract_change_allowed_next",
        "candidate_identifiers_included",
        "method_names_included",
        "method_signatures_included",
        "class_names_included",
        "decompiled_identifiers_included",
        "raw_logs_included",
        "screenshots_included",
        "source_text_included",
        "payload_dumps_included",
        "private_paths_included",
        "provider_data_included",
        "real_runtime_evidence_included",
        "committed_runtime_artifacts_included",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false.")
    errors.extend(_unsafe_review_value_errors(payload))
    return _dedupe(errors)


def ensure_safe_review_output_path(path: Path, expected_suffix: str) -> Path:
    _reject_unsafe_path_text(path)
    resolved_root = REVIEW_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeTargetedHookCandidateResearchReviewError(
            f"Review output path must stay under {REVIEW_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != expected_suffix:
        raise RuntimeTargetedHookCandidateResearchReviewError(
            f"Review output path must end in {expected_suffix}"
        )
    return resolved


def render_markdown_review(review: dict[str, object]) -> str:
    blockers = review["blockers"]
    blocker_lines = "\n".join(f"- `{item}`" for item in blockers) if blockers else "- None"
    return (
        "# Runtime Targeted Hook Candidate Research Review\n\n"
        f"- Schema version: `{review['schema_version']}`\n"
        f"- Source report valid: `{str(review['source_report_valid']).lower()}`\n"
        f"- Source research status: `{review['source_research_status']}`\n"
        f"- Research performed locally: "
        f"`{str(review['research_performed_locally']).lower()}`\n"
        f"- Candidate count: `{review['candidate_count']}`\n"
        f"- Candidate categories count: `{review['candidate_categories_count']}`\n"
        f"- Ready for hook candidate decision: "
        f"`{str(review['ready_for_hook_candidate_decision']).lower()}`\n"
        "- Hook implementation allowed next: `false`\n"
        "- Real text capture allowed next: `false`\n"
        "- Provider execution allowed next: `false`\n\n"
        "## Blockers\n\n"
        f"{blocker_lines}\n\n"
        "## Recommended Next Step\n\n"
        f"`{review['recommended_next_step']}`\n"
    )


def run_self_test() -> None:
    decision_errors = collect_decision_fixture_errors()
    if decision_errors:
        raise RuntimeTargetedHookCandidateResearchReviewError("; ".join(decision_errors))
    report = default_report_template()
    report.update(
        {
            "research_status": "pass",
            "research_performed_locally": True,
            "candidate_count": 2,
            "candidate_categories_count": 1,
            "evidence_summary": "Local targeted research was summarized with aggregate counts.",
            "recommended_next_step": REPORT_READY_NEXT_STEP,
        }
    )
    report_path = REPORT_ROOT / "self-test-review-report.json"
    json_path = REVIEW_ROOT / "self-test-review.json"
    markdown_path = REVIEW_ROOT / "self-test-review.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(canonical_json(report), encoding="utf-8")
    try:
        review = build_review(report_path)
        if review["ready_for_hook_candidate_decision"] is not True:
            raise RuntimeTargetedHookCandidateResearchReviewError("Self-test review was not ready.")
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(canonical_json(review), encoding="utf-8")
        markdown_path.write_text(render_markdown_review(review), encoding="utf-8")
        rendered_json = json.loads(json_path.read_text(encoding="utf-8"))
        rendered_values = "\n".join(_iter_string_values(rendered_json)).lower()
        rendered_markdown = markdown_path.read_text(encoding="utf-8").lower()
        for marker in FORBIDDEN_REVIEW_MARKERS:
            lowered = marker.lower()
            if lowered in rendered_values or lowered in rendered_markdown:
                raise RuntimeTargetedHookCandidateResearchReviewError(
                    "Self-test review leaked forbidden runtime evidence."
                )
        if str(REPORT_ROOT) in rendered_values or str(REPORT_ROOT).lower() in rendered_markdown:
            raise RuntimeTargetedHookCandidateResearchReviewError(
                "Self-test review leaked a private report path."
            )
    finally:
        report_path.unlink(missing_ok=True)
        json_path.unlink(missing_ok=True)
        markdown_path.unlink(missing_ok=True)


def _load_report_or_empty(report_path: Path) -> dict[str, Any]:
    try:
        payload = load_json(report_path)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _review_blockers(report: dict[str, Any], report_errors: list[str]) -> list[str]:
    blockers = [_blocker_for_error(error) for error in report_errors]
    if not report_errors:
        blockers.extend(str(item) for item in report.get("blocker_categories", []))
        if report.get("research_status") != "pass":
            blockers.append("research_status_not_pass")
        if report.get("research_performed_locally") is not True:
            blockers.append("local_research_not_confirmed")
        if _safe_count(report.get("candidate_count")) <= 0:
            blockers.append("no_candidate_count")
        if _safe_count(report.get("candidate_categories_count")) <= 0:
            blockers.append("no_candidate_categories")
    return _dedupe(blockers)


def _is_ready(
    report: dict[str, Any],
    report_errors: list[str],
    blockers: list[str],
) -> bool:
    return (
        not report_errors
        and not blockers
        and report.get("research_status") == "pass"
        and report.get("research_performed_locally") is True
        and _safe_count(report.get("candidate_count")) > 0
        and _safe_count(report.get("candidate_categories_count")) > 0
        and all(report.get(field) is False for field in FORBIDDEN_TRUE_FIELDS)
    )


def _blocker_for_error(error: str) -> str:
    lowered = error.lower()
    if "path" in lowered:
        return "unsafe_path_or_private_path"
    if "marker" in lowered or "payload" in lowered or "log" in lowered:
        return "unsafe_runtime_evidence_marker"
    if "secret" in lowered or "url" in lowered:
        return "secret_or_url_detected"
    if "method" in lowered or "identifier" in lowered or "class" in lowered:
        return "candidate_identifier_leak_detected"
    if "must be false" in lowered:
        return "forbidden_capability_enabled"
    if "schema_version" in lowered or "json object" in lowered:
        return "malformed_report"
    return "invalid_report"


def _safe_status(value: object) -> str:
    return value if isinstance(value, str) and value in ALLOWED_STATUSES else "invalid"


def _safe_count(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _assert_review_redacted(review: dict[str, object]) -> None:
    rendered = canonical_json(review)
    errors = _unsafe_review_value_errors(review)
    if errors:
        raise RuntimeTargetedHookCandidateResearchReviewError("; ".join(errors))
    if str(REPORT_ROOT) in rendered or str(REVIEW_ROOT) in rendered:
        raise RuntimeTargetedHookCandidateResearchReviewError(
            "Review output must not include private workspace paths."
        )


def _unsafe_review_value_errors(value: Any) -> list[str]:
    rendered = "\n".join(_iter_string_values(value)).lower()
    return [
        f"Review contains forbidden marker {marker!r}."
        for marker in FORBIDDEN_REVIEW_MARKERS
        if marker.lower() in rendered
    ]


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise RuntimeTargetedHookCandidateResearchReviewError(
            "Unsafe path traversal is not allowed."
        )
    for marker in ("logoutput.log", "player.log", "steamapps", "screenshot", "ocr", "decompiled"):
        if marker in normalized:
            raise RuntimeTargetedHookCandidateResearchReviewError(
                "Path uses a forbidden runtime/private marker."
            )


def _iter_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(_iter_string_values(item))
        return strings
    if isinstance(value, dict):
        strings = []
        for item in value.values():
            strings.extend(_iter_string_values(item))
        return strings
    return []


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


if __name__ == "__main__":
    sys.exit(main())
