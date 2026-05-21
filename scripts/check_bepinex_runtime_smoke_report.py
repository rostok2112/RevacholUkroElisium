from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    from scripts.schema_validator import load_json
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json"
REPORT_ROOT = ROOT / "workspace/synthetic-slice/bepinex-bridge/runtime-smoke"
SCHEMA_VERSION = "bepinex-bridge-runtime-smoke-report.v1"
ALLOWED_STATUSES = ("pass", "fail", "partial", "not_run")

REQUIRED_BOOL_FIELDS = (
    "build_attempted",
    "build_succeeded",
    "plugin_loaded_observed",
    "health_check_observed",
    "companion_available_observed",
    "companion_unavailable_observed",
    "synthetic_send_enabled",
    "synthetic_send_observed",
    "companion_received_synthetic_event",
    "game_continued_when_companion_unavailable",
    "created_by_user_manually",
)
REQUIRED_INT_FIELDS = ("warnings_count", "msb3277_warning_count")
REQUIRED_STRING_FIELDS = (
    "schema_version",
    "smoke_status",
    "plugin_id",
    "bridge_version",
    "notes_redacted",
    "evidence_summary",
)
OPTIONAL_STRING_FIELDS = (
    "next_step_notes",
    "synthetic_send_not_run_reason",
    "unavailable_case_not_run_reason",
)
OPTIONAL_STRING_LIST_FIELDS = ("blockers",)
OPTIONAL_TRUE_BOOL_FIELDS = ("evidence_summary_redacted",)

ALLOWED_URLS = ("http://127.0.0.1:8765",)
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
    "BepInEx/log",
    "stack trace",
    "Traceback (most recent call last)",
    " at Revachol",
    " at Il2Cpp",
    "ReadAsStringAsync",
    "response.Content",
    "request payload",
    "response payload",
    "raw_english_text",
    "input_type",
    ".png",
    ".jpg",
    ".wav",
    ".ogg",
    ".mp3",
    ".assets",
    ".bundle",
    "steamapps",
    "database.json",
    "HarmonyPatch",
    "Input.GetKey",
    "Keyboard.current",
    "Clipboard",
    "FindObjectOfType",
    "FindObjectsOfType",
    "GameObject.Find",
    "Resources.FindObjectsOfTypeAll",
    "SceneManager",
    "OCR",
    "Tesseract",
    "Il2CppDumper",
    "dnSpy",
    "Assembly-CSharp",
    "api.openai",
    "openai_compatible",
    "deepl",
    "anthropic",
    "local_model",
    "ensemble_reviewer",
)


class BepInExRuntimeSmokeReportError(RuntimeError):
    """Raised when a manual runtime smoke report is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a redacted synthetic/manual BepInEx runtime smoke report."
    )
    parser.add_argument(
        "--report",
        help=(
            "Optional user-local report JSON. Must be under "
            "workspace/synthetic-slice/bepinex-bridge/runtime-smoke/."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    report_path = FIXTURE_PATH
    if args.report:
        try:
            report_path = ensure_safe_report_path(Path(args.report))
        except BepInExRuntimeSmokeReportError as exc:
            parser.error(str(exc))

    errors = collect_runtime_smoke_report_errors(report_path)
    if errors:
        if args.quiet:
            print("BepInEx runtime smoke report check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("BepInEx runtime smoke report check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "bepinex-runtime-smoke-report-check.v1",
                    "report": _safe_report_path(report_path),
                    "committed_fixture": str(FIXTURE_PATH.relative_to(ROOT)),
                    "workspace_report_root": str(REPORT_ROOT.relative_to(ROOT)),
                    "synthetic_manual_only": True,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_runtime_smoke_report_safe(path: Path = FIXTURE_PATH) -> None:
    errors = collect_runtime_smoke_report_errors(path)
    if errors:
        raise BepInExRuntimeSmokeReportError("; ".join(errors))


def collect_runtime_smoke_report_errors(path: Path = FIXTURE_PATH) -> list[str]:
    errors: list[str] = []
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load runtime smoke report {path}: {exc}"]

    if not isinstance(payload, dict):
        return ["Runtime smoke report must be a JSON object."]

    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload))
    return errors


def ensure_safe_report_path(path: Path) -> Path:
    resolved_root = REPORT_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise BepInExRuntimeSmokeReportError(
            f"Report path must stay under {REPORT_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != ".json":
        raise BepInExRuntimeSmokeReportError("Runtime smoke report path must end in .json")
    return resolved


def default_report_template() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "smoke_status": "not_run",
        "plugin_id": "local.revachol.ukrainian-companion.bridge",
        "bridge_version": "0.4.0-synthetic",
        "build_attempted": False,
        "build_succeeded": False,
        "plugin_loaded_observed": False,
        "health_check_observed": False,
        "companion_available_observed": False,
        "companion_unavailable_observed": False,
        "synthetic_send_enabled": False,
        "synthetic_send_observed": False,
        "companion_received_synthetic_event": False,
        "game_continued_when_companion_unavailable": False,
        "warnings_count": 0,
        "msb3277_warning_count": 0,
        "blockers": [],
        "next_step_notes": "Fill with a short redacted next-step note if useful.",
        "synthetic_send_not_run_reason": "Synthetic send was not run for this template.",
        "unavailable_case_not_run_reason": "Unavailable companion case was not run for this template.",
        "evidence_summary_redacted": True,
        "notes_redacted": "Fill with a short redacted manual summary. Do not paste logs.",
        "evidence_summary": "Fill with safe observed metadata only. Do not paste payloads.",
        "created_by_user_manually": True,
    }


def canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_STRING_FIELDS:
        if not isinstance(payload.get(field), str) or not payload.get(field):
            errors.append(f"Runtime smoke report field {field!r} must be a non-empty string.")
    for field in REQUIRED_BOOL_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Runtime smoke report field {field!r} must be a boolean.")
    for field in REQUIRED_INT_FIELDS:
        value = payload.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"Runtime smoke report field {field!r} must be a non-negative integer.")

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Runtime smoke report schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("smoke_status") not in ALLOWED_STATUSES:
        errors.append(
            "Runtime smoke report smoke_status must be one of: " + ", ".join(ALLOWED_STATUSES) + "."
        )
    if payload.get("created_by_user_manually") is not True:
        errors.append("Runtime smoke report must set created_by_user_manually=true.")
    if payload.get("build_succeeded") and not payload.get("build_attempted"):
        errors.append(
            "Runtime smoke report cannot have build_succeeded=true when build_attempted=false."
        )
    if payload.get("synthetic_send_observed") and not payload.get("synthetic_send_enabled"):
        errors.append(
            "Runtime smoke report cannot observe synthetic send unless synthetic_send_enabled=true."
        )
    if payload.get("companion_received_synthetic_event") and not payload.get(
        "synthetic_send_observed"
    ):
        errors.append(
            "Runtime smoke report cannot observe companion receipt without synthetic_send_observed=true."
        )
    for field in OPTIONAL_STRING_FIELDS:
        if field in payload and not isinstance(payload.get(field), str):
            errors.append(f"Runtime smoke report field {field!r} must be a string when present.")
    for field in OPTIONAL_STRING_LIST_FIELDS:
        value = payload.get(field)
        if field in payload and (
            not isinstance(value, list) or not all(isinstance(item, str) for item in value)
        ):
            errors.append(
                f"Runtime smoke report field {field!r} must be a list of strings when present."
            )
    for field in OPTIONAL_TRUE_BOOL_FIELDS:
        if field in payload and payload.get(field) is not True:
            errors.append(f"Runtime smoke report field {field!r} must be true when present.")
    return errors


def _safety_errors(payload: dict[str, Any]) -> list[str]:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    errors: list[str] = []

    for url in URL_PATTERN.findall(rendered):
        if url.rstrip(".,)") not in ALLOWED_URLS:
            errors.append(f"Runtime smoke report contains non-localhost URL {url!r}.")
    if SECRET_VALUE_PATTERN.search(rendered):
        errors.append("Runtime smoke report contains a secret/API-key-looking value.")
    if WINDOWS_PRIVATE_PATH_PATTERN.search(rendered) or POSIX_PRIVATE_PATH_PATTERN.search(rendered):
        errors.append("Runtime smoke report contains a private absolute path.")

    lowered = rendered.lower()
    for marker in FORBIDDEN_REPORT_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"Runtime smoke report contains forbidden marker {marker!r}.")
    return errors


def _safe_report_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve()))
    except ValueError:
        return f"<local:{path.name}>"


if __name__ == "__main__":
    sys.exit(main())
