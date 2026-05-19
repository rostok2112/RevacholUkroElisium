from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
import sys
from typing import Any

try:
    from scripts.local_overlay_prototype import LocalOverlayPrototypeError, render_overlay_html
    from scripts.render_overlay_review import (
        MODES,
        PLAYER_MODE_FORBIDDEN_MARKERS,
        REVIEW_HTML_FORBIDDEN_MARKERS,
        OverlayReviewError,
        load_view_model_fixture,
    )
except ImportError:  # pragma: no cover - used when run as a script path.
    from local_overlay_prototype import LocalOverlayPrototypeError, render_overlay_html
    from render_overlay_review import (
        MODES,
        PLAYER_MODE_FORBIDDEN_MARKERS,
        REVIEW_HTML_FORBIDDEN_MARKERS,
        OverlayReviewError,
        load_view_model_fixture,
    )


SCHEMA_VERSION = "overlay-review-accessibility-check.v1"
COMPACT_MAX_PARAGRAPHS = 10
COMPACT_MAX_VISIBLE_TEXT_LENGTH = 800

SECTION_IDS = {
    "compact": "compact-mode",
    "deep": "deep-mode",
    "debug": "debug-mode",
}

COMMON_FORBIDDEN_MARKERS = REVIEW_HTML_FORBIDDEN_MARKERS + (
    "Disco Elysium: The Final Cut",
    "raw_provider_request",
    "prompt_pack_sections",
    "prompt_pack_focus_sections",
)

UNESCAPED_FORBIDDEN_MARKERS = (
    "<script",
    "</script",
    "javascript:",
    "http://",
    "https://",
)

COMPACT_REQUIRED_MARKERS = (
    "compact-mode",
    "Коротко українською",
    "Є глибше пояснення",
    "Впевненість",
    "Дії",
    "Глибше пояснення",
    "Скопіювати український зміст",
)

DEEP_REQUIRED_HEADINGS = (
    "Оригінал",
    "Літературний український варіант",
    "Що тут відбувається",
    "Підтекст / іронія / референс",
    "Тон / голос",
    "Глосарій",
    "Ризики / невпевненість",
)

DEEP_REQUIRED_MARKERS = (
    "deep-mode",
    *DEEP_REQUIRED_HEADINGS,
    "Дії",
    "Наступна нотатка",
    "Скопіювати пояснення",
)

DEBUG_REQUIRED_MARKERS = (
    "debug-mode",
    "Debug / Developer Metadata",
    "Raw risk flags",
    "synthetic_fixture",
    "mock_provider",
    "prompt_pack_guided",
    "Privacy / Cache Dry Run",
    "provider-cache-v1.",
    "Declarative Actions",
    "switch_debug",
    "debug_only=True",
)

DEBUG_FORBIDDEN_MARKERS = (
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
    "openai_compatible",
    "deepl_glossary",
    "local_model",
    "ensemble_reviewer",
)


class OverlayReviewAccessibilityError(ValueError):
    """Raised when fixture-rendered overlay HTML fails static guardrails."""


class ParsedOverlayHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html_lang: str | None = None
        self.section_ids: list[str] = []
        self.headings: list[tuple[int, str]] = []
        self.titles: list[str] = []
        self.paragraphs: list[str] = []
        self.visible_text_chunks: list[str] = []
        self.script_tag_count = 0
        self.event_handler_attrs: list[str] = []
        self.javascript_attrs: list[str] = []
        self._tag_stack: list[str] = []
        self._capture_tag: str | None = None
        self._capture_text: list[str] = []

    @property
    def visible_text(self) -> str:
        return " ".join(chunk.strip() for chunk in self.visible_text_chunks if chunk.strip())

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._tag_stack.append(tag)
        attr_map = {key.lower(): value or "" for key, value in attrs}

        if tag == "html":
            self.html_lang = attr_map.get("lang")
        if tag == "script":
            self.script_tag_count += 1
        if "id" in attr_map:
            self.section_ids.append(attr_map["id"])
        for key, value in attr_map.items():
            if key.startswith("on"):
                self.event_handler_attrs.append(key)
            if value.lower().strip().startswith("javascript:"):
                self.javascript_attrs.append(key)
        if tag in {"title", "h1", "h2", "h3", "p"}:
            self._capture_tag = tag
            self._capture_text = []

    def handle_data(self, data: str) -> None:
        if self._capture_tag is not None:
            self._capture_text.append(data)
        if not any(tag in {"head", "style", "script", "title"} for tag in self._tag_stack):
            self.visible_text_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._capture_tag == tag:
            text = " ".join(part.strip() for part in self._capture_text if part.strip())
            if tag == "title":
                self.titles.append(text)
            elif tag in {"h1", "h2", "h3"}:
                self.headings.append((int(tag[1]), text))
            elif tag == "p" and text:
                self.paragraphs.append(text)
            self._capture_tag = None
            self._capture_text = []
        if tag in self._tag_stack:
            index = len(self._tag_stack) - 1 - self._tag_stack[::-1].index(tag)
            del self._tag_stack[index:]


def collect_overlay_review_accessibility_errors(mode: str, html: str) -> list[str]:
    if mode not in MODES:
        return [f"{mode}: unsupported overlay review mode"]

    parser = ParsedOverlayHTML()
    parser.feed(html)
    errors: list[str] = []

    _check_common_structure(mode, html, parser, errors)
    _check_heading_flow(mode, parser, errors)
    _check_common_safety(mode, html, parser, errors)

    if mode == "compact":
        _check_compact(html, parser, errors)
    elif mode == "deep":
        _check_deep(html, parser, errors)
    else:
        _check_debug(html, errors)

    return errors


def check_overlay_review_accessibility(*, mode: str = "all") -> dict[str, Any]:
    modes = list(MODES) if mode == "all" else [mode]
    if any(selected_mode not in MODES for selected_mode in modes):
        raise OverlayReviewAccessibilityError(f"Unsupported overlay review mode: {mode}")

    results: dict[str, dict[str, Any]] = {}
    for selected_mode in modes:
        try:
            view_model = load_view_model_fixture(selected_mode)
            html = render_overlay_html(view_model)
            errors = collect_overlay_review_accessibility_errors(selected_mode, html)
            parser = ParsedOverlayHTML()
            parser.feed(html)
            metrics = _metrics(parser, html)
        except (OverlayReviewError, LocalOverlayPrototypeError, ValueError) as exc:
            errors = [str(exc)]
            metrics = {}
        results[selected_mode] = {
            "ok": not errors,
            "errors": errors,
            "metrics": metrics,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "ok": all(result["ok"] for result in results.values()),
        "fixture_based": True,
        "writes_files": False,
        "starts_server": False,
        "calls_provider": False,
        "modes": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run structural readability/accessibility guardrails on fixture-rendered overlay HTML. "
            "This is not a browser audit or WCAG certification."
        )
    )
    parser.add_argument(
        "--mode",
        choices=("all", *MODES),
        default="all",
        help="Which fixture-rendered overlay mode to check. Default: all.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short status line.")
    args = parser.parse_args()

    try:
        summary = check_overlay_review_accessibility(mode=args.mode)
    except OverlayReviewAccessibilityError as exc:
        parser.error(str(exc))

    if args.quiet:
        if summary["ok"]:
            print("Overlay review accessibility check passed.")
        else:
            print("Overlay review accessibility check failed.", file=sys.stderr)
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["ok"] else 1


def _check_common_structure(
    mode: str,
    html: str,
    parser: ParsedOverlayHTML,
    errors: list[str],
) -> None:
    if parser.html_lang != "uk":
        errors.append(f"{mode}: expected html lang='uk'")
    if not parser.titles or not any(title.strip() for title in parser.titles):
        errors.append(f"{mode}: missing nonempty title")
    h1s = [text for level, text in parser.headings if level == 1 and text.strip()]
    if len(h1s) != 1:
        errors.append(f"{mode}: expected exactly one nonempty h1")
    expected_section = SECTION_IDS[mode]
    if expected_section not in parser.section_ids:
        errors.append(f"{mode}: missing section id {expected_section!r}")
    if "<!doctype html>" not in html.lower():
        errors.append(f"{mode}: missing doctype")


def _check_heading_flow(mode: str, parser: ParsedOverlayHTML, errors: list[str]) -> None:
    headings = [(level, text) for level, text in parser.headings if text.strip()]
    if headings and headings[0][0] != 1:
        errors.append(f"{mode}: first heading must be h1")
    seen_h3 = False
    for level, text in headings:
        if level == 3:
            seen_h3 = True
        if level == 2 and seen_h3:
            errors.append(f"{mode}: h2 heading {text!r} appears after an h3")


def _check_common_safety(
    mode: str,
    html: str,
    parser: ParsedOverlayHTML,
    errors: list[str],
) -> None:
    lowered = html.lower()
    for marker in COMMON_FORBIDDEN_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"{mode}: contains forbidden marker {marker!r}")
    for marker in UNESCAPED_FORBIDDEN_MARKERS:
        if marker.lower() in lowered:
            errors.append(f"{mode}: contains unsafe HTML marker {marker!r}")
    if parser.script_tag_count:
        errors.append(f"{mode}: contains script tag")
    for attr in parser.event_handler_attrs:
        errors.append(f"{mode}: contains event handler attribute {attr!r}")
    for attr in parser.javascript_attrs:
        errors.append(f"{mode}: contains javascript URL attribute {attr!r}")


def _check_compact(html: str, parser: ParsedOverlayHTML, errors: list[str]) -> None:
    _require_markers("compact", html, COMPACT_REQUIRED_MARKERS, errors)
    _reject_markers("compact", html, PLAYER_MODE_FORBIDDEN_MARKERS, errors)
    _reject_markers(
        "compact",
        html,
        (
            "Debug / Developer Metadata",
            "Raw risk flags",
            "Raw Deep Notes",
            "Declarative Actions",
            "provider_debug",
            "provider-cache-v1.",
            "debug_only",
            "switch_debug",
        ),
        errors,
    )
    if len(parser.paragraphs) > COMPACT_MAX_PARAGRAPHS:
        errors.append(
            f"compact: paragraph count {len(parser.paragraphs)} exceeds {COMPACT_MAX_PARAGRAPHS}"
        )
    if len(parser.visible_text) > COMPACT_MAX_VISIBLE_TEXT_LENGTH:
        errors.append(
            "compact: visible text length "
            f"{len(parser.visible_text)} exceeds {COMPACT_MAX_VISIBLE_TEXT_LENGTH}"
        )


def _check_deep(html: str, parser: ParsedOverlayHTML, errors: list[str]) -> None:
    _require_markers("deep", html, DEEP_REQUIRED_MARKERS, errors)
    _reject_markers("deep", html, PLAYER_MODE_FORBIDDEN_MARKERS, errors)
    _reject_markers(
        "deep",
        html,
        (
            "Prompt-pack policy keeps",
            "Debug / Developer Metadata",
            "Raw risk flags",
            "Raw Deep Notes",
            "Declarative Actions",
            "provider_debug",
            "provider-cache-v1.",
            "debug_only",
            "switch_debug",
        ),
        errors,
    )
    heading_texts = [text for _level, text in parser.headings]
    position = -1
    for heading in DEEP_REQUIRED_HEADINGS:
        try:
            next_position = heading_texts.index(heading, position + 1)
        except ValueError:
            errors.append(f"deep: missing grouped heading {heading!r}")
            continue
        position = next_position


def _check_debug(html: str, errors: list[str]) -> None:
    _require_markers("debug", html, DEBUG_REQUIRED_MARKERS, errors)
    _reject_markers("debug", html, DEBUG_FORBIDDEN_MARKERS, errors)


def _require_markers(
    mode: str,
    html: str,
    markers: tuple[str, ...],
    errors: list[str],
) -> None:
    for marker in markers:
        if marker not in html:
            errors.append(f"{mode}: missing expected marker {marker!r}")


def _reject_markers(
    mode: str,
    html: str,
    markers: tuple[str, ...],
    errors: list[str],
) -> None:
    lowered = html.lower()
    for marker in markers:
        if marker.lower() in lowered:
            errors.append(f"{mode}: contains forbidden marker {marker!r}")


def _metrics(parser: ParsedOverlayHTML, html: str) -> dict[str, Any]:
    return {
        "html_length": len(html),
        "visible_text_length": len(parser.visible_text),
        "paragraph_count": len(parser.paragraphs),
        "heading_count": len(parser.headings),
        "section_ids": list(parser.section_ids),
    }


if __name__ == "__main__":
    raise SystemExit(main())
