from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.local_overlay_prototype import build_overlay_view_model
    from scripts.overlay_viewmodel_validator import (
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )
    from scripts.provider_pipeline import run_provider_pipeline
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT, build_context_packet
except ImportError:  # pragma: no cover - used when run as a script path.
    from local_overlay_prototype import build_overlay_view_model
    from overlay_viewmodel_validator import (
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )
    from provider_pipeline import run_provider_pipeline
    from schema_validator import load_json
    from synthetic_slice import ROOT, build_context_packet


FIXTURE_DIR = ROOT / "tests/fixtures"
DEFAULT_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
MODES = ("compact", "deep", "debug")
FIXTURE_PATHS = {
    mode: FIXTURE_DIR / f"overlay_prototype.{mode}.viewmodel.synthetic.json" for mode in MODES
}

RAW_INTERNAL_FLAGS = (
    "synthetic_fixture",
    "mock_provider",
    "deterministic_mock_provider",
    "deterministic_mock_pipeline",
    "prompt_pack_guided",
)
FUTURE_PROVIDER_MARKERS = (
    "openai_compatible",
    "deepl_glossary",
    "local_model",
    "ensemble_reviewer",
)
FORBIDDEN_ALL_FIXTURE_MARKERS = (
    "Disco Elysium: The Final Cut",
    "<!doctype html>",
    "<html",
    "prompt_pack_sections",
    "prompt_pack_focus_sections",
    "raw_provider_request",
    "api_key",
    "access_token",
    "bearer ",
    "sk-",
    "C:\\",
    "D:\\",
    "/Users/",
    "/home/",
    "data/extracted",
    "data/local",
    "steamapps",
    "http://",
    "https://",
) + FUTURE_PROVIDER_MARKERS


class OverlayFixtureError(ValueError):
    """Raised when overlay view-model fixtures drift or become unsafe."""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check or regenerate synthetic overlay prototype view-model fixtures."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Regenerate committed JSON fixtures intentionally.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short pass/fail line.")
    args = parser.parse_args()

    try:
        summary = check_overlay_viewmodel_fixtures(write=args.write)
    except (OverlayFixtureError, OSError, ValueError) as exc:
        if args.quiet:
            print(f"Overlay view-model fixture check failed: {exc}")
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if args.quiet:
        action = "updated" if args.write else "passed"
        print(f"Overlay view-model fixture check {action}.")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def check_overlay_viewmodel_fixtures(*, write: bool = False) -> dict[str, Any]:
    view_models = build_current_view_models()
    errors: list[str] = []
    drift: dict[str, list[str]] = {}

    for mode, view_model in view_models.items():
        try:
            validate_view_model_fixture(mode, view_model)
        except OverlayFixtureError as exc:
            errors.append(f"{mode}: {exc}")
            continue

        path = FIXTURE_PATHS[mode]
        rendered = canonical_json(view_model)
        if write:
            path.write_text(rendered + "\n", encoding="utf-8")
            continue
        if not path.exists():
            errors.append(f"{mode}: missing fixture {path.relative_to(ROOT)}")
            continue
        existing = path.read_text(encoding="utf-8")
        try:
            existing_payload = json.loads(existing)
            validate_view_model_fixture(mode, existing_payload)
        except (json.JSONDecodeError, OverlayFixtureError) as exc:
            errors.append(f"{mode}: committed fixture is invalid: {exc}")
            continue
        existing_rendered = canonical_json(existing_payload)
        if existing_rendered != rendered:
            drift[mode] = list(
                difflib.unified_diff(
                    existing_rendered.splitlines(),
                    rendered.splitlines(),
                    fromfile=_display_path(path),
                    tofile=f"current:{mode}",
                    lineterm="",
                )
            )

    if drift:
        drift_chunks = []
        for mode, lines in drift.items():
            drift_chunks.extend([f"{mode} fixture drift:", *lines])
        rendered_drift = "\n".join(drift_chunks)
        errors.append(rendered_drift)

    if errors:
        raise OverlayFixtureError("\n".join(errors))

    return {
        "schema_version": "overlay-viewmodel-fixture-check.v1",
        "ok": True,
        "write": write,
        "fixtures": {
            mode: str(path.relative_to(ROOT)).replace("\\", "/")
            for mode, path in FIXTURE_PATHS.items()
        },
    }


def build_current_view_models() -> dict[str, dict[str, Any]]:
    event = load_json(DEFAULT_EVENT)
    context_packet = build_context_packet(event)
    annotation_card = run_provider_pipeline(context_packet)
    return {
        mode: build_overlay_view_model(context_packet, annotation_card, mode=mode) for mode in MODES
    }


def validate_view_model_fixture(mode: str, view_model: dict[str, Any]) -> None:
    try:
        assert_valid_overlay_view_model(view_model, expected_mode=mode)
    except OverlayViewModelValidationError as exc:
        raise OverlayFixtureError(f"contract validation failed: {exc}") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


if __name__ == "__main__":
    sys.exit(main())
