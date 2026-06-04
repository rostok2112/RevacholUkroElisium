from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import load_json
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/m3_current_line_event_implementation.synthetic.json"
CONTRACT_DOC_PATH = ROOT / "docs/m3-current-line-event-contract.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
BEPINEX_DOC_PATH = ROOT / "docs/bepinex-bridge.md"
DESIGN_PATH = ROOT / "packages/bepinex-plugin/DESIGN.md"
README_PATH = ROOT / "packages/bepinex-plugin/README.md"
PLUGIN_SOURCE_PATH = ROOT / "packages/bepinex-plugin/src/RevacholCompanionBridgePlugin.cs"
EVENT_SOURCE_PATH = ROOT / "packages/bepinex-plugin/src/CurrentLineEventFactory.cs"
CLIENT_SOURCE_PATH = ROOT / "packages/bepinex-plugin/src/CompanionHttpClient.cs"
SCHEMA_VERSION = "m3-current-line-event-implementation.v1"
EVENT_SCHEMA_VERSION = "m3-current-line-event.v1"
ROADMAP_MILESTONE = "M3"
RECOMMENDED_NEXT_STEP = "m3_line_id_matching"
REQUIRED_TRUE_FIELDS = (
    "m2_closed",
    "m3_scope_recovery_done",
    "m3_current_line_event_contract_done",
    "m3_current_line_event_done",
)
INCOMPLETE_M3_FIELDS = (
    "m3_line_id_matching_done",
    "m3_debug_console_done",
)
FORBIDDEN_PERMISSION_FIELDS = (
    "raw_text_included_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "ocr_allowed",
    "game_file_reads_allowed",
    "bepinex_log_reads_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "line_id_matching_allowed_in_this_step",
    "private_line_index_reads_allowed_in_this_step",
    "debug_console_allowed_in_this_step",
    "generated_runtime_artifact_commit_allowed",
    "real_game_text_commit_allowed",
    "private_paths_commit_allowed",
)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:[\\/](?:Users|Program Files|Games|Steam|GOG|AppData)[\\/]",
    re.IGNORECASE,
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")
FORBIDDEN_VALUE_MARKERS = (
    "raw text approved",
    "raw dialogue approved",
    "ui text reading approved",
    "unity scanning approved",
    "hook implementation approved",
    "harmony patch approved",
    "ocr approved",
    "provider execution approved",
    "companion contract change approved",
    "line id matching approved in this step",
    "private line index reads approved",
    "debug console approved in this step",
    "raw payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "screen capture",
    "steamapps",
    "savegame",
    ".sav",
    "decompiled",
    "dnspy",
    "ilspy",
)


class M3CurrentLineEventImplementationError(RuntimeError):
    """Raised when the M3 current-line event implementation is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the M3 current-line event implementation boundary."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m3_current_line_event_implementation_errors()
    if errors:
        if args.quiet:
            print("M3 current-line event implementation check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M3 current-line event implementation check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m3-current-line-event-implementation-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m3_current_line_event_implementation_errors(
    path: Path = FIXTURE_PATH,
) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M3 current-line event implementation fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M3 current-line event implementation fixture must be a JSON object."]
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_source_errors())
        errors.extend(_doc_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_scalars = {
        "schema_version": SCHEMA_VERSION,
        "roadmap_milestone": ROADMAP_MILESTONE,
        "scope_status": "implementation_guarded",
        "implementation_kind": "disabled_by_default_redacted_local_event",
        "event_schema_version": EVENT_SCHEMA_VERSION,
        "event_kind": "current_line",
        "required_next_step": RECOMMENDED_NEXT_STEP,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M3 current-line implementation {field} must be {expected!r}.")
    if "m3_commit_cap" in payload or "m3_commits_used" in payload:
        errors.append("M3 current-line implementation fixture must not encode commit cap metadata.")
    if payload.get("default_current_line_event_enabled") is not False:
        errors.append("M3 current-line event must remain disabled by default.")
    if payload.get("default_emit_synthetic_current_line_event_on_start") is not False:
        errors.append("M3 synthetic current-line startup event must remain disabled by default.")
    if payload.get("default_runtime_current_line_transport_enabled") not in (None, False):
        errors.append("Runtime current-line transport must remain disabled by default.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M3 current-line implementation fixture must set {field}=true.")
    for field in (*INCOMPLETE_M3_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
        if payload.get(field) is not False:
            errors.append(f"M3 current-line implementation fixture must keep {field}=false.")
    return errors


def _source_errors() -> list[str]:
    errors: list[str] = []
    plugin = PLUGIN_SOURCE_PATH.read_text(encoding="utf-8")
    event_source = EVENT_SOURCE_PATH.read_text(encoding="utf-8")
    client = CLIENT_SOURCE_PATH.read_text(encoding="utf-8")
    combined = "\n".join((plugin, event_source))
    required_markers = (
        "DefaultCurrentLineEventEnabled = false",
        "DefaultEmitSyntheticCurrentLineEventOnStart = false",
        "DefaultRuntimeCurrentLineTransportEnabled = false",
        "CurrentLineEventEnabled",
        "EmitSyntheticCurrentLineEventOnStart",
        "RuntimeCurrentLineTransportEnabled",
        "EmitSyntheticCurrentLineEventNow",
        "SendSyntheticRuntimeCurrentLineEventNowAsync",
        "CurrentLineEventFactory.BuildSyntheticCurrentLineEventJson",
        "CurrentLineEventFactory.BuildSyntheticRuntimeCurrentLineEventJson",
        'SchemaVersion = "m3-current-line-event.v1"',
        'EventKind = "current_line"',
        'BridgeSource = "bepinex"',
        'SourceSynthetic = "synthetic"',
        '\\"capture_enabled\\":false',
        '\\"raw_text_included\\":false',
        '\\"private_paths_included\\":false',
        '\\"provider_called\\":false',
    )
    for marker in required_markers:
        if marker not in combined:
            errors.append(f"M3 current-line source missing required marker: {marker}.")
    forbidden_event_source_markers = (
        "raw_english_text",
        "RawEnglishText",
        "PostSyntheticProviderAnnotateAsync",
        "synthetic/provider-annotate",
        "CheckHealthAsync",
        "FindObjectOfType",
        "FindObjectsOfType",
        "Resources.FindObjectsOfTypeAll",
        "GameObject.Find",
        "HarmonyPatch",
        "Update(",
        "OnGUI(",
        "OCR",
        "Tesseract",
    )
    for marker in forbidden_event_source_markers:
        if marker in event_source:
            errors.append(f"M3 current-line event source must not contain {marker!r}.")
    if "PostRuntimeCurrentLineAsync" not in client or "runtime/current-line" not in client:
        errors.append("Runtime-first current-line transport must post to runtime/current-line.")
    if "LineIndex" in combined or "line-index" in combined:
        errors.append("M3 current-line implementation must not read or match line indexes.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        EVENT_SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "implementation_guarded",
        "disabled_by_default_redacted_local_event",
        "current_line",
    }
    for value in _iter_string_values(payload):
        if value in expected_values:
            continue
        for url in URL_PATTERN.findall(value):
            errors.append(f"{relative}: contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(value):
            errors.append(f"{relative}: contains a secret/API-key-looking value.")
        if WINDOWS_PRIVATE_PATH_PATTERN.search(value) or POSIX_PRIVATE_PATH_PATTERN.search(value):
            errors.append(f"{relative}: contains a private absolute path.")
        lowered = value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{relative}: contains forbidden marker {marker!r}.")
    return errors


def _doc_errors() -> list[str]:
    errors: list[str] = []
    required_refs = (
        "tests/fixtures/m3_current_line_event_implementation.synthetic.json",
        "scripts/check_m3_current_line_event_implementation.py",
        "packages/bepinex-plugin/src/CurrentLineEventFactory.cs",
        RECOMMENDED_NEXT_STEP,
    )
    for doc_path in (
        CONTRACT_DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        BEPINEX_DOC_PATH,
        DESIGN_PATH,
        README_PATH,
    ):
        if not doc_path.exists():
            errors.append(f"Missing M3 current-line implementation doc target: {doc_path.name}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for ref in required_refs:
            if ref not in text:
                errors.append(f"{_display_path(doc_path)} must reference {ref}.")
    return errors


def _iter_string_values(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _iter_string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_string_values(nested)


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(ROOT.resolve(strict=False))).replace(
            "\\", "/"
        )
    except ValueError:
        return path.name


if __name__ == "__main__":
    raise SystemExit(main())
