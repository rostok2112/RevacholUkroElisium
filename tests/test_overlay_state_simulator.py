from __future__ import annotations

from copy import deepcopy
import json
import subprocess
import sys
import unittest

from scripts import run_overlay_state_simulator
from scripts.overlay_state_simulator import (
    OverlayStateSimulatorError,
    assert_valid_overlay_transition,
    collect_overlay_transition_errors,
    simulate_overlay_action,
)
from scripts.render_overlay_review import load_view_model_fixture
from scripts.synthetic_slice import ROOT


class OverlayStateSimulatorTests(unittest.TestCase):
    def test_switch_deep_from_compact_previews_deep_visibility(self) -> None:
        preview = simulate_overlay_action(_fixture("compact"), "switch_deep")

        self.assertTrue(preview["allowed"])
        self.assertEqual("compact", preview["from_mode"])
        self.assertEqual("deep", preview["next_mode"])
        self.assertTrue(preview["next_visibility"]["annotations_visible"])
        self.assertFalse(preview["next_visibility"]["debug_visible"])
        self.assertEqual("none", preview["side_effect_type"])
        self.assertIn("глибше", preview["summary_uk"])

    def test_switch_compact_from_deep_previews_compact_visibility(self) -> None:
        preview = simulate_overlay_action(_fixture("deep"), "switch_compact")

        self.assertTrue(preview["allowed"])
        self.assertEqual("compact", preview["next_mode"])
        self.assertFalse(preview["next_visibility"]["annotations_visible"])
        self.assertFalse(preview["next_visibility"]["debug_visible"])

    def test_switch_debug_blocked_from_player_modes_and_allowed_in_debug(self) -> None:
        for mode in ("compact", "deep"):
            with self.subTest(mode=mode):
                preview = simulate_overlay_action(_fixture(mode), "switch_debug")
                self.assertFalse(preview["allowed"])
                self.assertEqual("debug_only_action_in_player_mode", preview["blocked_reason"])
                self.assertEqual(mode, preview["next_mode"])

        debug_preview = simulate_overlay_action(_fixture("debug"), "switch_debug")
        self.assertTrue(debug_preview["allowed"])
        self.assertEqual("debug", debug_preview["next_mode"])
        self.assertTrue(debug_preview["next_visibility"]["debug_visible"])

    def test_toggle_original_and_translation_change_preview_visibility_only(self) -> None:
        compact = _fixture("compact")
        original_preview = simulate_overlay_action(compact, "toggle_original")
        translation_preview = simulate_overlay_action(compact, "toggle_translation")

        self.assertFalse(original_preview["next_visibility"]["original_visible"])
        self.assertTrue(original_preview["next_visibility"]["translation_visible"])
        self.assertTrue(translation_preview["next_visibility"]["original_visible"])
        self.assertFalse(translation_preview["next_visibility"]["translation_visible"])
        self.assertFalse(original_preview["mutates_input_view_model"])

    def test_toggle_annotations_works_in_deep_and_blocks_in_compact(self) -> None:
        deep_preview = simulate_overlay_action(_fixture("deep"), "toggle_annotations")
        compact_preview = simulate_overlay_action(_fixture("compact"), "toggle_annotations")

        self.assertTrue(deep_preview["allowed"])
        self.assertFalse(deep_preview["next_visibility"]["annotations_visible"])
        self.assertFalse(compact_preview["allowed"])
        self.assertEqual("action_not_present", compact_preview["blocked_reason"])

    def test_navigation_actions_are_preview_only(self) -> None:
        for action_id in ("next_annotation", "previous_annotation"):
            with self.subTest(action_id=action_id):
                preview = simulate_overlay_action(_fixture("deep"), action_id)
                self.assertTrue(preview["allowed"])
                self.assertEqual("none", preview["side_effect_type"])
                self.assertIsNone(preview["copy_preview_text"])
                self.assertFalse(preview["mutates_input_view_model"])
                self.assertIn("без зміни індексу", preview["summary_uk"])

    def test_copy_original_returns_preview_text_without_clipboard_write(self) -> None:
        compact = _fixture("compact")
        preview = simulate_overlay_action(compact, "copy_original")

        self.assertTrue(preview["allowed"])
        self.assertEqual("copy_preview", preview["side_effect_type"])
        self.assertEqual(compact["source"]["original_english"], preview["copy_preview_text"])
        self.assertFalse(preview["clipboard_written"])

    def test_copy_ukrainian_summary_returns_player_ukrainian_text(self) -> None:
        compact = _fixture("compact")
        deep = _fixture("deep")

        compact_preview = simulate_overlay_action(compact, "copy_ukrainian_summary")
        deep_preview = simulate_overlay_action(deep, "copy_ukrainian_summary")

        self.assertEqual(
            compact["compact"]["concise_meaning_uk"], compact_preview["copy_preview_text"]
        )
        self.assertEqual(deep["deep"]["explanation_uk"], deep_preview["copy_preview_text"])
        self.assertIn("Установа", compact_preview["copy_preview_text"])
        self.assertIn("синтетична", deep_preview["copy_preview_text"])

    def test_copy_annotation_summary_returns_ukrainian_summary(self) -> None:
        deep = _fixture("deep")

        preview = simulate_overlay_action(deep, "copy_annotation_summary")

        self.assertTrue(preview["allowed"])
        self.assertEqual("copy_preview", preview["side_effect_type"])
        self.assertIn(deep["deep"]["explanation_uk"], preview["copy_preview_text"])
        self.assertIn("Образ", preview["copy_preview_text"])

    def test_hide_overlay_returns_hidden_preview(self) -> None:
        preview = simulate_overlay_action(_fixture("compact"), "hide_overlay")

        self.assertTrue(preview["allowed"])
        self.assertEqual("hide_preview", preview["side_effect_type"])
        self.assertTrue(preview["next_visibility"]["hidden"])
        self.assertFalse(preview["keyboard_hook_used"])

    def test_unknown_action_id_is_blocked(self) -> None:
        preview = simulate_overlay_action(_fixture("compact"), "launch_real_overlay")

        self.assertFalse(preview["allowed"])
        self.assertEqual("unknown_action", preview["blocked_reason"])

    def test_action_not_present_is_blocked(self) -> None:
        preview = simulate_overlay_action(_fixture("compact"), "next_annotation")

        self.assertFalse(preview["allowed"])
        self.assertEqual("action_not_present", preview["blocked_reason"])

    def test_malformed_visibility_state_fails(self) -> None:
        compact = _fixture("compact")
        compact["compact"]["visibility"]["original_visible"] = "yes"

        with self.assertRaises(OverlayStateSimulatorError) as raised:
            simulate_overlay_action(compact, "switch_deep")

        self.assertIn("Invalid overlay view model", str(raised.exception))

    def test_simulator_does_not_mutate_input_view_model(self) -> None:
        deep = _fixture("deep")
        original = deepcopy(deep)

        simulate_overlay_action(deep, "toggle_annotations")

        self.assertEqual(original, deep)

    def test_transition_preview_validation_rejects_game_title_and_private_markers(self) -> None:
        preview = simulate_overlay_action(_fixture("compact"), "switch_deep")
        preview["summary_uk"] = "Disco Elysium: The Final Cut"
        preview["copy_preview_text"] = "C:\\Users\\private"

        errors = collect_overlay_transition_errors(preview)

        self.assertTrue(_contains(errors, "Disco Elysium: The Final Cut"))
        self.assertTrue(_contains(errors, "C:\\"))

    def test_assert_valid_transition_accepts_valid_preview(self) -> None:
        preview = simulate_overlay_action(_fixture("deep"), "copy_annotation_summary")

        assert_valid_overlay_transition(preview)

    def test_cli_quiet_allowed_action_passes(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_state_simulator.py",
                "--fixture",
                "compact",
                "--action",
                "switch_deep",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Overlay state transition preview passed", completed.stdout)

    def test_cli_quiet_blocked_action_fails_cleanly(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_state_simulator.py",
                "--fixture",
                "compact",
                "--action",
                "switch_debug",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("debug_only_action_in_player_mode", completed.stderr)

    def test_cli_writes_safe_output_path(self) -> None:
        output = (
            run_overlay_state_simulator.DEFAULT_OUTPUT_ROOT
            / "test-overlay-state-simulator"
            / "summary.json"
        )
        if output.exists():
            output.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_state_simulator.py",
                "--fixture",
                "compact",
                "--action",
                "switch_deep",
                "--output",
                "workspace/synthetic-slice/overlay-prototype/transitions/test-overlay-state-simulator/summary.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        try:
            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("switch_deep", payload["action_id"])
            self.assertEqual("deep", payload["next_mode"])
        finally:
            if output.exists():
                output.unlink()

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_state_simulator.py",
                "--fixture",
                "compact",
                "--action",
                "switch_deep",
                "--output",
                "docs/transition.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)


def _fixture(mode: str) -> dict[str, object]:
    return deepcopy(load_view_model_fixture(mode))


def _contains(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)


if __name__ == "__main__":
    unittest.main()
