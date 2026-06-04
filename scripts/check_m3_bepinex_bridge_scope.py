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


FIXTURE_PATH = ROOT / "tests/fixtures/m3_bepinex_bridge_scope.synthetic.json"
DOC_PATH = ROOT / "docs/m3-bepinex-bridge-scope.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
BEPINEX_DOC_PATH = ROOT / "docs/bepinex-bridge.md"
DESIGN_PATH = ROOT / "packages/bepinex-plugin/DESIGN.md"
README_PATH = ROOT / "packages/bepinex-plugin/README.md"
SCHEMA_VERSION = "m3-bepinex-bridge-scope.v1"
ROADMAP_MILESTONE = "M3"
RECOMMENDED_NEXT_STEP = "m3_current_line_event_contract"
M3_COMMIT_CAP = 6

REQUIRED_TRUE_FIELDS = (
    "m2_closed",
    "existing_bridge_skeleton_reused",
    "existing_build_helper_reused",
    "existing_runtime_smoke_workflow_reused",
    "existing_metadata_probe_reused",
    "existing_local_workflow_wrapper_reused",
    "m3_scope_recovery_done",
)

INCOMPLETE_M3_FIELDS = (
    "m3_current_line_event_done",
    "m3_line_id_matching_done",
    "m3_debug_console_done",
)

FORBIDDEN_PERMISSION_FIELDS = (
    "implementation_allowed_next",
    "current_line_event_implementation_allowed_next",
    "line_id_matching_implementation_allowed_next",
    "debug_console_implementation_allowed_next",
    "real_text_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "ocr_allowed",
    "game_file_reads_allowed",
    "bepinex_log_reads_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "generated_runtime_artifact_commit_allowed",
    "real_game_text_commit_allowed",
    "private_paths_commit_allowed",
)

BASELINE_REFS = (
    "packages/bepinex-plugin/src/RevacholCompanionBridgePlugin.cs",
    "packages/bepinex-plugin/src/CompanionHttpClient.cs",
    "packages/bepinex-plugin/src/SyntheticEventFactory.cs",
    "packages/bepinex-plugin/src/MetadataProbe.cs",
    "scripts/build_bepinex_bridge.py",
    "scripts/check_bepinex_bridge_safety.py",
    "scripts/run_bepinex_metadata_probe_local_smoke.py",
    "scripts/run_bridge_to_overlay_synthetic_smoke.py",
    "scripts/run_local_bridge_workflow.py",
)

URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:(?:\\\\|\\)(?:Users|Program Files|Games|Steam|GOG|AppData)(?:\\\\|\\)"
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")

FORBIDDEN_VALUE_MARKERS = (
    "current-line capture approved",
    "current line capture approved",
    "real text capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "hook implementation approved",
    "harmony patch approved",
    "ocr approved",
    "provider execution approved",
    "companion contract change approved",
    "game file reads approved",
    "bepinex log reads approved",
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


class M3BepInExBridgeScopeError(RuntimeError):
    """Raised when the M3 BepInEx bridge scope fixture is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the M3 BepInEx bridge scope recovery.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m3_bepinex_bridge_scope_errors()
    if errors:
        if args.quiet:
            print("M3 BepInEx bridge scope check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("M3 BepInEx bridge scope check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m3-bepinex-bridge-scope-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "m3_commit_cap": M3_COMMIT_CAP,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m3_bepinex_bridge_scope_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M3 BepInEx bridge scope fixture: {exc}"]

    if not isinstance(payload, dict):
        return ["M3 BepInEx bridge scope fixture must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
        errors.extend(_baseline_file_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"M3 scope schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("roadmap_milestone") != ROADMAP_MILESTONE:
        errors.append(f"M3 scope roadmap_milestone must be {ROADMAP_MILESTONE!r}.")
    if payload.get("scope_status") != "baseline_recovery":
        errors.append("M3 scope_status must be 'baseline_recovery'.")
    if payload.get("m3_commit_cap") != M3_COMMIT_CAP:
        errors.append(f"M3 scope fixture must keep m3_commit_cap={M3_COMMIT_CAP}.")
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(f"M3 recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}.")
    if payload.get("required_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(f"M3 required_next_step must be {RECOMMENDED_NEXT_STEP!r}.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M3 scope fixture must set {field}=true.")
    for field in INCOMPLETE_M3_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M3 scope fixture must keep {field}=false until M3 implements it.")
    for field in FORBIDDEN_PERMISSION_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M3 scope fixture must keep {field}=false.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "baseline_recovery",
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
    refs = (
        "docs/m3-bepinex-bridge-scope.md",
        "tests/fixtures/m3_bepinex_bridge_scope.synthetic.json",
        "scripts/check_m3_bepinex_bridge_scope.py",
        RECOMMENDED_NEXT_STEP,
    )
    for doc_path in (
        DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        BEPINEX_DOC_PATH,
        DESIGN_PATH,
        README_PATH,
    ):
        if not doc_path.exists():
            errors.append(f"Missing M3 scope doc target: {_display_path(doc_path)}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for ref in refs:
            if ref not in text:
                errors.append(f"{_display_path(doc_path)} must reference {ref}.")
        errors.extend(_unsafe_doc_text_errors(text, doc_path))
    tasks_text = TASKS_PATH.read_text(encoding="utf-8")
    for criterion in (
        "Emit current line event.",
        "Match line IDs.",
        "Debug console.",
    ):
        if criterion not in tasks_text:
            errors.append(f"tasks/milestones.md must keep M3 criterion {criterion!r}.")
    return errors


def _unsafe_doc_text_errors(text: str, doc_path: Path) -> list[str]:
    lowered = text.lower()
    errors: list[str] = []
    for phrase in (
        "current-line capture is approved",
        "real text capture is approved",
        "ui text reading is approved",
        "unity scanning is approved",
        "provider execution is approved",
        "companion contract change is approved",
    ):
        if phrase in lowered:
            errors.append(f"{_display_path(doc_path)} must not say {phrase!r}.")
    return errors


def _baseline_file_errors() -> list[str]:
    errors: list[str] = []
    for ref in BASELINE_REFS:
        if not (ROOT / ref).exists():
            errors.append(f"M3 baseline file is missing: {ref}.")
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


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
