from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    from scripts.schema_validator import load_json
except ModuleNotFoundError:  # pragma: no cover
    from schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = (
    ROOT / "tests/fixtures/runtime_targeted_hook_candidate_research_report.synthetic.json"
)
REPORT_ROOT = ROOT / "workspace/local-private/runtime-capture/hook-research"
SCHEMA_VERSION = "runtime-targeted-hook-candidate-research-report.v1"
SELECTED_STRATEGY = "targeted_hook_research_first"
READY_NEXT_STEP = "runtime_targeted_hook_candidate_research_review_gate"
REPEAT_NEXT_STEP = "runtime_targeted_hook_candidate_research_local_report"
ALLOWED_STATUSES = ("not_run", "pass", "partial", "fail")

REQUIRED_STRING_FIELDS = (
    "schema_version",
    "selected_strategy",
    "research_status",
    "recommended_next_step",
    "notes_redacted",
    "evidence_summary",
)
REQUIRED_INTEGER_FIELDS = ("candidate_count", "candidate_categories_count")
REQUIRED_BOOL_FIELDS = (
    "research_performed_locally",
    "evidence_summary_redacted",
    "created_by_user_manually",
    "hook_implementation_used",
    "real_text_capture_used",
    "ui_inspection_used",
    "log_parsing_used",
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
    "ocr_used",
    "broad_unity_scanning_used",
    "game_file_reads_used",
    "bepinex_log_parsing_used",
    "provider_execution_used",
    "companion_contract_change_used",
    "committed_runtime_artifacts_included",
)
FORBIDDEN_TRUE_FIELDS = tuple(
    field
    for field in REQUIRED_BOOL_FIELDS
    if field
    not in (
        "research_performed_locally",
        "evidence_summary_redacted",
        "created_by_user_manually",
    )
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
METHOD_SIGNATURE_PATTERN = re.compile(
    r"\b(?:public|private|internal|protected|static|virtual|override|void|string|bool|int)\s+"
    r"[A-Za-z_][A-Za-z0-9_]*\s*\(",
    re.IGNORECASE,
)
QUALIFIED_IDENTIFIER_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z0-9_]{2,}\.(?:[A-Z][A-Za-z0-9_]{2,}|[a-z][A-Za-z0-9_]{2,})\b"
)

FORBIDDEN_REPORT_MARKERS = (
    "HarmonyPatch",
    "[HarmonyPatch",
    "LogOutput.log",
    "Player.log",
    "output_log.txt",
    "stack trace",
    "Traceback (most recent call last)",
    "request payload",
    "response payload",
    "raw companion payload",
    "provider payload",
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
    "steamapps",
    "database.json",
    "game hook",
    "method hook",
    "decompiled",
    "FindObjectOfType",
    "FindObjectsOfType",
    "GameObject.Find",
    "Resources.FindObjectsOfTypeAll",
    "SceneManager",
    "OCR",
    "Tesseract",
    "provider execution",
    "api.openai",
    "deepl",
    "anthropic",
    "local_model",
)


class RuntimeTargetedHookCandidateResearchReportError(RuntimeError):
    """Raised when a runtime targeted hook research report path is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a redacted runtime targeted hook candidate research report."
    )
    parser.add_argument("--report", help=f"Optional report JSON under {REPORT_ROOT}.")
    parser.add_argument("--write-template", help=f"Write a redacted template under {REPORT_ROOT}.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            run_self_test()
            if args.quiet:
                print("Runtime targeted hook candidate research report self-test passed.")
            else:
                print(
                    canonical_json(
                        {
                            "ok": True,
                            "schema_version": "runtime-targeted-hook-report-self-test.v1",
                        }
                    ),
                    end="",
                )
            return 0

        if args.write_template:
            output = ensure_safe_report_path(Path(args.write_template), must_exist=False)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(canonical_json(default_report_template()), encoding="utf-8")
            if args.quiet:
                print("Runtime targeted hook candidate research report template written.")
            else:
                print(
                    canonical_json(
                        {
                            "ok": True,
                            "schema_version": "runtime-targeted-hook-report-template-write.v1",
                            "output": _safe_report_path(output),
                        }
                    ),
                    end="",
                )
            return 0

        report_path = FIXTURE_PATH
        if args.report:
            report_path = ensure_safe_report_path(Path(args.report), must_exist=True)

        errors = collect_targeted_hook_candidate_research_report_errors(report_path)
    except RuntimeTargetedHookCandidateResearchReportError as exc:
        if args.quiet:
            print("Runtime targeted hook candidate research report check failed.")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if errors:
        if args.quiet:
            print("Runtime targeted hook candidate research report check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("Runtime targeted hook candidate research report check passed.")
    else:
        print(
            canonical_json(
                {
                    "ok": True,
                    "schema_version": "runtime-targeted-hook-report-check.v1",
                    "report": _safe_report_path(report_path),
                    "workspace_report_root": str(REPORT_ROOT.relative_to(ROOT)),
                }
            ),
            end="",
        )
    return 0


def collect_targeted_hook_candidate_research_report_errors(
    path: Path = FIXTURE_PATH,
) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load runtime targeted hook research report {path}: {exc}"]
    if not isinstance(payload, dict):
        return ["Runtime targeted hook research report must be a JSON object."]
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload))
    return errors


def ensure_safe_report_path(path: Path, *, must_exist: bool) -> Path:
    resolved_root = REPORT_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeTargetedHookCandidateResearchReportError(
            f"Report path must stay under {REPORT_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != ".json":
        raise RuntimeTargetedHookCandidateResearchReportError("Report path must end in .json")
    if must_exist and not resolved.exists():
        raise RuntimeTargetedHookCandidateResearchReportError("Report path does not exist")
    return resolved


def default_report_template() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "selected_strategy": SELECTED_STRATEGY,
        "research_status": "not_run",
        "research_performed_locally": False,
        "candidate_count": 0,
        "candidate_categories_count": 0,
        "blocker_categories": [],
        "notes_redacted": "Template only. No local hook research evidence is attached.",
        "evidence_summary": "Use redacted booleans, counts, statuses, and blockers only.",
        "evidence_summary_redacted": True,
        "created_by_user_manually": True,
        **{field: False for field in FORBIDDEN_TRUE_FIELDS},
        "recommended_next_step": REPEAT_NEXT_STEP,
    }


def canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def run_self_test() -> None:
    report = default_report_template()
    report.update(
        {
            "research_status": "pass",
            "research_performed_locally": True,
            "candidate_count": 2,
            "candidate_categories_count": 1,
            "evidence_summary": "Local targeted research was summarized with aggregate counts.",
            "recommended_next_step": READY_NEXT_STEP,
        }
    )
    path = REPORT_ROOT / "self-test-report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(report), encoding="utf-8")
    try:
        errors = collect_targeted_hook_candidate_research_report_errors(path)
        if errors:
            raise RuntimeTargetedHookCandidateResearchReportError("; ".join(errors))
        rendered = canonical_json(report)
        for marker in ("LogOutput.log", "HarmonyPatch", "Candidate.Controller"):
            if marker in rendered:
                raise RuntimeTargetedHookCandidateResearchReportError(
                    "Self-test report leaked forbidden evidence."
                )
    finally:
        path.unlink(missing_ok=True)


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_STRING_FIELDS:
        if not isinstance(payload.get(field), str) or not payload.get(field):
            errors.append(f"Runtime targeted hook report field {field!r} must be a string.")
    for field in REQUIRED_INTEGER_FIELDS:
        if not isinstance(payload.get(field), int) or payload.get(field) < 0:
            errors.append(
                f"Runtime targeted hook report field {field!r} must be a non-negative integer."
            )
    for field in REQUIRED_BOOL_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Runtime targeted hook report field {field!r} must be a boolean.")
    blockers = payload.get("blocker_categories")
    if not isinstance(blockers, list) or not all(isinstance(item, str) for item in blockers):
        errors.append(
            "Runtime targeted hook report field 'blocker_categories' must be a string list."
        )

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("selected_strategy") != SELECTED_STRATEGY:
        errors.append(f"selected_strategy must be {SELECTED_STRATEGY!r}.")
    if payload.get("research_status") not in ALLOWED_STATUSES:
        errors.append("research_status must be not_run, pass, partial, or fail.")
    if payload.get("evidence_summary_redacted") is not True:
        errors.append("evidence_summary_redacted must be true.")
    if payload.get("created_by_user_manually") is not True:
        errors.append("created_by_user_manually must be true.")
    for field in FORBIDDEN_TRUE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"{field} must be false.")

    structurally_ready = _is_structurally_ready(payload)
    expected_next = READY_NEXT_STEP if structurally_ready else REPEAT_NEXT_STEP
    if payload.get("recommended_next_step") != expected_next:
        errors.append(f"recommended_next_step must be {expected_next!r}.")
    if payload.get("research_status") == "not_run" and payload.get("research_performed_locally"):
        errors.append("research_performed_locally must be false when research_status is not_run.")
    if (
        payload.get("research_status") != "not_run"
        and payload.get("research_performed_locally") is not True
    ):
        errors.append(
            "research_performed_locally must be true when research_status is pass, partial, or fail."
        )
    if (
        isinstance(payload.get("candidate_categories_count"), int)
        and isinstance(payload.get("candidate_count"), int)
        and payload["candidate_categories_count"] > payload["candidate_count"]
    ):
        errors.append("candidate_categories_count must not exceed candidate_count.")
    return errors


def _is_structurally_ready(payload: dict[str, Any]) -> bool:
    return (
        payload.get("research_status") in {"pass", "partial", "fail"}
        and payload.get("research_performed_locally") is True
    )


def _safety_errors(payload: dict[str, Any]) -> list[str]:
    rendered = "\n".join(_iter_string_values(payload))
    errors: list[str] = []
    if URL_PATTERN.search(rendered):
        errors.append("Report contains a URL.")
    if SECRET_VALUE_PATTERN.search(rendered):
        errors.append("Report contains a secret/API-key-looking value.")
    if PRIVATE_PATH_PATTERN.search(rendered):
        errors.append("Report contains a private absolute path.")
    if METHOD_SIGNATURE_PATTERN.search(rendered):
        errors.append("Report contains a method-signature-looking value.")
    if QUALIFIED_IDENTIFIER_PATTERN.search(rendered):
        errors.append("Report contains a qualified identifier-looking value.")
    lowered = rendered.lower()
    for marker in FORBIDDEN_REPORT_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"Report contains forbidden marker {marker!r}.")
    return errors


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


def _safe_report_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return f"<local:{path.name}>"


if __name__ == "__main__":
    sys.exit(main())
