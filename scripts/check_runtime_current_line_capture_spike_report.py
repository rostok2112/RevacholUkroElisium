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
FIXTURE_PATH = ROOT / "tests/fixtures/runtime_current_line_capture_spike_report.synthetic.json"
REPORT_ROOT = ROOT / "workspace/local-private/runtime-current-line-capture-spike"
SCHEMA_VERSION = "runtime-current-line-capture-spike-report.v1"
ALLOWED_STATUSES = ("not_run", "pass", "partial", "fail")

REQUIRED_BOOL_FIELDS = (
    "plugin_loaded_observed",
    "companion_health_checked",
    "companion_available",
    "runtime_transport_enabled",
    "synthetic_runtime_send_configured",
    "synthetic_runtime_event_sent_observed",
    "companion_received_runtime_event",
    "translation_memory_checked",
    "provider_call_required_observed",
    "provider_called",
    "runtime_current_line_capture_enabled",
    "real_text_captured",
    "hooks_used",
    "ui_text_reading_used",
    "unity_scanning_used",
    "game_file_reads",
    "bepinex_log_reads_in_repo",
    "screenshots_included",
    "raw_logs_included",
    "raw_payloads_included",
    "private_paths_included",
    "created_by_user_manually",
    "evidence_summary_redacted",
)
REQUIRED_STRING_FIELDS = (
    "schema_version",
    "spike_status",
    "recommended_next_step",
    "notes_redacted",
    "evidence_summary",
)
OPTIONAL_STRING_LIST_FIELDS = ("blockers",)

URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:(?:\\\\|\\)(?:Users|Program Files|Games|Steam|GOG)(?:\\\\|\\)"
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")

FORBIDDEN_REPORT_MARKERS = (
    "LogOutput.log",
    "Player.log",
    "output_log.txt",
    "stack trace",
    "Traceback (most recent call last)",
    "request payload",
    "response payload",
    "raw companion payload",
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
    "HarmonyPatch",
    "game hook",
    "method hook",
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


class RuntimeCurrentLineCaptureSpikeReportError(RuntimeError):
    """Raised when a runtime current-line capture-spike report is unsafe."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a redacted runtime current-line capture-spike report."
    )
    parser.add_argument("--report", help=f"Optional report JSON under {REPORT_ROOT}.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    report_path = FIXTURE_PATH
    if args.report:
        try:
            report_path = ensure_safe_report_path(Path(args.report))
        except RuntimeCurrentLineCaptureSpikeReportError as exc:
            parser.error(str(exc))

    errors = collect_capture_spike_report_errors(report_path)
    if errors:
        if args.quiet:
            print("Runtime current-line capture spike report check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("Runtime current-line capture spike report check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "runtime-current-line-capture-spike-report-check.v1",
                    "report": _safe_report_path(report_path),
                    "workspace_report_root": str(REPORT_ROOT.relative_to(ROOT)),
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_capture_spike_report_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load runtime capture spike report {path}: {exc}"]
    if not isinstance(payload, dict):
        return ["Runtime capture spike report must be a JSON object."]
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload))
    return errors


def ensure_safe_report_path(path: Path) -> Path:
    resolved_root = REPORT_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeCurrentLineCaptureSpikeReportError(
            f"Report path must stay under {REPORT_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != ".json":
        raise RuntimeCurrentLineCaptureSpikeReportError("Report path must end in .json")
    return resolved


def default_report_template() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "spike_status": "not_run",
        "plugin_loaded_observed": False,
        "companion_health_checked": False,
        "companion_available": False,
        "runtime_transport_enabled": False,
        "synthetic_runtime_send_configured": False,
        "synthetic_runtime_event_sent_observed": False,
        "companion_received_runtime_event": False,
        "translation_memory_checked": False,
        "provider_call_required_observed": False,
        "provider_called": False,
        "runtime_current_line_capture_enabled": False,
        "real_text_captured": False,
        "hooks_used": False,
        "ui_text_reading_used": False,
        "unity_scanning_used": False,
        "game_file_reads": False,
        "bepinex_log_reads_in_repo": False,
        "screenshots_included": False,
        "raw_logs_included": False,
        "raw_payloads_included": False,
        "private_paths_included": False,
        "blockers": [],
        "recommended_next_step": "runtime_current_line_capture_spike",
        "notes_redacted": "Synthetic committed fixture. No local runtime evidence is attached.",
        "evidence_summary": "Template only. Use safe booleans and counts, never logs or text.",
        "evidence_summary_redacted": True,
        "created_by_user_manually": True,
    }


def canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_STRING_FIELDS:
        if not isinstance(payload.get(field), str) or not payload.get(field):
            errors.append(f"Runtime capture spike report field {field!r} must be a string.")
    for field in REQUIRED_BOOL_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Runtime capture spike report field {field!r} must be a boolean.")
    for field in OPTIONAL_STRING_LIST_FIELDS:
        value = payload.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"Runtime capture spike report field {field!r} must be a string list.")

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("spike_status") not in ALLOWED_STATUSES:
        errors.append("spike_status must be not_run, pass, partial, or fail.")
    if payload.get("created_by_user_manually") is not True:
        errors.append("created_by_user_manually must be true.")
    if payload.get("evidence_summary_redacted") is not True:
        errors.append("evidence_summary_redacted must be true.")
    if payload.get("provider_called") is not False:
        errors.append("provider_called must be false.")
    for field in (
        "runtime_current_line_capture_enabled",
        "real_text_captured",
        "hooks_used",
        "ui_text_reading_used",
        "unity_scanning_used",
        "game_file_reads",
        "bepinex_log_reads_in_repo",
        "screenshots_included",
        "raw_logs_included",
        "raw_payloads_included",
        "private_paths_included",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false.")
    if payload.get("synthetic_runtime_event_sent_observed") and not payload.get(
        "synthetic_runtime_send_configured"
    ):
        errors.append("synthetic runtime send cannot be observed unless configured.")
    if payload.get("companion_received_runtime_event") and not payload.get(
        "synthetic_runtime_event_sent_observed"
    ):
        errors.append("companion receipt requires synthetic runtime send observation.")
    if payload.get("translation_memory_checked") and not payload.get(
        "companion_received_runtime_event"
    ):
        errors.append("translation memory check requires companion runtime receipt.")
    return errors


def _safety_errors(payload: dict[str, Any]) -> list[str]:
    rendered = "\n".join(_iter_string_values(payload))
    errors: list[str] = []
    for url in URL_PATTERN.findall(rendered):
        if url.rstrip(".,)") != "http://127.0.0.1:8765":
            errors.append(f"Report contains non-localhost URL {url!r}.")
    if SECRET_VALUE_PATTERN.search(rendered):
        errors.append("Report contains a secret/API-key-looking value.")
    if WINDOWS_PRIVATE_PATH_PATTERN.search(rendered) or POSIX_PRIVATE_PATH_PATTERN.search(rendered):
        errors.append("Report contains a private absolute path.")
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
