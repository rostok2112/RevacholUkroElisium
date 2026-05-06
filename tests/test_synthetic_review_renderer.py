from pathlib import Path
import subprocess
import sys
import unittest

from scripts.provider_pipeline import run_provider_pipeline
from scripts.run_synthetic_slice import ROOT, _resolve_output
from scripts.schema_validator import load_json
from scripts.synthetic_review_renderer import render_review_html
from scripts.synthetic_slice import (
    build_context_packet,
    build_overlay_demo_model,
    run_synthetic_slice,
)


VALID_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"


class SyntheticReviewRendererTests(unittest.TestCase):
    def test_review_html_includes_compact_mode_fields(self) -> None:
        html = render_review_html(run_synthetic_slice(load_json(VALID_EVENT)))

        self.assertIn("Compact Mode", html)
        self.assertIn("Compact Ukrainian meaning", html)
        self.assertIn("Literary Ukrainian rendering", html)
        self.assertIn("Annotation available", html)

    def test_review_html_includes_deep_explanation_fields(self) -> None:
        html = render_review_html(run_synthetic_slice(load_json(VALID_EVENT)))

        self.assertIn("Deep Explanation Mode", html)
        self.assertIn("Deep explanation", html)
        self.assertIn("Idiom / Reference / Voice Notes", html)
        self.assertIn("Character voice note", html)
        self.assertIn("Idiom/Subtext", html)
        self.assertIn("Reference", html)
        self.assertIn("Character Voice", html)

    def test_review_html_includes_original_ukrainian_glossary_and_risk_fields(self) -> None:
        result = run_synthetic_slice(load_json(VALID_EVENT))
        html = render_review_html(result)

        self.assertIn(result["context_packet"]["current_line"]["source_text"], html)
        self.assertIn(result["annotation_card"]["concise_meaning_uk"], html)
        self.assertIn(result["annotation_card"]["literary_rendering_uk"], html)
        self.assertIn("committee", html)
        self.assertIn("infrastructure", html)
        self.assertIn("pipe", html)
        self.assertIn("0.78", html)
        self.assertIn("deterministic_mock_pipeline", html)
        self.assertIn("Original visible", html)
        self.assertIn("Translation visible", html)

    def test_review_html_escapes_unsafe_text(self) -> None:
        result = run_synthetic_slice(load_json(VALID_EVENT))
        unsafe = '<script>alert("x")</script>'
        result["overlay_demo"]["source"]["original_english"] = unsafe
        result["overlay_demo"]["modes"]["deep_explanation"]["sections"][0]["text"] = unsafe
        result["annotation_card"]["quality"][unsafe] = unsafe
        result["overlay_demo"]["debug"]["provider_debug"] = {"provider_name": unsafe}

        html = render_review_html(result)

        self.assertNotIn(unsafe, html)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", html)

    def test_review_html_includes_provider_and_prompt_pack_debug_metadata(self) -> None:
        result = _provider_slice_result()

        html = render_review_html(result)

        self.assertIn("Provider", html)
        self.assertIn("mock", html)
        self.assertIn("Provider role", html)
        self.assertIn("deterministic_mock", html)
        self.assertIn("Prompt pack", html)
        self.assertIn("ukrainian_annotation_v1", html)
        self.assertIn("Prompt pack version", html)
        self.assertIn("1.0.0", html)
        self.assertIn("Player-facing language default", html)
        self.assertIn("uk", html)
        self.assertIn("spoiler_policy", html)
        self.assertIn("anti_overlocalization_policy", html)
        self.assertIn("russianism_avoidance", html)

    def test_output_path_allows_workspace_synthetic_slice(self) -> None:
        output = _resolve_output(Path("workspace/synthetic-slice/test-review.html"))

        self.assertTrue(_is_relative_to(output, ROOT / "workspace/synthetic-slice"))

    def test_output_path_rejects_public_repo_path(self) -> None:
        with self.assertRaises(ValueError):
            _resolve_output(Path("docs/review.html"))

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_synthetic_slice.py",
                "--render-review",
                "--output",
                "docs/review.html",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)

    def test_cli_writes_review_only_under_workspace(self) -> None:
        output = ROOT / "workspace/synthetic-slice/test-review.html"
        if output.exists():
            output.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_synthetic_slice.py",
                "--render-review",
                "--output",
                "workspace/synthetic-slice/test-review.html",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(output.exists())
        self.assertTrue(
            _is_relative_to(output.resolve(strict=False), ROOT / "workspace/synthetic-slice")
        )
        output.unlink()


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


def _provider_slice_result() -> dict[str, object]:
    event = load_json(VALID_EVENT)
    context_packet = build_context_packet(event)
    annotation_card = run_provider_pipeline(context_packet)
    overlay_demo = build_overlay_demo_model(context_packet, annotation_card)
    return {
        "fake_game_event": event,
        "context_packet": context_packet,
        "annotation_card": annotation_card,
        "overlay_demo": overlay_demo,
    }


if __name__ == "__main__":
    unittest.main()
