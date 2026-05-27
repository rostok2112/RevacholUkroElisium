from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from schema_validator import load_json
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/overlay_refresh_readiness_contract.synthetic.json"
DOC_PATH = ROOT / "docs/overlay-refresh-readiness-contract.md"
OVERLAY_DOC = ROOT / "docs/overlay-prototype.md"
BEPINEX_DOC = ROOT / "docs/bepinex-bridge.md"
SCHEMA_VERSION = "overlay-refresh-readiness-contract.v1"
RECOMMENDED_NEXT_STEP = "metadata_only_overlay_refresh_helper"

READINESS_STATES = (
    "no_companion",
    "companion_available",
    "no_provider_state",
    "provider_state_ready",
    "overlay_state_ready",
    "overlay_view_ready",
    "overlay_html_review_ready",
    "stale",
    "error",
)

REQUIRED_SAFE_INPUTS = (
    "companion_health_status",
    "latest_provider_context_exists",
    "latest_provider_annotation_exists",
    "overlay_state_source_status",
    "overlay_state_source_validation_status",
    "overlay_view_model_validation_status",
    "accessibility_validation_status",
    "redacted_stale_status",
    "redacted_error_status",
)

FORBIDDEN_PERMISSION_FIELDS = (
    "current_line_capture_allowed",
    "real_text_capture_allowed",
    "ui_text_reading_allowed",
    "unity_scanning_allowed",
    "hooks_allowed",
    "ocr_allowed",
    "extraction_allowed",
    "real_provider_execution_allowed",
    "companion_contract_change_allowed",
    "production_overlay_shell_allowed",
    "polling_loop_allowed",
    "timer_allowed",
    "background_worker_allowed",
)

URL_PATTERN = re.compile(r"https?://[^\s\"'<>)]+", re.IGNORECASE)
SECRET_VALUE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*=)",
    re.IGNORECASE,
)
WINDOWS_PRIVATE_PATH_PATTERN = re.compile(
    r"\b[A-Za-z]:(?:\\\\|\\)(?:Users|Program Files|Games|Steam|GOG)(?:\\\\|\\)"
)
POSIX_PRIVATE_PATH_PATTERN = re.compile(r"(?<!\w)/(?:home|Users|mnt|Volumes|Applications)/")

FORBIDDEN_MARKERS = (
    "real_game_text",
    "real game text",
    "ui_text_string",
    "ui text string",
    "current_line_content",
    "current line content",
    "unity_object_name",
    "unity object name",
    "runtime_scene_name",
    "runtime scene name",
    "screenshot",
    "screen capture",
    "ocr output",
    "raw log",
    "logoutput.log",
    "player.log",
    "raw_provider_payload",
    "raw provider payload",
    "payload dump",
    "provider payload dump",
    "stack trace",
    "traceback (most recent call last)",
    "companion endpoint change",
    "new companion endpoint",
    "real provider call",
    "provider execution approved",
    "capture approved",
    "current-line capture approved",
    "real text capture approved",
    "steamapps",
    "data/extracted",
    "data/local",
)


class OverlayRefreshReadinessContractError(RuntimeError):
    """Raised when the overlay refresh readiness fixture is unsafe or malformed."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the metadata-only overlay refresh readiness contract fixture."
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_overlay_refresh_readiness_contract_errors()
    if errors:
        if args.quiet:
            print("Overlay refresh readiness contract check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("Overlay refresh readiness contract check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "overlay-refresh-readiness-contract-check.v1",
                    "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
                    "metadata_only": True,
                    "runtime_implementation_required": False,
                },
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


def assert_overlay_refresh_readiness_contract_safe(path: Path = FIXTURE_PATH) -> None:
    errors = collect_overlay_refresh_readiness_contract_errors(path)
    if errors:
        raise OverlayRefreshReadinessContractError("; ".join(errors))


def collect_overlay_refresh_readiness_contract_errors(path: Path = FIXTURE_PATH) -> list[str]:
    errors: list[str] = []
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load overlay refresh readiness fixture: {exc}"]

    if not isinstance(payload, dict):
        return ["Overlay refresh readiness fixture must be a JSON object."]

    errors.extend(_shape_errors(payload))
    errors.extend(_safety_errors(payload, path))
    if path == FIXTURE_PATH:
        errors.extend(_doc_link_errors())
    return errors


def _shape_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Overlay refresh readiness schema_version must be {SCHEMA_VERSION!r}.")
    if payload.get("bridge_to_overlay_smoke_passed") is not True:
        errors.append(
            "Overlay refresh readiness fixture must set bridge_to_overlay_smoke_passed=true."
        )
    if payload.get("metadata_only") is not True:
        errors.append("Overlay refresh readiness fixture must set metadata_only=true.")
    if payload.get("recommended_next_step") != RECOMMENDED_NEXT_STEP:
        errors.append(
            f"Overlay refresh readiness recommended_next_step must be {RECOMMENDED_NEXT_STEP!r}."
        )

    states = payload.get("readiness_states")
    if not isinstance(states, list) or not all(isinstance(item, str) for item in states):
        errors.append("Overlay refresh readiness readiness_states must be a list of strings.")
    else:
        if tuple(states) != READINESS_STATES:
            errors.append(
                "Overlay refresh readiness states must exactly match: "
                + ", ".join(READINESS_STATES)
                + "."
            )

    inputs = payload.get("allowed_metadata_inputs")
    if not isinstance(inputs, list) or not all(isinstance(item, str) for item in inputs):
        errors.append(
            "Overlay refresh readiness allowed_metadata_inputs must be a list of strings."
        )
    else:
        input_set = set(inputs)
        for required in REQUIRED_SAFE_INPUTS:
            if required not in input_set:
                errors.append(
                    f"Overlay refresh readiness allowed_metadata_inputs must include {required!r}."
                )

    for field in FORBIDDEN_PERMISSION_FIELDS:
        if not isinstance(payload.get(field), bool):
            errors.append(f"Overlay refresh readiness field {field!r} must be a boolean.")
        elif payload.get(field) is not False:
            errors.append(f"Overlay refresh readiness fixture must keep {field}=false.")

    if payload.get("bridge_to_overlay_smoke_passed") and any(
        payload.get(field) for field in FORBIDDEN_PERMISSION_FIELDS
    ):
        errors.append(
            "Overlay refresh readiness smoke success cannot imply capture, provider, shell, "
            "polling, or companion contract permission."
        )

    if not isinstance(payload.get("required_next_step"), str) or not payload.get(
        "required_next_step"
    ):
        errors.append("Overlay refresh readiness fixture must include required_next_step.")
    return errors


def _safety_errors(payload: dict[str, Any], path: Path) -> list[str]:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    relative = _display_path(path)
    errors: list[str] = []

    for url in URL_PATTERN.findall(rendered):
        errors.append(f"{relative}: contains external URL {url!r}.")
    if SECRET_VALUE_PATTERN.search(rendered):
        errors.append(f"{relative}: contains a secret/API-key-looking value.")
    if WINDOWS_PRIVATE_PATH_PATTERN.search(rendered) or POSIX_PRIVATE_PATH_PATTERN.search(rendered):
        errors.append(f"{relative}: contains a private absolute path.")

    lowered = rendered.lower()
    for marker in FORBIDDEN_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"{relative}: contains forbidden marker {marker!r}.")
    return errors


def _doc_link_errors() -> list[str]:
    errors: list[str] = []
    fixture_ref = str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/")
    checker_ref = "scripts/check_overlay_refresh_readiness_contract.py"
    for doc_path in (DOC_PATH, OVERLAY_DOC, BEPINEX_DOC):
        if not doc_path.exists():
            errors.append(
                f"Missing overlay refresh readiness doc link target: {_display_path(doc_path)}."
            )
            continue
        text = doc_path.read_text(encoding="utf-8").replace("\\", "/")
        if fixture_ref not in text:
            errors.append(f"{_display_path(doc_path)} must point to {fixture_ref}.")
        if checker_ref not in text:
            errors.append(f"{_display_path(doc_path)} must point to {checker_ref}.")
        if "current-line capture is approved" in text.lower():
            errors.append(f"{_display_path(doc_path)} must not approve current-line capture.")
        if "real text capture is approved" in text.lower():
            errors.append(f"{_display_path(doc_path)} must not approve real text capture.")
    return errors


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
