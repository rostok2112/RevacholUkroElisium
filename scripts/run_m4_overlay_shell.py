from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
from typing import Any

try:
    from scripts.overlay_viewmodel_validator import assert_valid_overlay_view_model
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from overlay_viewmodel_validator import assert_valid_overlay_view_model
    from schema_validator import load_json
    from synthetic_slice import ROOT


SCHEMA_VERSION = "m4-overlay-shell.v1"
DEFAULT_COMPACT_SOURCE = ROOT / "tests/fixtures/overlay_prototype.compact.viewmodel.synthetic.json"
OUTPUT_ROOT = ROOT / "workspace/local-private/overlay"
FORBIDDEN_HTML_MARKERS = (
    "synthetic_fixture",
    "mock_provider",
    "prompt_pack_guided",
    "provider_debug",
    "raw_provider_request",
    "prompt_pack_sections",
    "api_key",
    "access_token",
    "bearer ",
    "sk-",
    "password",
    "credential",
    "secret",
    "C:\\",
    "D:\\",
    "/Users/",
    "/home/",
    "steamapps",
    "LogOutput.log",
    "Player.log",
    "<script",
    "javascript:",
)


class M4OverlayShellError(ValueError):
    """Raised when the M4 overlay shell cannot render safely."""


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.self_test:
            summary = run_self_test(output=args.output)
        else:
            source = load_compact_view_model(args.source)
            html = build_compact_overlay_shell_html(source)
            output_path = write_html(html, args.output) if args.output else None
            summary = build_redacted_summary(source, output_path=output_path)
    except (M4OverlayShellError, OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.quiet:
        print(
            "M4 compact overlay shell: "
            f"{summary['render_status']} compact_translation_rendered="
            f"{str(summary['compact_translation_rendered']).lower()}."
        )
    else:
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render the M4 local browser overlay shell from an existing compact overlay view model. "
            "Generated HTML is allowed only under workspace/local-private/overlay/."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_COMPACT_SOURCE,
        help="Compact overlay view-model JSON. Defaults to the committed synthetic fixture.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional HTML output path under workspace/local-private/overlay/.",
    )
    parser.add_argument("--self-test", action="store_true", help="Render the committed fixture.")
    parser.add_argument("--quiet", action="store_true", help="Print one redacted status line.")
    return parser


def run_self_test(*, output: Path | None = None) -> dict[str, Any]:
    source = load_compact_view_model(DEFAULT_COMPACT_SOURCE)
    html = build_compact_overlay_shell_html(source)
    if "m4-compact-overlay" not in html:
        raise M4OverlayShellError("Self-test failed: compact shell marker missing.")
    compact = source["compact"]
    original = compact.get("original_english")
    if isinstance(original, str) and original and original in html:
        raise M4OverlayShellError("Self-test failed: original/source text leaked into shell HTML.")
    output_path = write_html(html, output) if output else None
    return build_redacted_summary(source, output_path=output_path)


def load_compact_view_model(path: Path) -> dict[str, Any]:
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise M4OverlayShellError("Compact overlay source must be a JSON object.")
    assert_valid_overlay_view_model(payload, expected_mode="compact")
    return payload


def build_compact_overlay_shell_html(view_model: dict[str, Any]) -> str:
    assert_valid_overlay_view_model(view_model, expected_mode="compact")
    compact = view_model["compact"]
    labels = _as_dict(compact.get("labels_uk"))
    translation = _string(compact.get("concise_meaning_uk"))
    confidence = _string(compact.get("confidence_summary_uk"))
    risk = _string(compact.get("risk_summary_uk"))
    deep_label = _string(compact.get("deep_notes_label_uk"))
    speaker = _string(compact.get("speaker"))

    html = "\n".join(
        [
            "<!doctype html>",
            '<html lang="uk">',
            "<head>",
            '  <meta charset="utf-8">',
            "  <title>Revachol M4 Overlay Shell</title>",
            "  <style>",
            "    :root { color-scheme: dark; font-family: Arial, sans-serif; }",
            "    body { margin: 0; background: transparent; color: #f4f0e8; }",
            "    .m4-compact-overlay { width: min(420px, calc(100vw - 24px)); margin: 12px; padding: 12px 14px; background: rgba(16, 18, 20, 0.92); border: 1px solid #8d8068; }",
            "    .eyebrow { margin: 0 0 6px; font-size: 12px; color: #c7bda7; text-transform: uppercase; }",
            "    .translation { margin: 0; font-size: 17px; line-height: 1.35; }",
            "    .meta { margin: 8px 0 0; font-size: 12px; color: #d4ccbd; }",
            "    .actions { margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; }",
            "    .action { border: 1px solid #7f725f; background: #211f1c; color: #f4f0e8; padding: 5px 8px; font-size: 12px; }",
            "  </style>",
            "</head>",
            "<body>",
            '  <main class="m4-compact-overlay" id="m4-compact-overlay" data-schema-version="m4-overlay-shell.v1">',
            f'    <p class="eyebrow">{_text(speaker or labels.get("concise_meaning", "Коротко українською"))}</p>',
            f'    <p class="translation">{_text(translation)}</p>',
            f'    <p class="meta">{_text(confidence)}</p>',
            f'    <p class="meta">{_text(risk)}</p>',
            f'    <p class="meta">{_text(deep_label)}</p>',
            '    <nav class="actions" aria-label="Overlay actions">',
            _render_compact_actions(compact.get("actions")),
            "    </nav>",
            "  </main>",
            "</body>",
            "</html>",
        ]
    )
    _assert_safe_html(html)
    return html


def write_html(html: str, output: Path) -> Path:
    safe_output = ensure_safe_output_path(output)
    safe_output.parent.mkdir(parents=True, exist_ok=True)
    safe_output.write_text(html + "\n", encoding="utf-8")
    return safe_output


def ensure_safe_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    allowed_root = OUTPUT_ROOT.resolve(strict=False)
    try:
        resolved.relative_to(allowed_root)
    except ValueError as exc:
        raise M4OverlayShellError(
            "Unsafe output path. Use a path under workspace/local-private/overlay/."
        ) from exc
    if resolved.suffix.lower() not in {".html", ".htm"}:
        raise M4OverlayShellError("Unsafe output path. Expected an .html file.")
    return resolved


def build_redacted_summary(
    view_model: dict[str, Any],
    *,
    output_path: Path | None,
) -> dict[str, Any]:
    compact = view_model["compact"]
    return {
        "schema_version": "m4-compact-overlay-shell-summary.v1",
        "render_status": "ready",
        "source_mode": "compact",
        "output_written": output_path is not None,
        "compact_translation_rendered": bool(compact.get("concise_meaning_uk")),
        "original_text_included": False,
        "debug_internals_included": False,
        "raw_provider_payloads_included": False,
        "private_paths_included": False,
        "screenshots_included": False,
        "provider_called": False,
        "companion_contract_changed": False,
        "global_keyboard_hooks_enabled": False,
        "clipboard_writes_enabled": False,
        "native_always_on_top_enabled": False,
        "recommended_next_step": "m4_genius_card_shell",
    }


def _render_compact_actions(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    rendered: list[str] = []
    for action in value:
        if not isinstance(action, dict) or action.get("debug_only") is True:
            continue
        if action.get("player_facing") is not True:
            continue
        label = _string(action.get("label_uk"))
        if label:
            rendered.append(f'      <span class="action">{_text(label)}</span>')
    return "\n".join(rendered)


def _assert_safe_html(html: str) -> None:
    lowered = html.lower()
    for marker in FORBIDDEN_HTML_MARKERS:
        if marker.lower() in lowered:
            raise M4OverlayShellError(f"Unsafe compact shell HTML marker: {marker}")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _text(value: Any) -> str:
    return escape(str(value or ""), quote=True)


if __name__ == "__main__":
    raise SystemExit(main())
