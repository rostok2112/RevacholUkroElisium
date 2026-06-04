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


FIXTURE_PATH = ROOT / "tests/fixtures/m4_real_overlay_scope.synthetic.json"
DOC_PATH = ROOT / "docs/m4-real-overlay-scope.md"
M3_CLOSEOUT_DOC_PATH = ROOT / "docs/m3-closeout.md"
OVERLAY_DOC_PATH = ROOT / "docs/overlay-prototype.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
KNOWN_RISKS_PATH = ROOT / "docs/devlog/KNOWN_RISKS.md"
DECISIONS_PENDING_PATH = ROOT / "docs/devlog/DECISIONS_PENDING.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SCHEMA_VERSION = "m4-real-overlay-scope.v1"
ROADMAP_MILESTONE = "M4"
RECOMMENDED_NEXT_STEP = "m4_overlay_shell_contract"

REQUIRED_TRUE_FIELDS = (
    "m3_closed",
    "existing_overlay_contract_reused",
    "overlay_viewmodel_fixtures_reused",
    "overlay_viewmodel_validator_reused",
    "overlay_state_source_reused",
    "overlay_actions_reused",
    "overlay_review_renderer_reused",
    "overlay_accessibility_checker_reused",
    "overlay_refresh_readiness_reused",
)

INCOMPLETE_M4_FIELDS = (
    "m4_compact_translation_done",
    "m4_genius_card_done",
    "m4_hotkeys_done",
    "real_overlay_shell_done",
)

FORBIDDEN_PERMISSION_FIELDS = (
    "duplicate_overlay_prototype_allowed",
    "native_always_on_top_allowed",
    "electron_or_tauri_setup_allowed",
    "global_keyboard_hooks_allowed",
    "page_local_hotkeys_allowed_next",
    "clipboard_writes_allowed",
    "ocr_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "game_file_reads_allowed",
    "bepinex_log_reads_allowed",
    "raw_provider_payload_commit_allowed",
    "generated_shell_artifact_commit_allowed",
    "screenshots_commit_allowed",
    "private_paths_commit_allowed",
    "real_game_text_commit_allowed",
)

URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
PRIVATE_PATH_PATTERN = re.compile(
    r"(\b[A-Za-z]:[\\/](?:Users|Program Files|Games|Steam|GOG|AppData)[\\/]|/(?:home|Users|mnt|Volumes|Applications)/)",
    re.IGNORECASE,
)
FORBIDDEN_VALUE_MARKERS = (
    "native always-on-top approved",
    "electron setup approved",
    "tauri setup approved",
    "global keyboard hook approved",
    "clipboard write approved",
    "ocr approved",
    "unity scanning approved",
    "hook implementation approved",
    "provider execution approved",
    "companion contract change approved",
    "game file read approved",
    "bepinex log read approved",
    "raw provider payload",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "steamapps",
    "decompiled",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate M4 real overlay scope recovery.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m4_real_overlay_scope_errors()
    if errors:
        if args.quiet:
            print("M4 real overlay scope check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("M4 real overlay scope check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m4-real-overlay-scope-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m4_real_overlay_scope_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M4 real overlay scope fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M4 real overlay scope fixture must be a JSON object."]

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
        "scope_status": "active",
        "required_next_step": RECOMMENDED_NEXT_STEP,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M4 scope {field} must be {expected!r}.")
    if "m4_commit_cap" in payload or "m4_commits_used" in payload:
        errors.append("M4 scope fixture must not encode commit cap metadata.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M4 scope fixture must set {field}=true.")
    for field in INCOMPLETE_M4_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M4 scope fixture must keep {field}=false.")
    for field in FORBIDDEN_PERMISSION_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M4 scope fixture must keep {field}=false.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "active",
    }
    for value in _iter_string_values(payload):
        if value in expected_values:
            continue
        for url in URL_PATTERN.findall(value):
            errors.append(f"{relative}: contains external URL {url!r}.")
        if SECRET_VALUE_PATTERN.search(value):
            errors.append(f"{relative}: contains a secret/API-key-looking value.")
        if PRIVATE_PATH_PATTERN.search(value):
            errors.append(f"{relative}: contains a private absolute path.")
        lowered = value.lower()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in lowered:
                errors.append(f"{relative}: contains forbidden marker {marker!r}.")
    return errors


def _doc_errors() -> list[str]:
    errors: list[str] = []
    required_refs = (
        "docs/m4-real-overlay-scope.md",
        "tests/fixtures/m4_real_overlay_scope.synthetic.json",
        "scripts/check_m4_real_overlay_scope.py",
        RECOMMENDED_NEXT_STEP,
    )
    for doc_path in (
        DOC_PATH,
        M3_CLOSEOUT_DOC_PATH,
        OVERLAY_DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        KNOWN_RISKS_PATH,
        DECISIONS_PENDING_PATH,
    ):
        if not doc_path.exists():
            errors.append(f"Missing M4 scope doc target: {doc_path.name}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for ref in required_refs:
            if ref not in text:
                errors.append(f"{_display_path(doc_path)} must reference {ref}.")

    tasks = TASKS_PATH.read_text(encoding="utf-8")
    for criterion in ("Compact translation.", "Genius card.", "Hotkeys."):
        if criterion not in tasks:
            errors.append(f"tasks/milestones.md must keep M4 criterion {criterion!r}.")
    if "## M5" not in tasks or "Maximum quality pipeline" not in tasks:
        errors.append("tasks/milestones.md must keep original M5 next milestone.")
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
