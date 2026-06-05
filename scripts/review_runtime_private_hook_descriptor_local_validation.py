from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.run_runtime_private_hook_descriptor_local_validation import (
        DESCRIPTOR_ROOT,
        READY_NEXT_STEP as VALIDATION_READY_NEXT_STEP,
        REPEAT_NEXT_STEP as VALIDATION_REPEAT_NEXT_STEP,
        SUMMARY_FALSE_FIELDS,
        SUMMARY_SCHEMA_VERSION,
        VALIDATION_ROOT,
        canonical_json,
        default_descriptor_template,
        validate_private_hook_descriptor,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover
    from run_runtime_private_hook_descriptor_local_validation import (
        DESCRIPTOR_ROOT,
        READY_NEXT_STEP as VALIDATION_READY_NEXT_STEP,
        REPEAT_NEXT_STEP as VALIDATION_REPEAT_NEXT_STEP,
        SUMMARY_FALSE_FIELDS,
        SUMMARY_SCHEMA_VERSION,
        VALIDATION_ROOT,
        canonical_json,
        default_descriptor_template,
        validate_private_hook_descriptor,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


REVIEW_ROOT = DESCRIPTOR_ROOT / "validation-review"
DECISION_FIXTURE_PATH = (
    ROOT
    / "tests/fixtures/runtime_private_hook_descriptor_local_validation_review_decision.synthetic.json"
)
REVIEW_SCHEMA_VERSION = "runtime-private-hook-descriptor-local-validation-review.v1"
DECISION_SCHEMA_VERSION = "runtime-private-hook-descriptor-local-validation-review-decision.v1"
READY_NEXT_STEP = "runtime_private_hook_implementation_contract"
REPEAT_NEXT_STEP = VALIDATION_REPEAT_NEXT_STEP
ALLOWED_SUMMARY_STATUSES = ("compatible", "incompatible", "decode_failed")

REQUIRED_SUMMARY_BOOL_FIELDS = (
    "descriptor_input_allowed",
    "descriptor_json_decoded",
    "descriptor_object_decoded",
    "descriptor_schema_version_matches",
    "descriptor_kind_valid",
    "selected_strategy_matches",
    "research_review_passed",
    "required_top_level_fields_present",
    "required_top_level_types_match",
    "candidate_object_present",
    "safety_object_present",
    "required_safety_flags_false",
    "descriptor_values_redacted",
    "descriptor_compatible",
    *SUMMARY_FALSE_FIELDS,
)
REQUIRED_SUMMARY_INT_FIELDS = ("candidate_top_level_field_count",)
FORBIDDEN_REVIEW_TRUE_FIELDS = (
    "hook_implementation_allowed_next",
    "real_text_capture_allowed_next",
    "ui_inspection_allowed_next",
    "log_parsing_allowed_next",
    "ocr_allowed_next",
    "broad_unity_scanning_allowed_next",
    "game_file_reads_allowed_next",
    "bepinex_log_parsing_allowed_next",
    "provider_execution_allowed_next",
    "companion_contract_change_allowed_next",
    "committed_runtime_artifacts_allowed",
    "descriptor_path_included",
    "descriptor_filename_included",
    "candidate_identifiers_included",
    "method_names_included",
    "class_names_included",
    "method_signatures_included",
    "decompiled_identifiers_included",
    "source_text_included",
    "payload_dumps_included",
    "raw_logs_included",
    "screenshots_included",
    "provider_data_included",
    "private_paths_included",
    "hashes_included",
    "runtime_evidence_included",
)
FORBIDDEN_REVIEW_MARKERS = (
    "HarmonyPatch",
    "LogOutput.log",
    "Player.log",
    "output_log.txt",
    "source_text",
    "raw_english_text",
    "dialogue text",
    "captured text",
    "private runtime text",
    "request payload",
    "response payload",
    "raw companion payload",
    "provider payload",
    "payload dump",
    "screenshot",
    "screen capture",
    "steamapps",
    "database.json",
    "decompiled",
    "api.openai",
    "deepl",
    "anthropic",
    "PrivateCandidate",
    "BuildRuntimeLineCandidate",
)


class RuntimePrivateHookDescriptorValidationReviewError(RuntimeError):
    """Raised when descriptor validation review cannot proceed safely."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review a redacted runtime private hook descriptor validation summary."
    )
    parser.add_argument("--summary", help=f"Validation summary JSON under {VALIDATION_ROOT}.")
    parser.add_argument("--output", help=f"Optional JSON review under {REVIEW_ROOT}.")
    parser.add_argument("--markdown-output", help=f"Optional Markdown review under {REVIEW_ROOT}.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Runtime private hook descriptor validation review self-test passed.")
            else:
                print(
                    canonical_json(
                        {
                            "ok": True,
                            "schema_version": (
                                "runtime-private-hook-descriptor-validation-review-self-test.v1"
                            ),
                        }
                    ),
                    end="",
                )
            return 0
        if not args.summary:
            parser.error("--summary is required unless --self-test is used.")
        review = build_review(Path(args.summary))
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
            print("Runtime private hook descriptor validation review failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        status = "ready" if review["ready_for_hook_implementation_contract"] else "not ready"
        print(f"Runtime private hook descriptor validation review {status}.")
    else:
        print(canonical_json(review), end="")
    return 0


def build_review(summary_path: Path) -> dict[str, object]:
    safe_summary = ensure_safe_summary_path(summary_path)
    payload = _load_summary(safe_summary)
    summary = payload if isinstance(payload, dict) else {}
    summary_errors = collect_summary_errors(summary)
    blockers = _review_blockers(summary, summary_errors)
    ready = _is_ready(summary, summary_errors, blockers)
    review = {
        "schema_version": REVIEW_SCHEMA_VERSION,
        "summary_valid": not summary_errors,
        "summary_status": _safe_status(summary.get("validation_status")),
        "descriptor_compatible": summary.get("descriptor_compatible") is True,
        "descriptor_json_decoded": summary.get("descriptor_json_decoded") is True,
        "descriptor_object_decoded": summary.get("descriptor_object_decoded") is True,
        "descriptor_schema_version_matches": (
            summary.get("descriptor_schema_version_matches") is True
        ),
        "descriptor_kind_valid": summary.get("descriptor_kind_valid") is True,
        "selected_strategy_matches": summary.get("selected_strategy_matches") is True,
        "research_review_passed": summary.get("research_review_passed") is True,
        "required_top_level_fields_present": (
            summary.get("required_top_level_fields_present") is True
        ),
        "required_top_level_types_match": (summary.get("required_top_level_types_match") is True),
        "candidate_object_present": summary.get("candidate_object_present") is True,
        "candidate_top_level_field_count": _safe_count(
            summary.get("candidate_top_level_field_count")
        ),
        "safety_object_present": summary.get("safety_object_present") is True,
        "required_safety_flags_false": summary.get("required_safety_flags_false") is True,
        "descriptor_values_redacted": summary.get("descriptor_values_redacted") is True,
        "ready_for_hook_implementation_contract": ready,
        "hook_implementation_allowed_next": False,
        "real_text_capture_allowed_next": False,
        "ui_inspection_allowed_next": False,
        "log_parsing_allowed_next": False,
        "ocr_allowed_next": False,
        "broad_unity_scanning_allowed_next": False,
        "game_file_reads_allowed_next": False,
        "bepinex_log_parsing_allowed_next": False,
        "provider_execution_allowed_next": False,
        "companion_contract_change_allowed_next": False,
        "committed_runtime_artifacts_allowed": False,
        "descriptor_path_included": False,
        "descriptor_filename_included": False,
        "candidate_identifiers_included": False,
        "method_names_included": False,
        "class_names_included": False,
        "method_signatures_included": False,
        "decompiled_identifiers_included": False,
        "source_text_included": False,
        "payload_dumps_included": False,
        "raw_logs_included": False,
        "screenshots_included": False,
        "provider_data_included": False,
        "private_paths_included": False,
        "hashes_included": False,
        "runtime_evidence_included": False,
        "blockers": blockers,
        "recommended_next_step": READY_NEXT_STEP if ready else REPEAT_NEXT_STEP,
        "summary_path_redacted": True,
        "review_output_private_only": True,
    }
    _assert_review_redacted(review)
    return review


def collect_summary_errors(summary: Any) -> list[str]:
    if not isinstance(summary, dict):
        return ["summary_json_object_required"]
    errors: list[str] = []
    if summary.get("schema_version") != SUMMARY_SCHEMA_VERSION:
        errors.append("summary_schema_version_mismatch")
    if summary.get("validation_status") not in ALLOWED_SUMMARY_STATUSES:
        errors.append("summary_validation_status_invalid")
    blockers = summary.get("blocker_categories")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        errors.append("summary_blocker_categories_invalid")
    for field in REQUIRED_SUMMARY_BOOL_FIELDS:
        if not isinstance(summary.get(field), bool):
            errors.append(f"{field}_must_be_boolean")
    for field in REQUIRED_SUMMARY_INT_FIELDS:
        if not isinstance(summary.get(field), int) or summary.get(field) < 0:
            errors.append(f"{field}_must_be_non_negative_integer")
    for field in FORBIDDEN_REVIEW_TRUE_FIELDS:
        if summary.get(field) is not False:
            errors.append(f"{field}_must_be_false")
    if summary.get("recommended_next_step") not in (
        VALIDATION_READY_NEXT_STEP,
        REPEAT_NEXT_STEP,
    ):
        errors.append("summary_recommended_next_step_invalid")
    errors.extend(_unsafe_value_errors(summary))
    return _dedupe(errors)


def collect_decision_fixture_errors(path: Path = DECISION_FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load descriptor validation review decision fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["Descriptor validation review decision fixture must be a JSON object."]
    errors: list[str] = []
    if payload.get("schema_version") != DECISION_SCHEMA_VERSION:
        errors.append(f"schema_version must be {DECISION_SCHEMA_VERSION!r}.")
    if payload.get("selected_strategy") != "targeted_hook_research_first":
        errors.append("selected_strategy must remain targeted_hook_research_first.")
    if payload.get("validation_review_gate_done") is not True:
        errors.append("validation_review_gate_done must be true.")
    if payload.get("hook_implementation_contract_allowed_next") != "decision_pending":
        errors.append("hook_implementation_contract_allowed_next must remain decision_pending.")
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
        "bepinex_log_parsing_allowed_next",
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
        "descriptor_reopened_during_review",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false.")
    errors.extend(_unsafe_value_errors(payload))
    return _dedupe(errors)


def ensure_safe_summary_path(path: Path) -> Path:
    _reject_unsafe_path_text(path)
    resolved_root = VALIDATION_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimePrivateHookDescriptorValidationReviewError(
            f"Summary path must stay under {VALIDATION_ROOT.relative_to(ROOT)}"
        ) from exc
    if _is_under(resolved, REVIEW_ROOT.resolve()):
        raise RuntimePrivateHookDescriptorValidationReviewError(
            "Summary path must not be inside review output root."
        )
    if resolved.suffix.lower() != ".json":
        raise RuntimePrivateHookDescriptorValidationReviewError("Summary path must end in .json.")
    if not resolved.exists():
        raise RuntimePrivateHookDescriptorValidationReviewError("Summary path does not exist.")
    raw_path = ROOT / path if not path.is_absolute() else path
    if raw_path.is_symlink() or resolved.is_dir():
        raise RuntimePrivateHookDescriptorValidationReviewError(
            "Summary path must be a regular JSON file."
        )
    return resolved


def ensure_safe_review_output_path(path: Path, expected_suffix: str) -> Path:
    _reject_unsafe_path_text(path)
    resolved_root = REVIEW_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimePrivateHookDescriptorValidationReviewError(
            f"Review output path must stay under {REVIEW_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != expected_suffix:
        raise RuntimePrivateHookDescriptorValidationReviewError(
            f"Review output path must end in {expected_suffix}."
        )
    if resolved.exists() and (resolved.is_symlink() or resolved.is_dir()):
        raise RuntimePrivateHookDescriptorValidationReviewError(
            "Review output path must be a regular file."
        )
    return resolved


def render_markdown_review(review: dict[str, object]) -> str:
    blockers = review["blockers"]
    blocker_lines = "\n".join(f"- `{item}`" for item in blockers) if blockers else "- None"
    return (
        "# Runtime Private Hook Descriptor Validation Review\n\n"
        f"- Schema version: `{review['schema_version']}`\n"
        f"- Summary valid: `{str(review['summary_valid']).lower()}`\n"
        f"- Summary status: `{review['summary_status']}`\n"
        f"- Descriptor compatible: `{str(review['descriptor_compatible']).lower()}`\n"
        f"- Candidate field count: `{review['candidate_top_level_field_count']}`\n"
        f"- Ready for hook implementation contract: "
        f"`{str(review['ready_for_hook_implementation_contract']).lower()}`\n"
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
        raise RuntimePrivateHookDescriptorValidationReviewError("; ".join(decision_errors))
    descriptor = default_descriptor_template()
    descriptor.update(
        {
            "research_review_passed": True,
            "candidate": {
                "private_candidate_alias": "PrivateCandidate.Controller",
                "private_signature_hint": "private string BuildRuntimeLineCandidate()",
                "private_target_category_count": 1,
            },
            "recommended_next_step": "runtime_private_hook_descriptor_local_validation_review_gate",
        }
    )
    descriptor_path = DESCRIPTOR_ROOT / "self-test-review-descriptor.json"
    summary_path = VALIDATION_ROOT / "self-test-review-summary.json"
    json_path = REVIEW_ROOT / "self-test-review.json"
    markdown_path = REVIEW_ROOT / "self-test-review.md"
    descriptor_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor_path.write_text(canonical_json(descriptor), encoding="utf-8")
    try:
        summary = validate_private_hook_descriptor(descriptor_path)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(canonical_json(summary), encoding="utf-8")
        descriptor_path.unlink(missing_ok=True)
        review = build_review(summary_path)
        if review["ready_for_hook_implementation_contract"] is not True:
            raise RuntimePrivateHookDescriptorValidationReviewError(
                "Self-test review was not ready."
            )
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(canonical_json(review), encoding="utf-8")
        markdown_path.write_text(render_markdown_review(review), encoding="utf-8")
        rendered_json = json.loads(json_path.read_text(encoding="utf-8"))
        rendered_values = "\n".join(_iter_string_values(rendered_json)).lower()
        rendered_markdown = markdown_path.read_text(encoding="utf-8").lower()
        for marker in FORBIDDEN_REVIEW_MARKERS:
            lowered = marker.lower()
            if lowered in rendered_values or lowered in rendered_markdown:
                raise RuntimePrivateHookDescriptorValidationReviewError(
                    "Self-test review leaked forbidden runtime evidence."
                )
    finally:
        descriptor_path.unlink(missing_ok=True)
        summary_path.unlink(missing_ok=True)
        json_path.unlink(missing_ok=True)
        markdown_path.unlink(missing_ok=True)


def _load_summary(summary_path: Path) -> Any:
    try:
        return load_json(summary_path)
    except Exception as exc:
        raise RuntimePrivateHookDescriptorValidationReviewError(
            "Summary JSON could not be decoded."
        ) from exc


def _review_blockers(summary: dict[str, Any], summary_errors: list[str]) -> list[str]:
    blockers = [_blocker_for_error(error) for error in summary_errors]
    if not summary_errors:
        blockers.extend(str(item) for item in summary.get("blocker_categories", []))
        if summary.get("validation_status") != "compatible":
            blockers.append("summary_status_not_compatible")
        for field in (
            "descriptor_compatible",
            "research_review_passed",
            "required_top_level_fields_present",
            "required_top_level_types_match",
            "required_safety_flags_false",
            "descriptor_values_redacted",
        ):
            if summary.get(field) is not True:
                blockers.append(f"{field}_not_true")
    return _dedupe(blockers)


def _is_ready(
    summary: dict[str, Any],
    summary_errors: list[str],
    blockers: list[str],
) -> bool:
    return (
        not summary_errors
        and not blockers
        and summary.get("validation_status") == "compatible"
        and summary.get("descriptor_compatible") is True
        and summary.get("research_review_passed") is True
        and summary.get("required_top_level_fields_present") is True
        and summary.get("required_top_level_types_match") is True
        and summary.get("required_safety_flags_false") is True
        and summary.get("descriptor_values_redacted") is True
        and all(summary.get(field) is False for field in FORBIDDEN_REVIEW_TRUE_FIELDS)
    )


def _blocker_for_error(error: str) -> str:
    lowered = error.lower()
    if "path" in lowered:
        return "unsafe_path_or_private_path"
    if "marker" in lowered or "payload" in lowered or "log" in lowered:
        return "unsafe_runtime_evidence_marker"
    if "secret" in lowered or "url" in lowered:
        return "secret_or_url_detected"
    if "must_be_false" in lowered or "must be false" in lowered:
        return "forbidden_capability_enabled"
    if "schema" in lowered or "json_object" in lowered:
        return "malformed_summary"
    if "status" in lowered:
        return "summary_status_invalid"
    return "invalid_summary"


def _safe_status(value: object) -> str:
    return value if isinstance(value, str) and value in ALLOWED_SUMMARY_STATUSES else "invalid"


def _safe_count(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _assert_review_redacted(review: dict[str, object]) -> None:
    rendered = canonical_json(review)
    if str(VALIDATION_ROOT) in rendered or str(REVIEW_ROOT) in rendered:
        raise RuntimePrivateHookDescriptorValidationReviewError(
            "Review output must not include private workspace paths."
        )
    errors = _unsafe_value_errors(review)
    if errors:
        raise RuntimePrivateHookDescriptorValidationReviewError("; ".join(errors))


def _unsafe_value_errors(value: Any) -> list[str]:
    rendered = "\n".join(_iter_string_values(value)).lower()
    return [
        f"Review contains forbidden marker {marker!r}."
        for marker in FORBIDDEN_REVIEW_MARKERS
        if marker.lower() in rendered
    ]


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise RuntimePrivateHookDescriptorValidationReviewError(
            "Unsafe path traversal is not allowed."
        )
    for marker in (
        "logoutput.log",
        "player.log",
        "steamapps",
        "screenshot",
        "screen-capture",
        "ocr",
        "payload",
        "provider",
    ):
        if marker in normalized:
            raise RuntimePrivateHookDescriptorValidationReviewError(
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


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


if __name__ == "__main__":
    sys.exit(main())
