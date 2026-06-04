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


FIXTURE_PATH = ROOT / "tests/fixtures/m3_current_line_event_contract.synthetic.json"
DOC_PATH = ROOT / "docs/m3-current-line-event-contract.md"
SCOPE_DOC_PATH = ROOT / "docs/m3-bepinex-bridge-scope.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
BEPINEX_DOC_PATH = ROOT / "docs/bepinex-bridge.md"
DESIGN_PATH = ROOT / "packages/bepinex-plugin/DESIGN.md"
README_PATH = ROOT / "packages/bepinex-plugin/README.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SCHEMA_VERSION = "m3-current-line-event-contract.v1"
EVENT_SCHEMA_VERSION = "m3-current-line-event.v1"
ROADMAP_MILESTONE = "M3"
RECOMMENDED_NEXT_STEP = "m3_current_line_event_implementation"
ALLOWED_EVENT_FIELDS = (
    "schema_version",
    "event_kind",
    "bridge_source",
    "emitted_at_unix_ms",
    "line_id",
    "conversation_id",
    "source",
    "capture_enabled",
    "raw_text_included",
    "private_paths_included",
    "provider_called",
)
ALLOWED_EVENT_SOURCES = ("synthetic", "runtime_metadata")
REQUIRED_TRUE_FIELDS = (
    "m2_closed",
    "m3_scope_recovery_done",
    "disabled_by_default_required",
    "local_only_required",
    "reuse_existing_bridge_baseline_required",
)
INCOMPLETE_M3_FIELDS = (
    "m3_current_line_event_done",
    "m3_line_id_matching_done",
    "m3_debug_console_done",
)
FORBIDDEN_PERMISSION_FIELDS = (
    "implementation_allowed_next",
    "line_id_matching_implementation_allowed_next",
    "debug_console_implementation_allowed_next",
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
    "game file reads approved",
    "bepinex log reads approved",
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


class M3CurrentLineEventContractError(RuntimeError):
    """Raised when the M3 current-line event contract is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the M3 current-line event contract.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m3_current_line_event_contract_errors()
    if errors:
        if args.quiet:
            print("M3 current-line event contract check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M3 current-line event contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m3-current-line-event-contract-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m3_current_line_event_contract_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M3 current-line event contract fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M3 current-line event contract fixture must be a JSON object."]
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected_scalars = {
        "schema_version": SCHEMA_VERSION,
        "roadmap_milestone": ROADMAP_MILESTONE,
        "scope_status": "contract_only",
        "event_schema_version": EVENT_SCHEMA_VERSION,
        "event_kind": "current_line",
        "current_line_event_implementation_allowed_next": "contract_defined_only",
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "required_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M3 current-line event {field} must be {expected!r}.")
    if "m3_commit_cap" in payload or "m3_commits_used" in payload:
        errors.append("M3 current-line event fixture must not encode commit cap metadata.")
    if tuple(payload.get("allowed_event_fields", ())) != ALLOWED_EVENT_FIELDS:
        errors.append("M3 current-line event allowed_event_fields must match exactly.")
    if tuple(payload.get("allowed_event_sources", ())) != ALLOWED_EVENT_SOURCES:
        errors.append("M3 current-line event allowed_event_sources must match exactly.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M3 current-line event fixture must set {field}=true.")
    for field in (*INCOMPLETE_M3_FIELDS, *FORBIDDEN_PERMISSION_FIELDS):
        if payload.get(field) is not False:
            errors.append(f"M3 current-line event fixture must keep {field}=false.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        EVENT_SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "contract_only",
        "current_line",
        "contract_defined_only",
        *ALLOWED_EVENT_FIELDS,
        *ALLOWED_EVENT_SOURCES,
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
        "docs/m3-current-line-event-contract.md",
        "tests/fixtures/m3_current_line_event_contract.synthetic.json",
        "scripts/check_m3_current_line_event_contract.py",
        RECOMMENDED_NEXT_STEP,
    )
    for path in (
        DOC_PATH,
        SCOPE_DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        BEPINEX_DOC_PATH,
        DESIGN_PATH,
        README_PATH,
    ):
        if not path.exists():
            errors.append(f"Missing M3 current-line event doc target: {_display_path(path)}.")
            continue
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for required in required_refs:
            if required not in text:
                errors.append(f"{_display_path(path)} must reference {required}.")
        errors.extend(_unsafe_doc_text_errors(text, path))
    tasks_text = TASKS_PATH.read_text(encoding="utf-8")
    if "Emit current line event." not in tasks_text:
        errors.append("tasks/milestones.md must keep the M3 current-line event criterion.")
    return errors


def _unsafe_doc_text_errors(text: str, path: Path) -> list[str]:
    lowered = text.lower()
    errors: list[str] = []
    for phrase in (
        "raw text is approved",
        "ui text reading is approved",
        "unity scanning is approved",
        "provider execution is approved",
        "companion contract change is approved",
        "line id matching is approved in this step",
    ):
        if phrase in lowered:
            errors.append(f"{_display_path(path)} must not say {phrase!r}.")
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
