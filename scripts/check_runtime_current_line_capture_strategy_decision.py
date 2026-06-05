from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover
    from schema_validator import load_json
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/runtime_current_line_capture_strategy_decision.synthetic.json"
DOC_PATH = ROOT / "docs/runtime-current-line-capture-strategy-decision.md"
ADR_PATH = ROOT / "docs/adr/0008-current-line-capture-research.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
KNOWN_RISKS_PATH = ROOT / "docs/devlog/KNOWN_RISKS.md"
DECISIONS_PENDING_PATH = ROOT / "docs/devlog/DECISIONS_PENDING.md"
CHECK_ALL_PATH = ROOT / "scripts/check_all.py"
GITIGNORE_PATH = ROOT / ".gitignore"

SCHEMA_VERSION = "runtime-current-line-capture-strategy-decision.v1"
SELECTED_STRATEGY = "targeted_hook_research_first"
RECOMMENDED_NEXT_STEP = "runtime_targeted_hook_candidate_research_contract"
PRIVATE_RESEARCH_ROOT = "workspace/local-private/runtime-capture/hook-research/"

REQUIRED_TRUE_FIELDS = (
    "runtime_first_path_active",
    "manual_synthetic_transport_proven",
    "runtime_translation_memory_done",
    "runtime_current_line_transport_done",
    "runtime_current_line_capture_spike_done",
)
REQUIRED_FALSE_FIELDS = (
    "m2_private_export_source_available",
    "implementation_allowed_next",
    "hook_implementation_allowed_next",
    "real_text_capture_allowed_next",
    "broad_unity_scanning_allowed_next",
    "ocr_allowed_next",
    "screenshots_allowed_next",
    "save_file_reads_allowed_next",
    "game_file_reads_allowed_next",
    "bepinex_log_parsing_allowed_next",
    "provider_execution_allowed_next",
    "companion_contract_change_allowed_next",
    "decompiled_identifiers_in_tracked_docs_allowed",
    "raw_logs_allowed",
    "payload_dumps_allowed",
    "private_paths_allowed",
    "committed_runtime_evidence_allowed",
)

SECRET_PATTERN = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|api[_-]?key\s*=|bearer\s+)", re.I)
URL_PATTERN = re.compile(r"https?://", re.I)
PRIVATE_PATH_PATTERN = re.compile(r"(\b[A-Za-z]:[\\/]|/(?:home|Users|mnt|Volumes)/)", re.I)
METHOD_SIGNATURE_PATTERN = re.compile(
    r"\b(?:public|private|internal|protected|static|virtual|override|void|string|bool|int)\s+"
    r"[A-Za-z_][A-Za-z0-9_]*\s*\(",
    re.I,
)
QUALIFIED_IDENTIFIER_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z0-9_]{2,}\.(?:[A-Z][A-Za-z0-9_]{2,}|[a-z][A-Za-z0-9_]{2,})\b"
)

FORBIDDEN_MARKERS = (
    "HarmonyPatch",
    "[HarmonyPatch",
    "LogOutput.log",
    "Player.log",
    "output_log.txt",
    "stack trace",
    "Traceback (most recent call last)",
    "request payload",
    "response payload",
    "raw companion payload",
    "provider payload",
    "source_text",
    "raw_english_text",
    "dialogue text",
    "captured text",
    "private runtime text",
    ".png",
    ".jpg",
    ".jpeg",
    "screenshot",
    "screen capture",
    "steamapps",
    "database.json",
    "game hook implementation",
    "method hook implementation",
    "FindObjectOfType",
    "FindObjectsOfType",
    "GameObject.Find",
    "Resources.FindObjectsOfTypeAll",
    "SceneManager",
    "OCR",
    "Tesseract",
    "provider execution approved",
    "api.openai",
    "deepl",
    "anthropic",
    "local_model",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the runtime current-line capture strategy decision."
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    errors = collect_runtime_current_line_capture_strategy_decision_errors()
    if errors:
        print(
            "Runtime current-line capture strategy decision check failed."
            if args.quiet
            else "\n".join(errors)
        )
        return 1
    if args.quiet:
        print("Runtime current-line capture strategy decision check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "runtime-current-line-capture-strategy-decision-check.v1",
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_runtime_current_line_capture_strategy_decision_errors(
    path: Path = FIXTURE_PATH,
) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load runtime capture strategy fixture: {exc}"]
    if not isinstance(payload, dict):
        return ["Runtime capture strategy fixture must be a JSON object."]
    errors: list[str] = []
    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
        errors.extend(_check_all_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("decision_status") != "strategy_selected":
        errors.append("decision_status must be 'strategy_selected'.")
    if payload.get("selected_strategy") != SELECTED_STRATEGY:
        errors.append(f"selected_strategy must be {SELECTED_STRATEGY!r}.")
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(f"recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}.")
    if payload.get("targeted_hook_candidate_research_contract_allowed_next") != "contract_only":
        errors.append(
            "targeted_hook_candidate_research_contract_allowed_next must be 'contract_only'."
        )
    for field in REQUIRED_TRUE_FIELDS:
        if payload.get(field) is not True:
            errors.append(f"{field} must be true.")
    for field in REQUIRED_FALSE_FIELDS:
        if payload.get(field) is not False:
            errors.append(f"{field} must be false.")
    roots = payload.get("allowed_private_research_roots")
    if roots != [PRIVATE_RESEARCH_ROOT]:
        errors.append(f"allowed_private_research_roots must be {[PRIVATE_RESEARCH_ROOT]!r}.")
    for root in roots if isinstance(roots, list) else []:
        if not isinstance(root, str):
            errors.append("allowed_private_research_roots entries must be strings.")
            continue
        if not root.startswith("workspace/local-private/") or not root.endswith("/"):
            errors.append(
                "allowed_private_research_roots must stay under workspace/local-private/."
            )
        if ".." in Path(root).parts:
            errors.append("allowed_private_research_roots must not contain '..'.")
    if "workspace/" not in GITIGNORE_PATH.read_text(encoding="utf-8"):
        errors.append(".gitignore must keep workspace/ ignored.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    allowed = {
        SCHEMA_VERSION,
        SELECTED_STRATEGY,
        RECOMMENDED_NEXT_STEP,
        PRIVATE_RESEARCH_ROOT,
        "strategy_selected",
        "contract_only",
    }
    errors: list[str] = []
    for value in _iter_string_values(payload):
        if value in allowed:
            continue
        errors.extend(_unsafe_text_errors(value, _display_path(path)))
    return errors


def _doc_errors() -> list[str]:
    required_refs = (
        "docs/runtime-current-line-capture-strategy-decision.md",
        "tests/fixtures/runtime_current_line_capture_strategy_decision.synthetic.json",
        "scripts/check_runtime_current_line_capture_strategy_decision.py",
        SELECTED_STRATEGY,
        RECOMMENDED_NEXT_STEP,
    )
    errors: list[str] = []
    for doc_path in (
        DOC_PATH,
        ADR_PATH,
        SESSION_SUMMARY_PATH,
        NEXT_ACTIONS_PATH,
        KNOWN_RISKS_PATH,
        DECISIONS_PENDING_PATH,
    ):
        if not doc_path.exists():
            errors.append(f"Missing doc target: {_display_path(doc_path)}.")
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        refs_for_doc = required_refs
        if doc_path == DOC_PATH:
            refs_for_doc = required_refs[1:]
        for ref in refs_for_doc:
            if ref not in text:
                errors.append(f"{_display_path(doc_path)} must reference {ref}.")
        if doc_path == DOC_PATH:
            errors.extend(_unsafe_doc_text_errors(text, _display_path(doc_path)))
    return errors


def _check_all_errors() -> list[str]:
    text = CHECK_ALL_PATH.read_text(encoding="utf-8")
    if "scripts/check_runtime_current_line_capture_strategy_decision.py" not in text:
        return ["scripts/check_all.py must register the runtime capture strategy checker."]
    return []


def _unsafe_text_errors(value: str, label: str) -> list[str]:
    errors: list[str] = []
    if URL_PATTERN.search(value):
        errors.append(f"{label} contains an external URL.")
    if SECRET_PATTERN.search(value):
        errors.append(f"{label} contains a secret-looking value.")
    if PRIVATE_PATH_PATTERN.search(value):
        errors.append(f"{label} contains a private absolute path.")
    lowered = value.lower()
    for marker in FORBIDDEN_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"{label} contains forbidden marker {marker!r}.")
    if METHOD_SIGNATURE_PATTERN.search(value):
        errors.append(f"{label} contains a method-signature-looking value.")
    if QUALIFIED_IDENTIFIER_PATTERN.search(value):
        errors.append(f"{label} contains a qualified identifier-looking value.")
    return errors


def _unsafe_doc_text_errors(value: str, label: str) -> list[str]:
    errors: list[str] = []
    for marker in (
        "HarmonyPatch",
        "[HarmonyPatch",
        "LogOutput.log",
        "Player.log",
        "output_log.txt",
        "request payload",
        "response payload",
        "raw companion payload",
        "source_text",
        ".png",
        ".jpg",
        ".jpeg",
        "steamapps",
        "database.json",
        "FindObjectOfType",
        "FindObjectsOfType",
        "GameObject.Find",
        "Resources.FindObjectsOfTypeAll",
        "Tesseract",
        "api.openai",
    ):
        if marker.lower() in value.lower():
            errors.append(f"{label} contains forbidden tracked-doc marker {marker!r}.")
    if METHOD_SIGNATURE_PATTERN.search(value):
        errors.append(f"{label} contains a method-signature-looking value.")
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
