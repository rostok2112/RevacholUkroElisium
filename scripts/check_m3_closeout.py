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


FIXTURE_PATH = ROOT / "tests/fixtures/m3_closeout.synthetic.json"
DOC_PATH = ROOT / "docs/m3-closeout.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
KNOWN_RISKS_PATH = ROOT / "docs/devlog/KNOWN_RISKS.md"
DECISIONS_PENDING_PATH = ROOT / "docs/devlog/DECISIONS_PENDING.md"
BEPINEX_DOC_PATH = ROOT / "docs/bepinex-bridge.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SCHEMA_VERSION = "m3-closeout.v1"
ROADMAP_MILESTONE = "M3"
NEXT_ROADMAP_MILESTONE = "M4"
RECOMMENDED_NEXT_STEP = "m4_real_overlay_scope_recovery"
REQUIRED_TRUE_FIELDS = (
    "m2_closed",
    "m3_scope_recovery_done",
    "m3_current_line_event_contract_done",
    "m3_current_line_event_done",
    "m3_line_id_matching_done",
    "m3_debug_console_done",
    "m3_complete",
)
FORBIDDEN_PERMISSION_FIELDS = (
    "raw_text_capture_allowed",
    "raw_text_dump_allowed",
    "payload_dump_allowed",
    "line_id_dump_allowed",
    "record_id_dump_allowed",
    "source_text_dump_allowed",
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
    "raw text capture approved",
    "raw text dump approved",
    "payload dump approved",
    "line id dump approved",
    "record id dump approved",
    "source text dump approved",
    "ui text reading approved",
    "unity scanning approved",
    "hook implementation approved",
    "ocr approved",
    "provider execution approved",
    "companion contract change approved",
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
    parser = argparse.ArgumentParser(description="Validate M3 closeout.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)
    errors = collect_m3_closeout_errors()
    if errors:
        if args.quiet:
            print("M3 closeout check failed.")
        else:
            print("\n".join(errors))
        return 1
    if args.quiet:
        print("M3 closeout check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m3-closeout-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "next_roadmap_milestone": NEXT_ROADMAP_MILESTONE,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m3_closeout_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M3 closeout fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["M3 closeout fixture must be a JSON object."]
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
        "scope_status": "closed",
        "next_roadmap_milestone": NEXT_ROADMAP_MILESTONE,
        "required_next_step": RECOMMENDED_NEXT_STEP,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }
    for field, expected in expected_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"M3 closeout {field} must be {expected!r}.")
    if "m3_commit_cap" in payload or "m3_commits_used" in payload:
        errors.append("M3 closeout fixture must not encode commit cap metadata.")
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M3 closeout fixture must set {field}=true.")
    for field in FORBIDDEN_PERMISSION_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M3 closeout fixture must keep {field}=false.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        NEXT_ROADMAP_MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "closed",
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
        "docs/m3-closeout.md",
        "tests/fixtures/m3_closeout.synthetic.json",
        "scripts/check_m3_closeout.py",
        RECOMMENDED_NEXT_STEP,
    )
    for doc_path in (
        DOC_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        KNOWN_RISKS_PATH,
        DECISIONS_PENDING_PATH,
        BEPINEX_DOC_PATH,
    ):
        if not doc_path.exists():
            errors.append(f"Missing M3 closeout doc target: {doc_path.name}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        for ref in required_refs:
            if ref not in text:
                errors.append(f"{_display_path(doc_path)} must reference {ref}.")
    tasks = TASKS_PATH.read_text(encoding="utf-8")
    for criterion in ("Emit current line event.", "Match line IDs.", "Debug console."):
        if criterion not in tasks:
            errors.append(f"tasks/milestones.md must keep M3 criterion {criterion!r}.")
    if "## M4" not in tasks or "Compact translation." not in tasks:
        errors.append("tasks/milestones.md must keep original M4 real overlay milestone.")
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
