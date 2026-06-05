from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover
    from schema_validator import load_json
    from synthetic_slice import ROOT


DESCRIPTOR_ROOT = ROOT / "workspace/local-private/runtime-capture/hook-descriptors"
VALIDATION_ROOT = DESCRIPTOR_ROOT / "validation"
DESCRIPTOR_SCHEMA_VERSION = "runtime-private-hook-descriptor.v1"
SUMMARY_SCHEMA_VERSION = "runtime-private-hook-descriptor-local-validation-summary.v1"
DESCRIPTOR_KIND = "targeted_hook_candidate_private_descriptor"
SELECTED_STRATEGY = "targeted_hook_research_first"
READY_NEXT_STEP = "runtime_private_hook_descriptor_local_validation_review_gate"
REPEAT_NEXT_STEP = "repeat_runtime_private_hook_descriptor_local_validation"

REQUIRED_TOP_LEVEL_FIELDS = (
    "schema_version",
    "descriptor_kind",
    "selected_strategy",
    "research_review_passed",
    "candidate",
    "safety",
    "recommended_next_step",
)
REQUIRED_SAFETY_FALSE_FIELDS = (
    "hook_implementation_enabled",
    "real_text_capture_enabled",
    "ui_inspection_enabled",
    "log_parsing_enabled",
    "ocr_enabled",
    "broad_unity_scanning_enabled",
    "game_file_reads_enabled",
    "bepinex_log_parsing_enabled",
    "provider_execution_enabled",
    "companion_contract_change_enabled",
    "screenshots_included",
    "raw_logs_included",
    "payload_dumps_included",
    "source_text_included",
    "private_paths_included",
    "provider_data_included",
    "real_runtime_evidence_included",
    "committed_runtime_artifacts_included",
    "descriptor_values_publicly_emitted",
    "descriptor_values_hashed",
    "descriptor_values_normalized",
    "descriptor_values_committed",
)
SUMMARY_FALSE_FIELDS = (
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
)

URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
PRIVATE_PATH_PATTERN = re.compile(
    r"(\b[A-Za-z]:[\\/](?:Users|Program Files|Games|Steam|GOG|AppData)[\\/]|"
    r"/(?:home|Users|mnt|Volumes|Applications)/)",
    re.IGNORECASE,
)
FORBIDDEN_DESCRIPTOR_MARKERS = (
    "LogOutput.log",
    "Player.log",
    "output_log.txt",
    "stack trace",
    "Traceback (most recent call last)",
    "request payload",
    "response payload",
    "raw companion payload",
    "provider payload",
    "payload dump",
    "source_text",
    "raw_english_text",
    "dialogue text",
    "captured text",
    "private runtime text",
    ".png",
    ".jpg",
    ".jpeg",
    "screenshot",
    "screen capture",
    "database.json",
    "steamapps",
    "api.openai",
    "deepl",
    "anthropic",
    "local_model",
)


class RuntimePrivateHookDescriptorValidationError(RuntimeError):
    """Raised when descriptor validation cannot safely proceed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one explicit private runtime hook descriptor."
    )
    parser.add_argument("--descriptor", help=f"Descriptor JSON under {DESCRIPTOR_ROOT}.")
    parser.add_argument("--output", help=f"Optional redacted summary JSON under {VALIDATION_ROOT}.")
    parser.add_argument(
        "--write-template",
        help=f"Write a private descriptor template JSON under {DESCRIPTOR_ROOT}.",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Runtime private hook descriptor local validation self-test passed.")
            else:
                print(
                    canonical_json(
                        {
                            "ok": True,
                            "schema_version": (
                                "runtime-private-hook-descriptor-local-validation-self-test.v1"
                            ),
                        }
                    ),
                    end="",
                )
            return 0

        if args.write_template:
            template_path = ensure_safe_descriptor_path(Path(args.write_template), must_exist=False)
            template_path.parent.mkdir(parents=True, exist_ok=True)
            template_path.write_text(
                canonical_json(default_descriptor_template()), encoding="utf-8"
            )
            if args.quiet:
                print("Runtime private hook descriptor template written.")
            else:
                print(
                    canonical_json(
                        {
                            "ok": True,
                            "schema_version": ("runtime-private-hook-descriptor-template-write.v1"),
                            "output_path_redacted": True,
                        }
                    ),
                    end="",
                )
            return 0

        if not args.descriptor:
            parser.error("--descriptor is required unless --self-test or --write-template is used.")

        summary = validate_private_hook_descriptor(Path(args.descriptor))
        if args.output:
            output_path = ensure_safe_validation_output_path(Path(args.output))
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(canonical_json(summary), encoding="utf-8")
    except Exception as exc:
        if args.quiet:
            print("Runtime private hook descriptor local validation failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        print(f"Runtime private hook descriptor local validation {summary['validation_status']}.")
    else:
        print(canonical_json(summary), end="")
    return 0


def validate_private_hook_descriptor(path: Path) -> dict[str, object]:
    descriptor_path = ensure_safe_descriptor_path(path, must_exist=True)
    payload: Any
    decoded = False
    try:
        payload = load_json(descriptor_path)
        decoded = True
    except Exception:
        payload = None
    errors = collect_private_hook_descriptor_validation_errors(payload)
    blocker_categories = _blockers_for_errors(errors)
    if not decoded:
        blocker_categories = _dedupe(["json_decode_failed", *blocker_categories])
    status = _validation_status(decoded, errors)
    summary = _summary_for_payload(payload if decoded else None, status, blocker_categories)
    _assert_summary_redacted(summary)
    return summary


def collect_private_hook_descriptor_validation_errors(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["descriptor_json_object_required"]
    errors: list[str] = []
    errors.extend(_top_level_shape_errors(payload))
    errors.extend(_safety_shape_errors(payload.get("safety")))
    errors.extend(_unsafe_descriptor_value_errors(payload))
    return _dedupe(errors)


def ensure_safe_descriptor_path(path: Path, *, must_exist: bool) -> Path:
    resolved_root = DESCRIPTOR_ROOT.resolve()
    raw_path = ROOT / path if not path.is_absolute() else path
    resolved = raw_path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimePrivateHookDescriptorValidationError(
            f"Descriptor path must stay under {DESCRIPTOR_ROOT.relative_to(ROOT)}"
        ) from exc
    if _is_under(resolved, VALIDATION_ROOT.resolve()):
        raise RuntimePrivateHookDescriptorValidationError(
            "Descriptor/template path must not be inside validation output root."
        )
    if resolved.suffix.lower() != ".json":
        raise RuntimePrivateHookDescriptorValidationError("Descriptor path must end in .json.")
    _reject_unsafe_path_text(path)
    if must_exist:
        if not resolved.exists():
            raise RuntimePrivateHookDescriptorValidationError("Descriptor path does not exist.")
        if raw_path.is_symlink():
            raise RuntimePrivateHookDescriptorValidationError(
                "Descriptor path must not be symlink."
            )
        if resolved.is_dir():
            raise RuntimePrivateHookDescriptorValidationError("Descriptor path must be a file.")
    return resolved


def ensure_safe_validation_output_path(path: Path) -> Path:
    resolved_root = VALIDATION_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimePrivateHookDescriptorValidationError(
            f"Validation output path must stay under {VALIDATION_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != ".json":
        raise RuntimePrivateHookDescriptorValidationError(
            "Validation output path must end in .json."
        )
    _reject_unsafe_path_text(path)
    if resolved.exists() and (resolved.is_symlink() or resolved.is_dir()):
        raise RuntimePrivateHookDescriptorValidationError(
            "Validation output path must be a regular JSON file."
        )
    return resolved


def default_descriptor_template() -> dict[str, object]:
    return {
        "schema_version": DESCRIPTOR_SCHEMA_VERSION,
        "descriptor_kind": DESCRIPTOR_KIND,
        "selected_strategy": SELECTED_STRATEGY,
        "research_review_passed": False,
        "candidate": {
            "private_candidate_metadata_placeholder": "replace locally under ignored workspace",
            "private_target_category_count": 1,
        },
        "safety": {field: False for field in REQUIRED_SAFETY_FALSE_FIELDS},
        "recommended_next_step": REPEAT_NEXT_STEP,
    }


def canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def run_self_test() -> None:
    descriptor = default_descriptor_template()
    descriptor.update(
        {
            "research_review_passed": True,
            "candidate": {
                "private_candidate_alias": "PrivateCandidate.Controller",
                "private_signature_hint": "private string BuildRuntimeLineCandidate()",
                "private_target_category_count": 1,
            },
            "recommended_next_step": READY_NEXT_STEP,
        }
    )
    descriptor_path = DESCRIPTOR_ROOT / "self-test-private-descriptor.json"
    summary_path = VALIDATION_ROOT / "self-test-summary.json"
    descriptor_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor_path.write_text(canonical_json(descriptor), encoding="utf-8")
    try:
        summary = validate_private_hook_descriptor(descriptor_path)
        if summary["validation_status"] != "compatible":
            raise RuntimePrivateHookDescriptorValidationError(
                "Self-test descriptor did not validate."
            )
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(canonical_json(summary), encoding="utf-8")
        rendered = summary_path.read_text(encoding="utf-8")
        for marker in (
            "PrivateCandidate",
            "BuildRuntimeLineCandidate",
            str(DESCRIPTOR_ROOT),
            descriptor_path.name,
        ):
            if marker in rendered:
                raise RuntimePrivateHookDescriptorValidationError(
                    "Self-test summary leaked private descriptor evidence."
                )
    finally:
        descriptor_path.unlink(missing_ok=True)
        summary_path.unlink(missing_ok=True)


def _top_level_shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    keys = set(payload)
    required = set(REQUIRED_TOP_LEVEL_FIELDS)
    missing = sorted(required - keys)
    extra = sorted(keys - required)
    if missing:
        errors.append("required_top_level_fields_missing")
    if extra:
        errors.append("unknown_top_level_fields_present")
    for field in (
        "schema_version",
        "descriptor_kind",
        "selected_strategy",
        "recommended_next_step",
    ):
        if not isinstance(payload.get(field), str) or not payload.get(field):
            errors.append(f"{field}_must_be_string")
    if payload.get("schema_version") != DESCRIPTOR_SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    if payload.get("descriptor_kind") != DESCRIPTOR_KIND:
        errors.append("descriptor_kind_mismatch")
    if payload.get("selected_strategy") != SELECTED_STRATEGY:
        errors.append("selected_strategy_mismatch")
    if payload.get("research_review_passed") is not True:
        errors.append("research_review_not_passed")
    if not isinstance(payload.get("candidate"), dict) or not payload.get("candidate"):
        errors.append("candidate_object_required")
    expected_next = READY_NEXT_STEP if _ready_descriptor_shape(payload) else REPEAT_NEXT_STEP
    if payload.get("recommended_next_step") != expected_next:
        errors.append("recommended_next_step_mismatch")
    return errors


def _safety_shape_errors(safety: Any) -> list[str]:
    if not isinstance(safety, dict):
        return ["safety_object_required"]
    errors: list[str] = []
    keys = set(safety)
    required = set(REQUIRED_SAFETY_FALSE_FIELDS)
    if keys != required:
        errors.append("safety_fields_mismatch")
    for field in REQUIRED_SAFETY_FALSE_FIELDS:
        if safety.get(field) is not False:
            errors.append(f"{field}_must_be_false")
    return errors


def _ready_descriptor_shape(payload: dict[str, Any]) -> bool:
    return (
        payload.get("schema_version") == DESCRIPTOR_SCHEMA_VERSION
        and payload.get("descriptor_kind") == DESCRIPTOR_KIND
        and payload.get("selected_strategy") == SELECTED_STRATEGY
        and payload.get("research_review_passed") is True
        and isinstance(payload.get("candidate"), dict)
        and bool(payload.get("candidate"))
        and isinstance(payload.get("safety"), dict)
        and all(payload["safety"].get(field) is False for field in REQUIRED_SAFETY_FALSE_FIELDS)
        and set(payload["safety"]) == set(REQUIRED_SAFETY_FALSE_FIELDS)
    )


def _unsafe_descriptor_value_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for value in _iter_string_values(payload):
        if value in {
            DESCRIPTOR_SCHEMA_VERSION,
            DESCRIPTOR_KIND,
            SELECTED_STRATEGY,
            READY_NEXT_STEP,
            REPEAT_NEXT_STEP,
            *REQUIRED_TOP_LEVEL_FIELDS,
            *REQUIRED_SAFETY_FALSE_FIELDS,
        }:
            continue
        if URL_PATTERN.search(value):
            errors.append("url_detected")
        if SECRET_VALUE_PATTERN.search(value):
            errors.append("secret_value_detected")
        if PRIVATE_PATH_PATTERN.search(value):
            errors.append("private_path_detected")
        lowered = value.lower()
        for marker in FORBIDDEN_DESCRIPTOR_MARKERS:
            if marker.lower() in lowered:
                errors.append(f"forbidden_marker_detected:{marker}")
    return errors


def _summary_for_payload(
    payload: Any,
    status: str,
    blocker_categories: list[str],
) -> dict[str, object]:
    descriptor = payload if isinstance(payload, dict) else {}
    candidate = descriptor.get("candidate") if isinstance(descriptor.get("candidate"), dict) else {}
    safety = descriptor.get("safety") if isinstance(descriptor.get("safety"), dict) else {}
    compatible = status == "compatible"
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "descriptor_input_allowed": True,
        "descriptor_json_decoded": isinstance(payload, dict),
        "descriptor_object_decoded": isinstance(payload, dict),
        "descriptor_schema_version_matches": (
            descriptor.get("schema_version") == DESCRIPTOR_SCHEMA_VERSION
        ),
        "descriptor_kind_valid": descriptor.get("descriptor_kind") == DESCRIPTOR_KIND,
        "selected_strategy_matches": descriptor.get("selected_strategy") == SELECTED_STRATEGY,
        "research_review_passed": descriptor.get("research_review_passed") is True,
        "required_top_level_fields_present": set(REQUIRED_TOP_LEVEL_FIELDS).issubset(
            set(descriptor)
        ),
        "required_top_level_types_match": _top_level_types_match(descriptor),
        "candidate_object_present": bool(candidate),
        "candidate_top_level_field_count": len(candidate),
        "safety_object_present": bool(safety),
        "required_safety_flags_false": _safety_flags_false(safety),
        "descriptor_values_redacted": True,
        "validation_status": status,
        "descriptor_compatible": compatible,
        "blocker_categories": blocker_categories,
        **{field: False for field in SUMMARY_FALSE_FIELDS},
        "recommended_next_step": READY_NEXT_STEP if compatible else REPEAT_NEXT_STEP,
    }
    return summary


def _top_level_types_match(descriptor: dict[str, Any]) -> bool:
    return (
        isinstance(descriptor.get("schema_version"), str)
        and isinstance(descriptor.get("descriptor_kind"), str)
        and isinstance(descriptor.get("selected_strategy"), str)
        and isinstance(descriptor.get("research_review_passed"), bool)
        and isinstance(descriptor.get("candidate"), dict)
        and isinstance(descriptor.get("safety"), dict)
        and isinstance(descriptor.get("recommended_next_step"), str)
    )


def _safety_flags_false(safety: dict[str, Any]) -> bool:
    return set(safety) == set(REQUIRED_SAFETY_FALSE_FIELDS) and all(
        safety.get(field) is False for field in REQUIRED_SAFETY_FALSE_FIELDS
    )


def _validation_status(decoded: bool, errors: list[str]) -> str:
    if not decoded:
        return "decode_failed"
    return "incompatible" if errors else "compatible"


def _blockers_for_errors(errors: list[str]) -> list[str]:
    blockers: list[str] = []
    for error in errors:
        lowered = error.lower()
        if "decode" in lowered or "json_object" in lowered:
            blockers.append("malformed_descriptor")
        elif "safety" in lowered or "must_be_false" in lowered:
            blockers.append("forbidden_capability_enabled")
        elif "marker" in lowered or "payload" in lowered or "log" in lowered:
            blockers.append("unsafe_runtime_evidence_marker")
        elif "secret" in lowered or "url" in lowered:
            blockers.append("secret_or_url_detected")
        elif "path" in lowered:
            blockers.append("private_or_unsafe_path_detected")
        elif "candidate" in lowered:
            blockers.append("candidate_shape_invalid")
        elif "research_review" in lowered:
            blockers.append("prior_review_not_confirmed")
        else:
            blockers.append("descriptor_shape_invalid")
    return _dedupe(blockers)


def _assert_summary_redacted(summary: dict[str, object]) -> None:
    rendered = canonical_json(summary)
    if str(DESCRIPTOR_ROOT) in rendered or str(VALIDATION_ROOT) in rendered:
        raise RuntimePrivateHookDescriptorValidationError(
            "Summary must not include private workspace paths."
        )
    for marker in (
        "HarmonyPatch",
        "LogOutput.log",
        "Player.log",
        "provider payload",
        "PrivateCandidate",
        "BuildRuntimeLineCandidate",
    ):
        if marker.lower() in rendered.lower():
            raise RuntimePrivateHookDescriptorValidationError(
                "Summary leaked private or forbidden runtime evidence."
            )


def _reject_unsafe_path_text(path: Path) -> None:
    normalized = str(path).replace("\\", "/").lower()
    if ".." in Path(normalized).parts or normalized.startswith("../"):
        raise RuntimePrivateHookDescriptorValidationError("Unsafe path traversal is not allowed.")
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
            raise RuntimePrivateHookDescriptorValidationError(
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
        for key, item in value.items():
            strings.extend(_iter_string_values(key))
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
