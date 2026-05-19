from __future__ import annotations

import subprocess
import sys
import unittest

from scripts import check_overlay_review_accessibility as accessibility
from scripts.local_overlay_prototype import render_overlay_html
from scripts.render_overlay_review import load_view_model_fixture
from scripts.synthetic_slice import ROOT


class OverlayReviewAccessibilityTests(unittest.TestCase):
    def test_checker_passes_all_fixture_rendered_modes(self) -> None:
        summary = accessibility.check_overlay_review_accessibility()

        self.assertTrue(summary["ok"])
        self.assertTrue(summary["fixture_based"])
        self.assertFalse(summary["writes_files"])
        self.assertFalse(summary["starts_server"])
        self.assertFalse(summary["calls_provider"])
        self.assertEqual({"compact", "deep", "debug"}, set(summary["modes"]))

    def test_compact_html_passes_readability_checks(self) -> None:
        errors = accessibility.collect_overlay_review_accessibility_errors(
            "compact",
            _html("compact"),
        )

        self.assertEqual([], errors)

    def test_deep_html_passes_structure_checks(self) -> None:
        errors = accessibility.collect_overlay_review_accessibility_errors("deep", _html("deep"))

        self.assertEqual([], errors)

    def test_debug_html_passes_redaction_checks(self) -> None:
        errors = accessibility.collect_overlay_review_accessibility_errors(
            "debug",
            _html("debug"),
        )

        self.assertEqual([], errors)

    def test_missing_lang_fails(self) -> None:
        html = _html("compact").replace('<html lang="uk">', "<html>", 1)

        errors = accessibility.collect_overlay_review_accessibility_errors("compact", html)

        self.assertTrue(_contains(errors, "lang='uk'"))

    def test_missing_title_fails(self) -> None:
        html = _html("compact").replace(
            "  <title>Revachol Local Overlay Prototype</title>",
            "",
            1,
        )

        errors = accessibility.collect_overlay_review_accessibility_errors("compact", html)

        self.assertTrue(_contains(errors, "title"))

    def test_missing_h1_fails(self) -> None:
        html = _html("compact").replace("    <h1>Локальний прототип оверлею</h1>", "", 1)

        errors = accessibility.collect_overlay_review_accessibility_errors("compact", html)

        self.assertTrue(_contains(errors, "h1"))

    def test_heading_disorder_fails(self) -> None:
        html = _html("deep").replace("<h2>Оригінал</h2>", "<h3>Оригінал</h3>", 1)

        errors = accessibility.collect_overlay_review_accessibility_errors("deep", html)

        self.assertTrue(_contains(errors, "appears after an h3"))

    def test_compact_with_raw_flag_fails(self) -> None:
        html = _html("compact").replace("</section>", "<p>synthetic_fixture</p></section>", 1)

        errors = accessibility.collect_overlay_review_accessibility_errors("compact", html)

        self.assertTrue(_contains(errors, "synthetic_fixture"))

    def test_compact_with_excessive_debug_text_fails(self) -> None:
        html = _html("compact").replace(
            "</section>",
            f"<p>{'debug detail ' * 120}</p></section>",
            1,
        )

        errors = accessibility.collect_overlay_review_accessibility_errors("compact", html)

        self.assertTrue(_contains(errors, "visible text length"))

    def test_context_packet_game_title_fails(self) -> None:
        html = _html("deep").replace(
            "</section>",
            "<p>Disco Elysium: The Final Cut</p></section>",
            1,
        )

        errors = accessibility.collect_overlay_review_accessibility_errors("deep", html)

        self.assertTrue(_contains(errors, "Disco Elysium: The Final Cut"))

    def test_escaped_unsafe_html_is_allowed(self) -> None:
        html = _html("compact").replace(
            "</section>",
            "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;</section>",
            1,
        )

        errors = accessibility.collect_overlay_review_accessibility_errors("compact", html)

        self.assertEqual([], errors)

    def test_unescaped_script_tag_fails(self) -> None:
        html = _html("debug").replace("</section>", "<script>alert('x')</script></section>", 1)

        errors = accessibility.collect_overlay_review_accessibility_errors("debug", html)

        self.assertTrue(_contains(errors, "script"))

    def test_event_handler_attribute_fails(self) -> None:
        html = _html("compact").replace(
            '<section class="overlay" id="compact-mode">',
            '<section class="overlay" id="compact-mode" onclick="alert(1)">',
            1,
        )

        errors = accessibility.collect_overlay_review_accessibility_errors("compact", html)

        self.assertTrue(_contains(errors, "event handler"))

    def test_cli_quiet_passes(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/check_overlay_review_accessibility.py",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Overlay review accessibility check passed", completed.stdout)


def _html(mode: str) -> str:
    return render_overlay_html(load_view_model_fixture(mode))


def _contains(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)


if __name__ == "__main__":
    unittest.main()
