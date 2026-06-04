from __future__ import annotations

import copy
from pathlib import Path
import unittest

from scripts.run_m4_overlay_shell import (
    DEFAULT_COMPACT_SOURCE,
    M4OverlayShellError,
    build_compact_overlay_shell_html,
    build_redacted_summary,
    ensure_safe_output_path,
    load_compact_view_model,
    main,
    run_self_test,
    write_html,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M4OverlayShellTests(unittest.TestCase):
    def test_compact_fixture_renders_shell_without_source_text(self) -> None:
        view_model = load_compact_view_model(DEFAULT_COMPACT_SOURCE)
        html = build_compact_overlay_shell_html(view_model)

        self.assertIn("m4-compact-overlay", html)
        self.assertIn("m4-overlay-shell.v1", html)
        self.assertIn(view_model["compact"]["concise_meaning_uk"], html)
        self.assertNotIn(view_model["compact"]["original_english"], html)
        self.assertNotIn(view_model["source"]["line_id"], html)

    def test_rejects_non_compact_source(self) -> None:
        deep_path = ROOT / "tests/fixtures/overlay_prototype.deep.viewmodel.synthetic.json"

        with self.assertRaises(Exception):
            load_compact_view_model(deep_path)

    def test_rejects_debug_or_provider_markers_in_player_fields(self) -> None:
        view_model = load_json(DEFAULT_COMPACT_SOURCE)
        mutated = copy.deepcopy(view_model)
        mutated["compact"]["concise_meaning_uk"] = "raw_provider_request"

        with self.assertRaises(Exception):
            build_compact_overlay_shell_html(mutated)

    def test_output_path_bounds(self) -> None:
        safe = ensure_safe_output_path(Path("workspace/local-private/overlay/compact.html"))

        self.assertTrue(str(safe).endswith("workspace\\local-private\\overlay\\compact.html"))
        with self.assertRaises(M4OverlayShellError):
            ensure_safe_output_path(Path("workspace/synthetic-slice/overlay/compact.html"))
        with self.assertRaises(M4OverlayShellError):
            ensure_safe_output_path(Path("workspace/local-private/overlay/compact.txt"))

    def test_write_html_allowed_under_private_root(self) -> None:
        view_model = load_compact_view_model(DEFAULT_COMPACT_SOURCE)
        html = build_compact_overlay_shell_html(view_model)
        output = ROOT / "workspace/local-private/overlay/test-compact.html"
        try:
            written = write_html(html, output)
            self.assertTrue(written.exists())
            self.assertIn("m4-compact-overlay", written.read_text(encoding="utf-8"))
        finally:
            output.unlink(missing_ok=True)

    def test_redacted_summary_contains_no_paths_or_text(self) -> None:
        view_model = load_compact_view_model(DEFAULT_COMPACT_SOURCE)
        summary = build_redacted_summary(view_model, output_path=None)

        self.assertEqual("m4-compact-overlay-shell-summary.v1", summary["schema_version"])
        self.assertTrue(summary["compact_translation_rendered"])
        self.assertFalse(summary["original_text_included"])
        self.assertFalse(summary["private_paths_included"])
        self.assertNotIn("output_path", summary)
        self.assertNotIn(view_model["compact"]["concise_meaning_uk"], str(summary))

    def test_self_test_and_quiet_cli(self) -> None:
        summary = run_self_test()

        self.assertEqual("ready", summary["render_status"])
        self.assertEqual(0, main(["--self-test", "--quiet"]))

    def test_cli_rejects_unsafe_output(self) -> None:
        with self.assertRaises(SystemExit):
            main(["--output", "workspace/synthetic-slice/overlay/compact.html"])

    def test_check_all_registers_shell_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_m4_overlay_shell.py", text)
        self.assertIn("--self-test", text)


if __name__ == "__main__":
    unittest.main()
