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


FIXTURE_PATH = ROOT / "tests/fixtures/m2_local_extraction_import_scope.synthetic.json"
DOC_PATH = ROOT / "docs/adr/0012-m2-local-extraction-import-scope.md"
TASKS_PATH = ROOT / "tasks/milestones.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
GITIGNORE_PATH = ROOT / ".gitignore"
SCHEMA_VERSION = "m2-local-extraction-import-scope.v1"
ROADMAP_MILESTONE = "M2"
RECOMMENDED_NEXT_STEP = "m2_synthetic_import_format_contract"
ALLOWED_PRIVATE_INPUT_ROOTS = ("workspace/local-private/extraction-indexing/input/",)
ALLOWED_PRIVATE_OUTPUT_ROOTS = ("workspace/local-private/extraction-indexing/import/",)

REQUIRED_TRUE_FIELDS = (
    "local_only",
    "synthetic_fixtures_allowed",
    "explicit_user_selected_private_export_required",
    "contract_notes_redacted",
)

INCOMPLETE_M2_FIELDS = (
    "m2_import_locally_extracted_db_done",
    "m2_line_index_done",
    "m2_context_graph_done",
)

FORBIDDEN_PERMISSION_FIELDS = (
    "implementation_allowed_next",
    "automatic_game_install_scanning_allowed",
    "arbitrary_drive_scanning_allowed",
    "real_local_input_reads_allowed",
    "game_file_reads_allowed",
    "bepinex_log_reads_allowed",
    "screenshots_allowed",
    "ocr_allowed",
    "save_file_reads_allowed",
    "decompiled_code_allowed",
    "current_line_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "provider_execution_allowed",
    "companion_contract_change_allowed",
    "real_extracted_text_commit_allowed",
    "raw_extracted_payload_commit_allowed",
    "generated_index_commit_allowed",
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
WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[A-Za-z]:")

FORBIDDEN_VALUE_MARKERS = (
    "real extraction approved",
    "real local input reads approved",
    "game file reads approved",
    "steam scanning approved",
    "automatic game install scanning approved",
    "bepinex log reads approved",
    "current-line capture approved",
    "current line capture approved",
    "ui text reading approved",
    "unity scanning approved",
    "harmony patch approved",
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
    "screen capture",
    "steamapps",
    "savegame",
    ".sav",
    "decompiled",
    "dnspy",
    "ilspy",
)


class M2LocalExtractionImportScopeError(RuntimeError):
    """Raised when the original M2 scope fixture is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the original M2 local extraction import scope contract."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m2_local_extraction_import_scope_errors()
    if errors:
        if args.quiet:
            print("M2 local extraction import scope check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("M2 local extraction import scope check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m2-local-extraction-import-scope-check.v1",
                    "roadmap_milestone": ROADMAP_MILESTONE,
                    "implementation_allowed_next": False,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m2_local_extraction_import_scope_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 local extraction import scope fixture: {exc}"]

    if not isinstance(payload, dict):
        return ["M2 local extraction import scope fixture must be a JSON object."]

    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_root_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"M2 scope schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("roadmap_milestone") != ROADMAP_MILESTONE:
        errors.append(f"M2 scope roadmap_milestone must be {ROADMAP_MILESTONE!r}.")
    if payload.get("scope_status") != "contract_only":
        errors.append("M2 scope_status must be 'contract_only'.")
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(f"M2 recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}.")
    if payload.get("required_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(f"M2 required_next_step must be {RECOMMENDED_NEXT_STEP!r}.")

    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"M2 scope fixture must set {field}=true.")
    for field in INCOMPLETE_M2_FIELDS:
        if payload.get(field) is not False:
            errors.append(
                f"M2 scope fixture must keep {field}=false until original M2 is complete."
            )
    for field in FORBIDDEN_PERMISSION_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"M2 scope fixture must keep {field}=false.")
    return errors


def _root_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(
        _validate_roots(
            payload.get("allowed_private_input_roots"),
            expected=ALLOWED_PRIVATE_INPUT_ROOTS,
            label="input",
        )
    )
    errors.extend(
        _validate_roots(
            payload.get("allowed_private_output_roots"),
            expected=ALLOWED_PRIVATE_OUTPUT_ROOTS,
            label="output",
        )
    )
    if "workspace/" not in GITIGNORE_PATH.read_text(encoding="utf-8"):
        errors.append(".gitignore must keep workspace/ ignored for private M2 artifacts.")
    return errors


def _validate_roots(value: Any, *, expected: tuple[str, ...], label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return [f"M2 allowed private {label} roots must be a list of strings."]
    if tuple(value) != expected:
        return [f"M2 allowed private {label} roots must exactly match: {', '.join(expected)}."]

    errors: list[str] = []
    for root in value:
        normalized = root.replace("\\", "/")
        if normalized != root:
            errors.append(f"M2 private {label} root {root!r} must use forward slashes.")
        if not normalized.startswith("workspace/local-private/extraction-indexing/"):
            errors.append(f"M2 private {label} root {root!r} must stay under the ignored M2 root.")
        if not normalized.endswith("/"):
            errors.append(f"M2 private {label} root {root!r} must end with '/'.")
        if ".." in Path(normalized).parts or normalized.startswith("../"):
            errors.append(f"M2 private {label} root {root!r} must not contain '..'.")
        if normalized.startswith("/") or WINDOWS_ABSOLUTE_PATH_PATTERN.match(normalized):
            errors.append(f"M2 private {label} root {root!r} must be repo-relative.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    relative = _display_path(path)
    errors: list[str] = []
    expected_values = {
        SCHEMA_VERSION,
        ROADMAP_MILESTONE,
        RECOMMENDED_NEXT_STEP,
        "contract_only",
        *ALLOWED_PRIVATE_INPUT_ROOTS,
        *ALLOWED_PRIVATE_OUTPUT_ROOTS,
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
    fixture_ref = str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/")
    checker_ref = "scripts/check_m2_local_extraction_import_scope.py"
    adr_ref = "docs/adr/0012-m2-local-extraction-import-scope.md"
    for path in (DOC_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
        if not path.exists():
            errors.append(f"Missing M2 scope doc: {_display_path(path)}.")
            continue
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for required in (fixture_ref, checker_ref, adr_ref):
            if required not in text:
                errors.append(f"{_display_path(path)} must point to {required}.")

    tasks = TASKS_PATH.read_text(encoding="utf-8")
    for required in (
        "## M2",
        "Local extraction import",
        "Import locally extracted DB.",
        "Build line index.",
        "Build context graph.",
    ):
        if required not in tasks:
            errors.append(f"tasks/milestones.md must preserve original M2 text: {required!r}.")
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
