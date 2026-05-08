from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import threading
import unittest

from scripts.companion_client import CompanionClient
from scripts.companion_server import DEFAULT_HOST, make_server
from scripts.local_overlay_prototype import build_overlay_view_model, render_overlay_html
from scripts.provider_pipeline import run_provider_pipeline
from scripts.run_local_overlay_prototype import DEFAULT_OUTPUT_ROOT, ROOT, resolve_output_path
from scripts.schema_validator import load_json
from scripts.synthetic_slice import build_context_packet


VALID_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"


class LocalOverlayPrototypeTests(unittest.TestCase):
    def test_view_model_builds_from_provider_annotation_response(self) -> None:
        context_packet, annotation_card = _provider_context_and_annotation()

        view_model = build_overlay_view_model(context_packet, annotation_card, mode="compact")

        self.assertEqual("local-overlay-prototype.v1", view_model["schema_version"])
        self.assertEqual("compact", view_model["mode"])
        self.assertEqual(
            context_packet["current_line"]["source_text"],
            view_model["source"]["original_english"],
        )
        self.assertEqual(
            annotation_card["concise_meaning_uk"],
            view_model["compact"]["concise_meaning_uk"],
        )
        self.assertEqual(
            annotation_card["literary_rendering_uk"],
            view_model["deep"]["literary_rendering_uk"],
        )
        self.assertEqual("mock", view_model["debug"]["provider_debug"]["provider_name"])

    def test_compact_mode_contains_original_concise_confidence_and_risks(self) -> None:
        context_packet, annotation_card = _provider_context_and_annotation()
        view_model = build_overlay_view_model(context_packet, annotation_card, mode="compact")

        html = render_overlay_html(view_model)

        self.assertIn("compact-mode", html)
        self.assertIn(context_packet["current_line"]["source_text"], html)
        self.assertIn(annotation_card["concise_meaning_uk"], html)
        self.assertIn("Confidence", html)
        self.assertIn("prompt_pack_guided", html)
        self.assertIn("Deep notes available", html)

    def test_deep_mode_contains_literary_rendering_annotations_and_glossary(self) -> None:
        _context_packet, annotation_card = _provider_context_and_annotation()
        view_model = build_overlay_view_model(
            *_provider_context_and_annotation(),
            mode="deep",
        )

        html = render_overlay_html(view_model)

        self.assertIn("deep-mode", html)
        self.assertIn(annotation_card["literary_rendering_uk"], html)
        self.assertIn(annotation_card["explanation_uk"], html)
        self.assertIn("Idiom / Reference / Subtext Notes", html)
        self.assertIn("Tone / Character Voice", html)
        self.assertIn("committee", html)
        self.assertIn("infrastructure", html)

    def test_debug_mode_contains_safe_metadata_without_prompt_or_private_paths(self) -> None:
        context_packet, annotation_card = _provider_context_and_annotation()
        view_model = build_overlay_view_model(context_packet, annotation_card, mode="debug")

        html = render_overlay_html(view_model)

        self.assertIn("debug-mode", html)
        self.assertIn("mock", html)
        self.assertIn("ukrainian_annotation_v1", html)
        self.assertIn("provider-cache-v1.", html)
        self.assertIn("workspace/provider-cache", html)
        self.assertIn("Writes raw payload", html)
        self.assertIn("False", html)
        self.assertNotIn("prompt_pack_sections", html)
        self.assertNotIn("raw_provider_request", html)
        self.assertNotIn("C:\\", html)
        self.assertNotIn("D:\\", html)
        self.assertNotIn("api_key", html.lower())

    def test_debug_mode_does_not_render_schema_required_game_title(self) -> None:
        context_packet, annotation_card = _provider_context_and_annotation()
        view_model = build_overlay_view_model(context_packet, annotation_card, mode="debug")

        html = render_overlay_html(view_model)

        self.assertNotIn(context_packet["game"]["title"], html)

    def test_renderer_escapes_unsafe_text(self) -> None:
        context_packet, annotation_card = _provider_context_and_annotation()
        unsafe = '<script>alert("x")</script>'
        context_packet["current_line"]["source_text"] = unsafe
        annotation_card["concise_meaning_uk"] = unsafe
        annotation_card["literary_rendering_uk"] = unsafe
        annotation_card["explanation_uk"] = unsafe
        annotation_card["deep_notes"][0]["text"] = unsafe
        annotation_card["provider_debug"]["provider_name"] = unsafe

        compact_html = render_overlay_html(
            build_overlay_view_model(context_packet, annotation_card, mode="compact")
        )
        deep_html = render_overlay_html(
            build_overlay_view_model(context_packet, annotation_card, mode="deep")
        )
        debug_html = render_overlay_html(
            build_overlay_view_model(context_packet, annotation_card, mode="debug")
        )

        escaped = "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"
        for html in (compact_html, deep_html, debug_html):
            with self.subTest(html=html[:20]):
                self.assertNotIn(unsafe, html)
                self.assertIn(escaped, html)

    def test_output_path_allows_overlay_workspace(self) -> None:
        output = resolve_output_path(
            Path("workspace/synthetic-slice/overlay-prototype/overlay-test.html")
        )

        self.assertTrue(_is_relative_to(output, DEFAULT_OUTPUT_ROOT))

    def test_output_path_rejects_public_repo_path(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_path(Path("docs/overlay.html"))

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_local_overlay_prototype.py",
                "--self-test",
                "--output",
                "docs/overlay.html",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)

    def test_cli_self_test_starts_and_stops_local_server(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_local_overlay_prototype.py",
                "--self-test",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Local overlay prototype self-test passed", completed.stdout)

    def test_cli_reads_latest_provider_state_from_existing_server(self) -> None:
        server = make_server(DEFAULT_HOST, 0)
        host, port = server.server_address[:2]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = CompanionClient(f"http://{host}:{port}")
            client.provider_annotate_fake_event(load_json(VALID_EVENT))

            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_local_overlay_prototype.py",
                    "--server-url",
                    f"http://{host}:{port}",
                    "--mode",
                    "compact",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Local Overlay Prototype", completed.stdout)
        self.assertIn("Ukrainian concise meaning", completed.stdout)

    def test_cli_writes_html_and_json_only_under_workspace(self) -> None:
        html_output = DEFAULT_OUTPUT_ROOT / "overlay-test.html"
        json_output = DEFAULT_OUTPUT_ROOT / "overlay-test.json"
        for path in (html_output, json_output):
            if path.exists():
                path.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_local_overlay_prototype.py",
                "--self-test",
                "--mode",
                "debug",
                "--output",
                "workspace/synthetic-slice/overlay-prototype/overlay-test.html",
                "--json-output",
                "workspace/synthetic-slice/overlay-prototype/overlay-test.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        try:
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(html_output.exists())
            self.assertTrue(json_output.exists())
            payload = json.loads(json_output.read_text(encoding="utf-8"))
            self.assertEqual("debug", payload["mode"])
            self.assertIn("provider-cache-v1.", html_output.read_text(encoding="utf-8"))
            self.assertTrue(_is_relative_to(html_output, DEFAULT_OUTPUT_ROOT))
            self.assertTrue(_is_relative_to(json_output, DEFAULT_OUTPUT_ROOT))
        finally:
            for path in (html_output, json_output):
                if path.exists():
                    path.unlink()


def _provider_context_and_annotation() -> tuple[dict[str, object], dict[str, object]]:
    context_packet = build_context_packet(load_json(VALID_EVENT))
    annotation_card = run_provider_pipeline(context_packet)
    return context_packet, annotation_card


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
