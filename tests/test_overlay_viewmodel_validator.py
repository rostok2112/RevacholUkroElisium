from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts import check_overlay_viewmodel_fixtures as fixture_check
from scripts.overlay_viewmodel_validator import (
    OverlayViewModelValidationError,
    assert_valid_overlay_view_model,
    collect_overlay_viewmodel_errors,
)


class OverlayViewModelValidatorTests(unittest.TestCase):
    def test_valid_committed_fixtures_pass(self) -> None:
        for mode in ("compact", "deep", "debug"):
            with self.subTest(mode=mode):
                assert_valid_overlay_view_model(_load_fixture(mode), expected_mode=mode)

    def test_missing_required_compact_field_fails(self) -> None:
        compact = _load_fixture("compact")
        del compact["compact"]["concise_meaning_uk"]

        errors = collect_overlay_viewmodel_errors(compact, expected_mode="compact")

        self.assertTrue(_contains(errors, "concise_meaning_uk"))

    def test_wrong_mode_fails(self) -> None:
        compact = _load_fixture("compact")
        compact["mode"] = "deep"

        errors = collect_overlay_viewmodel_errors(compact, expected_mode="compact")

        self.assertTrue(_contains(errors, "$.mode"))
        self.assertTrue(_contains(errors, "expected 'compact'"))

    def test_compact_raw_flag_fails(self) -> None:
        compact = _load_fixture("compact")
        compact["compact"]["risk_summary_uk"] = "synthetic_fixture"

        errors = collect_overlay_viewmodel_errors(compact, expected_mode="compact")

        self.assertTrue(_contains(errors, "synthetic_fixture"))

    def test_deep_provider_debug_fails(self) -> None:
        deep = _load_fixture("deep")
        deep["deep"]["provider_debug"] = {"provider_name": "mock"}

        errors = collect_overlay_viewmodel_errors(deep, expected_mode="deep")

        self.assertTrue(_contains(errors, "provider_debug"))

    def test_debug_secret_and_private_path_fail(self) -> None:
        debug = _load_fixture("debug")
        debug["debug"]["privacy"]["cache_root"] = "C:\\Users\\example\\secret-cache"

        errors = collect_overlay_viewmodel_errors(debug, expected_mode="debug")

        self.assertTrue(_contains(errors, "C:\\"))
        self.assertTrue(_contains(errors, "secret"))

    def test_visibility_state_is_mode_specific(self) -> None:
        compact = _load_fixture("compact")
        deep = _load_fixture("deep")
        debug = _load_fixture("debug")

        self.assertFalse(compact["compact"]["visibility"]["annotations_visible"])
        self.assertFalse(compact["compact"]["visibility"]["debug_visible"])
        self.assertEqual(["compact", "deep"], compact["compact"]["visibility"]["available_modes"])
        self.assertTrue(deep["deep"]["visibility"]["annotations_visible"])
        self.assertFalse(deep["deep"]["visibility"]["debug_visible"])
        self.assertTrue(debug["debug"]["visibility"]["debug_visible"])
        self.assertEqual(
            ["compact", "deep", "debug"],
            debug["debug"]["visibility"]["available_modes"],
        )

    def test_unknown_action_id_fails(self) -> None:
        compact = _load_fixture("compact")
        compact["compact"]["actions"][0]["id"] = "launch_real_overlay"

        errors = collect_overlay_viewmodel_errors(compact, expected_mode="compact")

        self.assertTrue(_contains(errors, "unknown action id"))

    def test_empty_action_label_fails(self) -> None:
        compact = _load_fixture("compact")
        compact["compact"]["actions"][0]["label_uk"] = ""

        errors = collect_overlay_viewmodel_errors(compact, expected_mode="compact")

        self.assertTrue(_contains(errors, "label_uk"))
        self.assertTrue(_contains(errors, "must not be empty"))

    def test_action_key_binding_field_fails(self) -> None:
        compact = _load_fixture("compact")
        compact["compact"]["actions"][0]["key_binding"] = "Ctrl+Space"

        errors = collect_overlay_viewmodel_errors(compact, expected_mode="compact")

        self.assertTrue(_contains(errors, "key_binding"))

    def test_debug_visible_true_fails_in_compact(self) -> None:
        compact = _load_fixture("compact")
        compact["compact"]["visibility"]["debug_visible"] = True

        errors = collect_overlay_viewmodel_errors(compact, expected_mode="compact")

        self.assertTrue(_contains(errors, "debug_visible"))
        self.assertTrue(_contains(errors, "debug hidden"))

    def test_debug_only_action_fails_in_compact(self) -> None:
        compact = _load_fixture("compact")
        switch_debug = _load_fixture("debug")["debug"]["actions"][2]
        compact["compact"]["actions"].append(switch_debug)

        errors = collect_overlay_viewmodel_errors(compact, expected_mode="compact")

        self.assertTrue(_contains(errors, "debug-only action"))

    def test_debug_fixture_can_include_debug_only_action(self) -> None:
        debug = _load_fixture("debug")

        errors = collect_overlay_viewmodel_errors(debug, expected_mode="debug")

        self.assertFalse(errors)
        self.assertIn("switch_debug", [action["id"] for action in debug["debug"]["actions"]])

    def test_context_packet_game_title_fails_in_every_mode(self) -> None:
        for mode in ("compact", "deep", "debug"):
            view_model = _load_fixture(mode)
            view_model["source"]["original_english"] = "Disco Elysium: The Final Cut"

            errors = collect_overlay_viewmodel_errors(view_model, expected_mode=mode)

            with self.subTest(mode=mode):
                self.assertTrue(_contains(errors, "Disco Elysium: The Final Cut"))

    def test_generated_html_marker_fails(self) -> None:
        debug = _load_fixture("debug")
        debug["debug"]["raw_deep_notes"][0]["text"] = "<!doctype html><html></html>"

        errors = collect_overlay_viewmodel_errors(debug, expected_mode="debug")

        self.assertTrue(_contains(errors, "<!doctype html>"))

    def test_assert_valid_raises_clear_error(self) -> None:
        compact = _load_fixture("compact")
        compact["compact"]["risk_summary_uk"] = "mock_provider"

        with self.assertRaises(OverlayViewModelValidationError) as raised:
            assert_valid_overlay_view_model(compact, expected_mode="compact")

        self.assertIn("mock_provider", str(raised.exception))

    def test_fixture_checker_surfaces_contract_validation_failure(self) -> None:
        current = fixture_check.build_current_view_models()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_paths = {
                mode: temp_root / f"overlay_prototype.{mode}.viewmodel.synthetic.json"
                for mode in ("compact", "deep", "debug")
            }
            for mode, path in temp_paths.items():
                payload = deepcopy(current[mode])
                if mode == "compact":
                    del payload["compact"]["concise_meaning_uk"]
                path.write_text(
                    fixture_check.canonical_json(payload) + "\n",
                    encoding="utf-8",
                )

            original_paths = fixture_check.FIXTURE_PATHS
            fixture_check.FIXTURE_PATHS = temp_paths
            try:
                with self.assertRaises(fixture_check.OverlayFixtureError) as raised:
                    fixture_check.check_overlay_viewmodel_fixtures()
            finally:
                fixture_check.FIXTURE_PATHS = original_paths

        message = str(raised.exception)
        self.assertIn("committed fixture is invalid", message)
        self.assertIn("contract validation failed", message)
        self.assertIn("concise_meaning_uk", message)


def _load_fixture(mode: str) -> dict[str, object]:
    return json.loads(fixture_check.FIXTURE_PATHS[mode].read_text(encoding="utf-8"))


def _contains(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)


if __name__ == "__main__":
    unittest.main()
