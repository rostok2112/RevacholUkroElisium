from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts import check_overlay_viewmodel_fixtures as fixture_check
from scripts.local_overlay_prototype import render_overlay_html


FIXTURE_PATHS = fixture_check.FIXTURE_PATHS
RAW_FLAGS = (
    "synthetic_fixture",
    "mock_provider",
    "deterministic_mock_provider",
    "prompt_pack_guided",
)
FORBIDDEN_MARKERS = (
    "Disco Elysium: The Final Cut",
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
    "<!doctype html>",
    "<html",
    "openai_compatible",
    "deepl_glossary",
    "local_model",
    "ensemble_reviewer",
)


class OverlayViewModelFixtureTests(unittest.TestCase):
    def test_fixture_regression_passes_with_current_fixtures(self) -> None:
        summary = fixture_check.check_overlay_viewmodel_fixtures()

        self.assertTrue(summary["ok"])
        self.assertIn("compact", summary["fixtures"])
        self.assertIn("debug", summary["fixtures"])

    def test_compact_fixture_hides_raw_flags_and_uses_player_ukrainian(self) -> None:
        compact = _load_fixture("compact")
        rendered = _canonical(compact)

        self.assertEqual({"schema_version", "mode", "source", "compact"}, set(compact))
        self.assertEqual("compact", compact["mode"])
        self.assertEqual("Коротко українською", compact["compact"]["labels_uk"]["concise_meaning"])
        self.assertEqual("Є глибше пояснення", compact["compact"]["deep_notes_label_uk"])
        self.assertIn("Впевненість", compact["compact"]["confidence_summary_uk"])
        self.assertIn("людська перевірка", compact["compact"]["risk_summary_uk"])
        self.assertFalse(compact["compact"]["visibility"]["debug_visible"])
        self.assertEqual("compact", compact["compact"]["visibility"]["current_mode"])
        self.assertIn(
            "copy_ukrainian_summary",
            [action["id"] for action in compact["compact"]["actions"]],
        )
        self.assertNotIn("switch_debug", [action["id"] for action in compact["compact"]["actions"]])
        for flag in RAW_FLAGS:
            with self.subTest(flag=flag):
                self.assertNotIn(flag, rendered)

    def test_deep_fixture_has_ukrainian_structure_and_no_provider_policy_note(self) -> None:
        deep = _load_fixture("deep")
        rendered = _canonical(deep)

        self.assertEqual({"schema_version", "mode", "source", "deep"}, set(deep))
        self.assertEqual("deep", deep["mode"])
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
                self.assertIn(heading, deep["deep"]["section_order_uk"])
        self.assertNotIn("Prompt-pack policy keeps", rendered)
        self.assertTrue(deep["deep"]["visibility"]["annotations_visible"])
        self.assertFalse(deep["deep"]["visibility"]["debug_visible"])
        self.assertIn("next_annotation", [action["id"] for action in deep["deep"]["actions"]])
        self.assertNotIn("switch_debug", [action["id"] for action in deep["deep"]["actions"]])
        for flag in RAW_FLAGS:
            with self.subTest(flag=flag):
                self.assertNotIn(flag, rendered)

    def test_debug_fixture_contains_raw_metadata_safely(self) -> None:
        debug = _load_fixture("debug")
        rendered = _canonical(debug)

        self.assertEqual({"schema_version", "mode", "source", "debug"}, set(debug))
        self.assertEqual("debug", debug["mode"])
        self.assertIn("synthetic_fixture", rendered)
        self.assertIn("mock_provider", rendered)
        self.assertIn("prompt_pack_guided", rendered)
        self.assertEqual("mock", debug["debug"]["provider"]["provider_name"])
        self.assertEqual("ukrainian_annotation_v1", debug["debug"]["prompt_pack"]["pack_id"])
        self.assertIn("provider-cache-v1.", debug["debug"]["privacy"]["cache_key"])
        self.assertFalse(debug["debug"]["privacy"]["cache_write_plan"]["would_write"])
        self.assertFalse(debug["debug"]["privacy"]["cache_write_plan"]["writes_raw_payload"])
        self.assertTrue(debug["debug"]["visibility"]["debug_visible"])
        self.assertIn("switch_debug", [action["id"] for action in debug["debug"]["actions"]])
        self.assertTrue(
            next(action for action in debug["debug"]["actions"] if action["id"] == "switch_debug")[
                "debug_only"
            ]
        )

    def test_fixtures_exclude_forbidden_markers(self) -> None:
        for mode in ("compact", "deep", "debug"):
            rendered = _canonical(_load_fixture(mode))
            with self.subTest(mode=mode):
                for marker in FORBIDDEN_MARKERS:
                    self.assertNotIn(marker.lower(), rendered.lower())

    def test_renderer_escapes_fixture_payloads(self) -> None:
        compact = _load_fixture("compact")
        unsafe = '<script>alert("x")</script>'
        compact["source"]["original_english"] = unsafe
        compact["compact"]["concise_meaning_uk"] = unsafe

        html = render_overlay_html(compact)

        self.assertNotIn(unsafe, html)
        self.assertIn("&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", html)

    def test_drift_detection_catches_tampered_fixture(self) -> None:
        current = fixture_check.build_current_view_models()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_paths = {
                mode: temp_root / f"overlay_prototype.{mode}.viewmodel.synthetic.json"
                for mode in ("compact", "deep", "debug")
            }
            for mode, path in temp_paths.items():
                path.write_text(
                    fixture_check.canonical_json(current[mode]) + "\n", encoding="utf-8"
                )
            tampered = deepcopy(current["compact"])
            tampered["compact"]["deep_notes_label_uk"] = "tampered"
            temp_paths["compact"].write_text(
                fixture_check.canonical_json(tampered) + "\n",
                encoding="utf-8",
            )

            original_paths = fixture_check.FIXTURE_PATHS
            fixture_check.FIXTURE_PATHS = temp_paths
            try:
                with self.assertRaises(fixture_check.OverlayFixtureError) as raised:
                    fixture_check.check_overlay_viewmodel_fixtures()
            finally:
                fixture_check.FIXTURE_PATHS = original_paths

        self.assertIn("compact fixture drift", str(raised.exception))


def _load_fixture(mode: str) -> dict[str, object]:
    path = FIXTURE_PATHS[mode]
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    unittest.main()
