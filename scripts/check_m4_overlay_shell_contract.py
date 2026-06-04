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


FIXTURE_PATH = ROOT / "tests/fixtures/m4_overlay_shell_contract.synthetic.json"
DOC_PATH = ROOT / "docs/m4-overlay-shell-contract.md"
SCOPE_DOC_PATH = ROOT / "docs/m4-real-overlay-scope.md"
OVERLAY_DOC_PATH = ROOT / "docs/overlay-prototype.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
KNOWN_RISKS_PATH = ROOT / "docs/devlog/KNOWN_RISKS.md"
DECISIONS_PENDING_PATH = ROOT / "docs/devlog/DECISIONS_PENDING.md"
GITIGNORE_PATH = ROOT / ".gitignore"
SCHEMA_VERSION = "m4-overlay-shell-contract.v1"
ROADMAP_MILESTONE = "M4"
RECOMMENDED_NEXT_STEP = "m4_compact_translation_shell"
ALLOWED_INPUT_SCHEMA_VERSIONS = ("overlay-state-source.v1", "local-overlay-prototype.v1")
REQUIRED_REUSED_MODULES = (
    "scripts/overlay_state_source.py",
    "scripts/local_overlay_prototype.py",
    "scripts/overlay_viewmodel_validator.py",
    "scripts/overlay_actions.py",
)
ALLOWED_PRIVATE_OUTPUT_ROOTS = ("workspace/local-private/overlay/",)

REQUIRED_TRUE_FIELDS = (
    "m4_scope_recovery_done",
    "browser_shell_contract_defined",
)
CONTRACT_ONLY_FIELDS = (
    "compact_translation_allowed_next",
    "genius_card_allowed_next",
    "page_local_hotkeys_allowed_next",
)
INCOMPLETE_M4_FIELDS = (
    "m4_compact_translation_done",
    "m4_genius_card_done",
    "m4_hotkeys_done",
)
FORBIDDEN_PERMISSION_FIELDS = (
    "implementation_allowed_next",
    "native_always_on_top_allowed",
    "electron_or_tauri_setup_allowed",
    "global_keyboard_hooks_allowed",
    "clipboard_writes_allowed",
    "ocr_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "game_file_reads_allowed",
    "bepinex_log_reads_allowed",
    "raw_provider_payload_included",
    "debug_internals_in_player_view_allowed",
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
    "provider execution approved",
    "companion contract change approved",
    "debug internals in player view approved",
    "raw provider payload",
    "raw prompt",
    "payload dump",
    "raw log",
    "logoutput.log",
    "player.log",
    "screenshot",
    "steamapps",
    "decompiled",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate M4 overlay shell contract.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m4_overlay_shell_contract_errors()
    if errors:
        if args.quiet:
            print("M4 overlay shell contract check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("M4 overlay shell contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m4-overlay-shell-contract-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m4_overlay_shell_contract_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M4 overlay shell contract fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M4 overlay shell contract fixture must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_root_errors(payload))
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
        "m4_commit_cap": 6,
        "m4_commits_used": 2,
        "required_next_step": RECOMMENDED_NEXT_STEP,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M4 overlay shell contract {field} must be {expected!r}.")
    if tuple(payload.get("allowed_input_schema_versions", ())) != ALLOWED_INPUT_SCHEMA_VERSIONS:
        errors.append("M4 overlay shell contract must keep the approved input schema versions.")
    if tuple(payload.get("required_reused_modules", ())) != REQUIRED_REUSED_MODULES:
        errors.append("M4 overlay shell contract must reuse the approved overlay modules.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M4 overlay shell contract fixture must set {field}=true.")
    for field in CONTRACT_ONLY_FIELDS:
        if payload.get(field) != "contract_defined_only":
            errors.append(f"M4 overlay shell contract fixture must set {field!r} contract-only.")
    for field in INCOMPLETE_M4_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M4 overlay shell contract fixture must keep {field}=false.")
    for field in FORBIDDEN_PERMISSION_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M4 overlay shell contract fixture must keep {field}=false.")
    return errors


def _root_errors(payload: dict[str, Any]) -> list[str]:
    roots = payload.get("allowed_private_output_roots")
    errors: list[str] = []
    if not isinstance(roots, list) or not all(isinstance(root, str) for root in roots):
        errors.append("M4 overlay shell allowed private output roots must be a list of strings.")
    elif tuple(roots) != ALLOWED_PRIVATE_OUTPUT_ROOTS:
        errors.append("M4 overlay shell output root must be workspace/local-private/overlay/.")
    else:
        for root in roots:
            if root != root.replace("\\", "/"):
                errors.append("M4 overlay shell output roots must use forward slashes.")
            if not root.startswith("workspace/local-private/") or not root.endswith("/"):
                errors.append(
                    "M4 overlay shell output root must stay under workspace/local-private/."
                )
            if ".." in Path(root).parts:
                errors.append("M4 overlay shell output root must not contain '..'.")
    if "workspace/" not in GITIGNORE_PATH.read_text(encoding="utf-8"):
        errors.append(".gitignore must keep workspace/ ignored.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "contract_only",
        "contract_defined_only",
        *ALLOWED_INPUT_SCHEMA_VERSIONS,
        *REQUIRED_REUSED_MODULES,
        *ALLOWED_PRIVATE_OUTPUT_ROOTS,
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
        "docs/m4-overlay-shell-contract.md",
        "tests/fixtures/m4_overlay_shell_contract.synthetic.json",
        "scripts/check_m4_overlay_shell_contract.py",
        RECOMMENDED_NEXT_STEP,
    )
    for doc_path in (
        DOC_PATH,
        SCOPE_DOC_PATH,
        OVERLAY_DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        KNOWN_RISKS_PATH,
        DECISIONS_PENDING_PATH,
    ):
        if not doc_path.exists():
            errors.append(f"Missing M4 overlay shell contract doc target: {doc_path.name}.")
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
