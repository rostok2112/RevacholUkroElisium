from __future__ import annotations

import shutil
import subprocess
import sys
import unittest

from scripts import render_overlay_review
from scripts.local_overlay_prototype import render_overlay_html
from scripts.schema_validator import load_json
from scripts.synthetic_slice import ROOT


TEST_OUTPUT_ROOT = render_overlay_review.DEFAULT_OUTPUT_ROOT / "test-overlay-review-renderer"
RAW_PLAYER_FLAGS = (
    "synthetic_fixture",
    "mock_provider",
    "deterministic_mock_provider",
    "prompt_pack_guided",
)
FORBIDDEN_DEBUG_MARKERS = (
    "prompt_pack_sections",
    "raw_provider_request",
    "api_key",
    "access_token",
    "bearer ",
    "sk-",
    "C:\\",
    "D:\\",
    "/Users/",
    "/home/",
    "openai_compatible",
    "deepl_glossary",
    "local_model",
    "ensemble_reviewer",
)


class OverlayReviewRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        _remove_test_output()

    def tearDown(self) -> None:
        _remove_test_output()

    def test_review_renderer_writes_fixture_based_html_and_index(self) -> None:
        summary = render_overlay_review.render_overlay_review(output_root=TEST_OUTPUT_ROOT)

        self.assertTrue(summary["ok"])
        self.assertTrue(summary["fixture_based"])
        self.assertFalse(summary["calls_companion_server"])
        self.assertFalse(summary["calls_provider"])
        for filename in ("compact.html", "deep.html", "debug.html", "index.html"):
            with self.subTest(filename=filename):
                self.assertTrue((TEST_OUTPUT_ROOT / filename).exists())

    def test_compact_and_deep_html_hide_raw_flags_and_show_player_ukrainian(self) -> None:
        render_overlay_review.render_overlay_review(output_root=TEST_OUTPUT_ROOT)

        compact_html = (TEST_OUTPUT_ROOT / "compact.html").read_text(encoding="utf-8")
        deep_html = (TEST_OUTPUT_ROOT / "deep.html").read_text(encoding="utf-8")

        self.assertIn("Коротко українською", compact_html)
        self.assertIn("Є глибше пояснення", compact_html)
        self.assertIn("Впевненість", compact_html)
        self.assertIn("Дії", compact_html)
        self.assertIn("Глибше пояснення", compact_html)
        self.assertIn("Скопіювати український зміст", compact_html)
        for heading in (
            "Оригінал",
            "Літературний український варіант",
            "Що тут відбувається",
            "Підтекст / іронія / референс",
            "Тон / голос",
            "Глосарій",
            "Ризики / невпевненість",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, deep_html)
        self.assertIn("Дії", deep_html)
        self.assertIn("Наступна нотатка", deep_html)
        self.assertIn("Скопіювати пояснення", deep_html)
        self.assertNotIn("Prompt-pack policy keeps", deep_html)
        self.assertNotIn("switch_debug", compact_html)
        self.assertNotIn("switch_debug", deep_html)
        self.assertNotIn("debug_only", compact_html)
        self.assertNotIn("debug_only", deep_html)
        for raw_flag in RAW_PLAYER_FLAGS:
            with self.subTest(raw_flag=raw_flag):
                self.assertNotIn(raw_flag, compact_html)
                self.assertNotIn(raw_flag, deep_html)

    def test_debug_html_contains_metadata_safely(self) -> None:
        render_overlay_review.render_overlay_review(output_root=TEST_OUTPUT_ROOT)

        debug_html = (TEST_OUTPUT_ROOT / "debug.html").read_text(encoding="utf-8")

        self.assertIn("Raw risk flags", debug_html)
        self.assertIn("synthetic_fixture", debug_html)
        self.assertIn("mock_provider", debug_html)
        self.assertIn("prompt_pack_guided", debug_html)
        self.assertIn("ukrainian_annotation_v1", debug_html)
        self.assertIn("provider-cache-v1.", debug_html)
        self.assertIn("Writes raw payload", debug_html)
        self.assertIn("Declarative Actions", debug_html)
        self.assertIn("switch_debug", debug_html)
        self.assertIn("debug_only=True", debug_html)
        self.assertNotIn("Disco Elysium: The Final Cut", debug_html)
        for marker in FORBIDDEN_DEBUG_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker.lower(), debug_html.lower())

    def test_mode_specific_render_writes_selected_mode_and_index(self) -> None:
        summary = render_overlay_review.render_overlay_review(
            output_root=TEST_OUTPUT_ROOT,
            mode="compact",
        )

        self.assertIn("compact", summary["written"])
        self.assertIn("index", summary["written"])
        self.assertTrue((TEST_OUTPUT_ROOT / "compact.html").exists())
        self.assertTrue((TEST_OUTPUT_ROOT / "index.html").exists())
        self.assertFalse((TEST_OUTPUT_ROOT / "deep.html").exists())
        self.assertFalse((TEST_OUTPUT_ROOT / "debug.html").exists())

    def test_rejects_unsafe_output_root(self) -> None:
        with self.assertRaises(render_overlay_review.OverlayReviewError):
            render_overlay_review.resolve_output_root(ROOT / "docs/overlay-review")

    def test_cli_rejects_unsafe_output_root(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/render_overlay_review.py",
                "--output-root",
                "docs/overlay-review",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output root", completed.stderr)

    def test_cli_quiet_writes_workspace_review(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/render_overlay_review.py",
                "--output-root",
                "workspace/synthetic-slice/overlay-prototype/review/test-overlay-review-renderer",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Overlay review HTML rendered", completed.stdout)
        self.assertTrue((TEST_OUTPUT_ROOT / "compact.html").exists())
        self.assertTrue((TEST_OUTPUT_ROOT / "deep.html").exists())
        self.assertTrue((TEST_OUTPUT_ROOT / "debug.html").exists())
        self.assertTrue((TEST_OUTPUT_ROOT / "index.html").exists())

    def test_no_generated_html_is_added_to_test_fixtures(self) -> None:
        render_overlay_review.render_overlay_review(output_root=TEST_OUTPUT_ROOT)

        html_fixtures = list((ROOT / "tests/fixtures").rglob("*.html"))

        self.assertEqual([], html_fixtures)

    def test_rendering_escapes_unsafe_fixture_payloads(self) -> None:
        compact = load_json(
            ROOT / "tests/fixtures/overlay_prototype.compact.viewmodel.synthetic.json"
        )
        unsafe = '<script>alert("x")</script>'
        compact["source"]["original_english"] = unsafe
        compact["compact"]["concise_meaning_uk"] = unsafe

        html = render_overlay_html(compact)

        self.assertNotIn(unsafe, html)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", html)
        render_overlay_review.validate_review_html("compact", html)

    def test_review_html_excludes_context_packet_game_title_in_all_modes(self) -> None:
        render_overlay_review.render_overlay_review(output_root=TEST_OUTPUT_ROOT)

        for filename in ("compact.html", "deep.html", "debug.html", "index.html"):
            with self.subTest(filename=filename):
                html = (TEST_OUTPUT_ROOT / filename).read_text(encoding="utf-8")
                self.assertNotIn("Disco Elysium: The Final Cut", html)


def _remove_test_output() -> None:
    if TEST_OUTPUT_ROOT.exists():
        shutil.rmtree(TEST_OUTPUT_ROOT)


if __name__ == "__main__":
    unittest.main()
