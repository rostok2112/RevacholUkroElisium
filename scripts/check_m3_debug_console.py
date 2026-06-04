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


FIXTURE_PATH = ROOT / "tests/fixtures/m3_debug_console.synthetic.json"
SOURCE_PATH = ROOT / "packages/bepinex-plugin/src/DebugCommandHandler.cs"
PLUGIN_SOURCE_PATH = ROOT / "packages/bepinex-plugin/src/RevacholCompanionBridgePlugin.cs"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
BEPINEX_DOC_PATH = ROOT / "docs/bepinex-bridge.md"
DESIGN_PATH = ROOT / "packages/bepinex-plugin/DESIGN.md"
README_PATH = ROOT / "packages/bepinex-plugin/README.md"
SCHEMA_VERSION = "m3-debug-console.v1"
ROADMAP_MILESTONE = "M3"
RECOMMENDED_NEXT_STEP = "m3_closeout"
M3_COMMIT_CAP = 6
ALLOWED_COMMANDS = (
    "bridge_status",
    "synthetic_send",
    "current_line_event_status",
    "matcher_status",
)
REQUIRED_TRUE_FIELDS = (
    "m2_closed",
    "m3_scope_recovery_done",
    "m3_current_line_event_done",
    "m3_line_id_matching_done",
    "m3_debug_console_done",
)
FORBIDDEN_PERMISSION_FIELDS = (
    "default_debug_console_enabled",
    "raw_text_dump_allowed",
    "payload_dump_allowed",
    "private_path_dump_allowed",
    "line_id_dump_allowed",
    "record_id_dump_allowed",
    "source_text_dump_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "game_file_reads_allowed",
    "bepinex_log_reads_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "ocr_allowed",
    "generated_runtime_artifact_commit_allowed",
    "real_game_text_commit_allowed",
    "private_paths_commit_allowed",
)
URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
FORBIDDEN_VALUE_MARKERS = (
    "raw text dump approved",
    "payload dump approved",
    "private path dump approved",
    "line id dump approved",
    "record id dump approved",
    "source text dump approved",
    "provider execution approved",
    "companion contract change approved",
    "game file reads approved",
    "bepinex log reads approved",
    "ui text reading approved",
    "unity scanning approved",
    "hook implementation approved",
    "ocr approved",
    "raw payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "steamapps",
    "decompiled",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the M3 debug console boundary.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m3_debug_console_errors()
    if errors:
        if args.quiet:
            print("M3 debug console check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M3 debug console check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m3-debug-console-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m3_debug_console_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M3 debug console fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M3 debug console fixture must be a JSON object."]
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
        "m3_commit_cap": M3_COMMIT_CAP,
        "implementation_kind": "disabled_by_default_redacted_debug_commands",
        "required_next_step": RECOMMENDED_NEXT_STEP,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M3 debug console {field} must be {expected!r}.")
    if tuple(payload.get("allowed_commands", ())) != ALLOWED_COMMANDS:
        errors.append("M3 debug console allowed_commands must match exactly.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M3 debug console fixture must set {field}=true.")
    for field in FORBIDDEN_PERMISSION_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M3 debug console fixture must keep {field}=false.")
    return errors


def _source_errors() -> list[str]:
    errors: list[str] = []
    source = SOURCE_PATH.read_text(encoding="utf-8")
    plugin = PLUGIN_SOURCE_PATH.read_text(encoding="utf-8")
    required_markers = (
        "DefaultDebugConsoleEnabled = false",
        "DebugConsoleEnabled",
        "RunDebugCommand",
        "DebugCommandHandler.BuildResult",
        'SchemaVersion = "m3-debug-console-command-result.v1"',
        'BridgeStatus = "bridge_status"',
        'SyntheticSend = "synthetic_send"',
        'CurrentLineEventStatus = "current_line_event_status"',
        'MatcherStatus = "matcher_status"',
        '"synthetic_send_performed"',
        '"raw_text_included"',
        '"payload_dump_included"',
        '"private_paths_included"',
        '"provider_called"',
    )
    combined = source + "\n" + plugin
    for marker in required_markers:
        if marker not in combined:
            errors.append(f"M3 debug console source missing required marker: {marker}.")
    forbidden_markers = (
        "ReadAllText",
        "File.",
        "Directory.",
        "PostSyntheticProviderAnnotateAsync(",
        "HttpClient",
        "FindObjectOfType",
        "FindObjectsOfType",
        "Resources.FindObjectsOfTypeAll",
        "GameObject.Find",
        "HarmonyPatch",
        "Update(",
        "OnGUI(",
        "OCR",
        "Tesseract",
        "raw_english_text",
        "RawEnglishText",
    )
    for marker in forbidden_markers:
        if marker in source:
            errors.append(f"M3 debug console source must not contain {marker!r}.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "implementation_guarded",
        "disabled_by_default_redacted_debug_commands",
        *ALLOWED_COMMANDS,
    }
    for value in _iter_string_values(payload):
        if value in expected_values:
            continue
        for url in URL_PATTERN.findall(value):
            errors.append(f"{relative}: contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(value):
            errors.append(f"{relative}: contains a secret/API-key-looking value.")
        lowered = value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{relative}: contains forbidden marker {marker!r}.")
    return errors


def _doc_errors() -> list[str]:
    errors: list[str] = []
    required_refs = (
        "packages/bepinex-plugin/src/DebugCommandHandler.cs",
        "tests/fixtures/m3_debug_console.synthetic.json",
        "scripts/check_m3_debug_console.py",
        RECOMMENDED_NEXT_STEP,
    )
    for doc_path in (
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        BEPINEX_DOC_PATH,
        DESIGN_PATH,
        README_PATH,
    ):
        if not doc_path.exists():
            errors.append(f"Missing M3 debug console doc target: {doc_path.name}.")
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
