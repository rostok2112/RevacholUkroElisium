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
FIXTURE_PATH = ROOT / "tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json"
REPORT_ROOT = ROOT / "workspace/synthetic-slice/bepinex-bridge/metadata-probe"
SCHEMA_VERSION = "bepinex-bridge-metadata-probe-report.v1"
ALLOWED_STATUSES = ("not_run", "pass", "partial", "fail")

REQUIRED_BOOL_FIELDS = (
    "metadata_only",
    "probe_enabled",
    "probe_attempted",
    "probe_completed",
    "plugin_loaded",
    "companion_health_checked",
    "companion_available",
    "synthetic_event_send_configured",
    "synthetic_event_sent",
    "scene_probe_attempted",
    "ui_probe_attempted",
    "current_line_capture_enabled",
    "real_text_captured",
    "created_by_user_manually",
)
REQUIRED_STRING_FIELDS = ("schema_version", "probe_status", "redacted_notes")
OPTIONAL_STRING_FIELDS = ("next_step_notes", "not_run_reason")
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
    "real dialogue",
    "dialogue text",
    "ui text",
    "ui_text",
    "raw_english_text",
    "source text",
    "captured text",
    "text captured",
    "screenshot",
    "screen capture",
    ".png",
    ".jpg",
    ".jpeg",
    ".wav",
    ".ogg",
    ".mp3",
    ".assets",
    ".bundle",
    "save file",
    "save data",
    "steamapps",
    "LogOutput.log",
    "Player.log",
    "output_log.txt",
    "stack trace",
    "Traceback (most recent call last)",
    " at Revachol",
    " at Il2Cpp",
    "request payload",
    "response payload",
    "raw companion payload",
    "input_type",
    "response.Content",
    "ReadAsStringAsync",
    "HarmonyPatch",
    "Harmony patch",
    "game hook",
    "method hook",
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


class BepInExMetadataProbeReportError(RuntimeError):
    """Raised when a metadata-only probe report is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a synthetic/redacted BepInEx metadata probe report."
    )
    parser.add_argument(
        "--report",
        help=(
            "Optional user-local report JSON. Must be under "
            "workspace/synthetic-slice/bepinex-bridge/metadata-probe/."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    report_path = FIXTURE_PATH
    if args.report:
        try:
            report_path = ensure_safe_metadata_probe_report_path(Path(args.report))
        except BepInExMetadataProbeReportError as exc:
            parser.error(str(exc))

    errors = collect_metadata_probe_report_errors(report_path)
    if errors:
        if args.quiet:
            print("BepInEx metadata probe report check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("BepInEx metadata probe report check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "bepinex-metadata-probe-report-check.v1",
                    "report": _safe_report_path(report_path),
                    "committed_fixture": str(FIXTURE_PATH.relative_to(ROOT)),
                    "workspace_report_root": str(REPORT_ROOT.relative_to(ROOT)),
                    "metadata_only": True,
                    "real_report_required": False,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_metadata_probe_report_safe(path: Path = FIXTURE_PATH) -> None:
    errors = collect_metadata_probe_report_errors(path)
    if errors:
        raise BepInExMetadataProbeReportError("; ".join(errors))


def collect_metadata_probe_report_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load metadata probe report {path}: {exc}"]

    if not isinstance(payload, dict):
        return ["Metadata probe report must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload))
    return errors


def ensure_safe_metadata_probe_report_path(path: Path) -> Path:
    resolved_root = REPORT_ROOT.resolve()
    resolved = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise BepInExMetadataProbeReportError(
            f"Metadata probe report path must stay under {REPORT_ROOT.relative_to(ROOT)}"
        ) from exc
    if resolved.suffix.lower() != ".json":
        raise BepInExMetadataProbeReportError("Metadata probe report path must end in .json")
    return resolved


def canonical_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def default_metadata_probe_report_template() -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "probe_status": "not_run",
        "metadata_only": True,
        "probe_enabled": False,
        "probe_attempted": False,
        "probe_completed": False,
        "plugin_loaded": False,
        "companion_health_checked": False,
        "companion_available": False,
        "synthetic_event_send_configured": False,
        "synthetic_event_sent": False,
        "scene_probe_attempted": False,
        "ui_probe_attempted": False,
        "current_line_capture_enabled": False,
        "real_text_captured": False,
        "counters": {
            "safe_status_events": 0,
            "synthetic_events": 0,
        },
        "blockers": [],
        "next_step_notes": "Fill with a short redacted next-step note if useful.",
        "not_run_reason": "Metadata probe was not run for this template.",
        "evidence_summary_redacted": True,
        "redacted_notes": (
            "Template only. Fill with safe metadata observations. Do not paste logs."
        ),
        "created_by_user_manually": True,
    }


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_STRING_FIELDS:
        if not isinstance(payload.get(field), str) or not payload.get(field):
            errors.append(f"Metadata probe report field {field!r} must be a non-empty string.")
    for field in REQUIRED_BOOL_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Metadata probe report field {field!r} must be a boolean.")

    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Metadata probe report schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("probe_status") not in ALLOWED_STATUSES:
        errors.append(
            "Metadata probe report probe_status must be one of: "
            + ", ".join(ALLOWED_STATUSES)
            + "."
        )
    if payload.get("metadata_only") is not True:
        errors.append("Metadata probe report must set metadata_only=true.")
    if payload.get("real_text_captured") is not False:
        errors.append("Metadata probe report must set real_text_captured=false.")
    if payload.get("current_line_capture_enabled") is not False:
        errors.append("Metadata probe report must set current_line_capture_enabled=false.")
    if payload.get("created_by_user_manually") is not True:
        errors.append("Metadata probe report must set created_by_user_manually=true.")
    if payload.get("probe_attempted") and not payload.get("probe_enabled"):
        errors.append(
            "Metadata probe report cannot have probe_attempted=true when probe_enabled=false."
        )
    if payload.get("probe_completed") and not payload.get("probe_attempted"):
        errors.append(
            "Metadata probe report cannot have probe_completed=true when probe_attempted=false."
        )
    if payload.get("synthetic_event_sent") and not payload.get("synthetic_event_send_configured"):
        errors.append(
            "Metadata probe report cannot have synthetic_event_sent=true when "
            "synthetic_event_send_configured=false."
        )
    for field in OPTIONAL_STRING_FIELDS:
        if field in payload and not isinstance(payload.get(field), str):
            errors.append(f"Metadata probe report field {field!r} must be a string when present.")
    for field in OPTIONAL_STRING_LIST_FIELDS:
        value = payload.get(field)
        if field in payload and (
            not isinstance(value, list) or not all(isinstance(item, str) for item in value)
        ):
            errors.append(
                f"Metadata probe report field {field!r} must be a list of strings when present."
            )
    for field in OPTIONAL_TRUE_BOOL_FIELDS:
        if field in payload and payload.get(field) is not True:
            errors.append(f"Metadata probe report field {field!r} must be true when present.")

    counters = payload.get("counters")
    if not isinstance(counters, dict):
        errors.append("Metadata probe report field 'counters' must be an object.")
    else:
        for key, value in counters.items():
            if not isinstance(key, str) or not key:
                errors.append("Metadata probe report counters must use non-empty string keys.")
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                errors.append(
                    f"Metadata probe report counter {key!r} must be a non-negative integer."
                )
    return errors


def _safety_errors(payload: dict[str, Any]) -> list[str]:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    errors: list[str] = []

    for url in URL_PATTERN.findall(rendered):
        if url.rstrip(".,)") not in ALLOWED_URLS:
            errors.append(f"Metadata probe report contains non-localhost URL {url!r}.")
    if SECRET_VALUE_PATTERN.search(rendered):
        errors.append("Metadata probe report contains a secret/API-key-looking value.")
    if WINDOWS_PRIVATE_PATH_PATTERN.search(rendered) or POSIX_PRIVATE_PATH_PATTERN.search(rendered):
        errors.append("Metadata probe report contains a private absolute path.")

    lowered = rendered.lower()
    for marker in FORBIDDEN_REPORT_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"Metadata probe report contains forbidden marker {marker!r}.")
    return errors


def _safe_report_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve()))
    except ValueError:
        return f"<local:{path.name}>"


if __name__ == "__main__":
    sys.exit(main())
