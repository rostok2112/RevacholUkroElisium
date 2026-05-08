from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts import check_overlay_viewmodel_fixtures as fixture_check
    from scripts.local_overlay_prototype import LocalOverlayPrototypeError, render_overlay_html
    from scripts.overlay_viewmodel_validator import (
        COMMON_FORBIDDEN_MARKERS,
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ImportError:  # pragma: no cover - used when run as a script path.
    import check_overlay_viewmodel_fixtures as fixture_check
    from local_overlay_prototype import LocalOverlayPrototypeError, render_overlay_html
    from overlay_viewmodel_validator import (
        COMMON_FORBIDDEN_MARKERS,
        OverlayViewModelValidationError,
        assert_valid_overlay_view_model,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


MODES = ("compact", "deep", "debug")
DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/overlay-prototype/review"
INDEX_FILE = "index.html"

PLAYER_MODE_FORBIDDEN_MARKERS = (
    "synthetic_fixture",
    "mock_provider",
    "deterministic_mock_provider",
    "deterministic_mock_pipeline",
    "prompt_pack_guided",
    "Prompt-pack policy keeps",
    "Raw risk flags",
    "Raw Deep Notes",
    "provider_debug",
    "provider-cache-v1.",
)

REVIEW_HTML_FORBIDDEN_MARKERS = tuple(
    marker for marker in COMMON_FORBIDDEN_MARKERS if marker not in {"<!doctype html>", "<html"}
)


class OverlayReviewError(ValueError):
    """Raised when fixture-backed overlay review HTML is unsafe or stale."""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Render local overlay review HTML from committed synthetic view-model fixtures. "
            "This never calls the companion server, providers, network, or real game tooling."
        )
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help=(
            "Directory for generated review HTML. Must be under "
            "workspace/synthetic-slice/overlay-prototype/review/."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("all", *MODES),
        default="all",
        help="Which fixture mode to render. Default: all.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short status line.")
    args = parser.parse_args()

    try:
        summary = render_overlay_review(output_root=args.output_root, mode=args.mode)
    except (OverlayReviewError, LocalOverlayPrototypeError, OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.quiet:
        print("Overlay review HTML rendered.")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def render_overlay_review(*, output_root: Path = DEFAULT_OUTPUT_ROOT, mode: str = "all") -> dict:
    resolved_root = resolve_output_root(output_root)
    modes = list(MODES) if mode == "all" else [mode]
    for selected_mode in modes:
        if selected_mode not in MODES:
            raise OverlayReviewError(f"Unsupported overlay review mode: {selected_mode}")

    resolved_root.mkdir(parents=True, exist_ok=True)
    written: dict[str, str] = {}
    for selected_mode in modes:
        view_model = load_view_model_fixture(selected_mode)
        html = render_overlay_html(view_model)
        validate_review_html(selected_mode, html)
        output_path = resolved_root / f"{selected_mode}.html"
        output_path.write_text(html + "\n", encoding="utf-8")
        written[selected_mode] = _display_path(output_path)

    index_html = build_index_html(modes)
    validate_index_html(index_html)
    index_path = resolved_root / INDEX_FILE
    index_path.write_text(index_html + "\n", encoding="utf-8")
    written["index"] = _display_path(index_path)

    return {
        "schema_version": "overlay-review-render.v1",
        "ok": True,
        "fixture_based": True,
        "calls_companion_server": False,
        "calls_provider": False,
        "output_root": _display_path(resolved_root),
        "written": written,
    }


def load_view_model_fixture(mode: str) -> dict[str, Any]:
    if mode not in MODES:
        raise OverlayReviewError(f"Unsupported overlay review mode: {mode}")
    fixture_path = fixture_check.FIXTURE_PATHS[mode]
    payload = load_json(fixture_path)
    try:
        assert_valid_overlay_view_model(payload, expected_mode=mode)
    except OverlayViewModelValidationError as exc:
        raise OverlayReviewError(f"{mode} fixture contract validation failed: {exc}") from exc
    return payload


def build_index_html(modes: list[str]) -> str:
    links = "\n".join(
        [
            f'        <li><a href="{escape(f"{mode}.html", quote=True)}">{escape(_mode_label(mode), quote=True)}</a></li>'
            for mode in modes
        ]
    )
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="uk">',
            "<head>",
            '  <meta charset="utf-8">',
            "  <title>Revachol Overlay Review</title>",
            "  <style>",
            "    body { margin: 2rem; background: #111; color: #eee; font-family: sans-serif; }",
            "    a { color: #aad7ff; }",
            "    code { background: #2b2b2b; padding: 0.1rem 0.25rem; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <main>",
            "    <h1>Revachol Overlay Review</h1>",
            "    <p>Generated from committed synthetic overlay view-model fixtures.</p>",
            "    <ul>",
            links,
            "    </ul>",
            "    <p><code>workspace/synthetic-slice/overlay-prototype/review/</code></p>",
            "  </main>",
            "</body>",
            "</html>",
        ]
    )


def validate_review_html(mode: str, html: str) -> None:
    _assert_markers_absent(html, REVIEW_HTML_FORBIDDEN_MARKERS, f"{mode} review HTML")
    if mode in {"compact", "deep"}:
        _assert_markers_absent(html, PLAYER_MODE_FORBIDDEN_MARKERS, f"{mode} player HTML")
        if mode == "compact":
            _assert_markers_present(
                html,
                ("Коротко українською", "Є глибше пояснення", "Впевненість"),
                "compact player HTML",
            )
        if mode == "deep":
            _assert_markers_present(
                html,
                (
                    "Оригінал",
                    "Літературний український варіант",
                    "Що тут відбувається",
                    "Підтекст / іронія / референс",
                    "Тон / голос",
                    "Глосарій",
                    "Ризики / невпевненість",
                ),
                "deep player HTML",
            )
    else:
        _assert_markers_present(
            html,
            (
                "Raw risk flags",
                "synthetic_fixture",
                "mock_provider",
                "prompt_pack_guided",
                "ukrainian_annotation_v1",
                "provider-cache-v1.",
                "Writes raw payload",
                "False",
            ),
            "debug review HTML",
        )


def validate_index_html(html: str) -> None:
    _assert_markers_absent(html, REVIEW_HTML_FORBIDDEN_MARKERS, "review index HTML")
    _assert_markers_absent(html, PLAYER_MODE_FORBIDDEN_MARKERS, "review index HTML")


def resolve_output_root(output_root: Path) -> Path:
    raw = output_root.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    allowed_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, allowed_root):
        raise OverlayReviewError(
            "Unsafe output root. Use a path under "
            "workspace/synthetic-slice/overlay-prototype/review/ for generated review HTML."
        )
    return resolved


def _assert_markers_absent(text: str, markers: tuple[str, ...], label: str) -> None:
    lowered = text.lower()
    for marker in markers:
        if marker.lower() in lowered:
            raise OverlayReviewError(f"{label} contains forbidden marker: {marker}")


def _assert_markers_present(text: str, markers: tuple[str, ...], label: str) -> None:
    for marker in markers:
        if marker not in text:
            raise OverlayReviewError(f"{label} is missing expected marker: {marker}")


def _mode_label(mode: str) -> str:
    return {
        "compact": "Compact / компактний",
        "deep": "Deep / глибоке пояснення",
        "debug": "Debug / developer",
    }[mode]


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
