from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.check_overlay_state_source_fixtures import (
    FIXTURE_PATHS,
    STATE_SOURCE_CASES,
    OverlayStateSourceFixtureError,
    build_current_state_sources,
    check_overlay_state_source_fixtures,
    validate_state_source_fixture,
)
from scripts.overlay_state_simulator import simulate_overlay_action
from scripts.overlay_state_source import assert_valid_overlay_state_source
from scripts.overlay_viewmodel_validator import assert_valid_overlay_view_model
from scripts.schema_validator import load_json
from scripts.synthetic_slice import ROOT


FORBIDDEN_MARKERS = (
    "Disco Elysium: The Final Cut",
    "context_packet.game.title",
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


class OverlayStateSourceFixtureTests(unittest.TestCase):
    def test_all_committed_fixtures_validate(self) -> None:
        for case, path in FIXTURE_PATHS.items():
            with self.subTest(case=case):
                state = load_json(path)
                validate_state_source_fixture(case, state)
                assert_valid_overlay_state_source(state)

    def test_fixture_checker_passes_current_fixtures(self) -> None:
        summary = check_overlay_state_source_fixtures()

        self.assertTrue(summary["ok"])
        self.assertFalse(summary["write"])
        self.assertEqual(set(STATE_SOURCE_CASES), set(summary["fixtures"]))

    def test_fixture_checker_detects_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _temp_fixture_paths(Path(tmp))
            check_overlay_state_source_fixtures(write=True, fixture_paths=paths)
            payload = load_json(paths["ready.compact"])
            payload["current_mode"] = "deep"
            paths["ready.compact"].write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(OverlayStateSourceFixtureError) as raised:
                check_overlay_state_source_fixtures(fixture_paths=paths)

        self.assertIn("committed fixture is invalid", str(raised.exception))

    def test_write_regeneration_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = _temp_fixture_paths(Path(tmp))
            check_overlay_state_source_fixtures(write=True, fixture_paths=paths)
            first = {case: paths[case].read_text(encoding="utf-8") for case in STATE_SOURCE_CASES}
            check_overlay_state_source_fixtures(write=True, fixture_paths=paths)
            second = {case: paths[case].read_text(encoding="utf-8") for case in STATE_SOURCE_CASES}

        self.assertEqual(first, second)

    def test_ready_fixtures_embed_valid_view_models_and_transitions(self) -> None:
        for case in ("ready.compact", "ready.deep", "ready.debug"):
            with self.subTest(case=case):
                state = load_json(FIXTURE_PATHS[case])
                mode = case.split(".", 1)[1]
                assert_valid_overlay_view_model(state["view_model"], expected_mode=mode)
                action_id = {
                    "compact": "switch_deep",
                    "deep": "switch_compact",
                    "debug": "switch_debug",
                }[mode]
                preview = simulate_overlay_action(state["view_model"], action_id)
                self.assertTrue(preview["allowed"])

    def test_no_provider_state_is_valid_not_a_crash(self) -> None:
        state = load_json(FIXTURE_PATHS["no_provider_state"])

        self.assertEqual("no_provider_state", state["source_status"])
        self.assertIsNone(state["view_model"])
        self.assertEqual([], state["available_actions"])
        self.assertEqual("no_provider_state", state["error"]["code"])

    def test_stale_state_is_deterministic(self) -> None:
        state = load_json(FIXTURE_PATHS["stale"])
        generated = build_current_state_sources()["stale"]

        self.assertEqual("stale", state["source_status"])
        self.assertEqual(30, state["stale_after_seconds"])
        self.assertEqual("stale", state["error"]["code"])
        self.assertEqual(generated, state)

    def test_error_state_contains_safe_redacted_error_only(self) -> None:
        state = load_json(FIXTURE_PATHS["error"])

        self.assertEqual("error", state["source_status"])
        self.assertIsNone(state["view_model"])
        self.assertEqual("partial_provider_state", state["error"]["code"])
        rendered = json.dumps(state, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("C:\\", rendered)
        self.assertNotIn("prompt_pack_sections", rendered)

    def test_fixtures_exclude_forbidden_markers(self) -> None:
        for case, path in FIXTURE_PATHS.items():
            rendered = path.read_text(encoding="utf-8")
            with self.subTest(case=case):
                for marker in FORBIDDEN_MARKERS:
                    self.assertNotIn(marker.lower(), rendered.lower(), marker)

    def test_safety_validation_rejects_game_title_and_secret_markers(self) -> None:
        state = deepcopy(load_json(FIXTURE_PATHS["ready.compact"]))
        state["view_model"]["source"]["original_english"] = "Disco Elysium: The Final Cut"

        with self.assertRaises(OverlayStateSourceFixtureError) as raised:
            validate_state_source_fixture("ready.compact", state)

        self.assertIn("Disco Elysium: The Final Cut", str(raised.exception))

    def test_no_side_effect_alias_fields_are_locked(self) -> None:
        state = load_json(FIXTURE_PATHS["ready.compact"])

        self.assertFalse(state["provider_call_performed"])
        self.assertFalse(state["calls_provider"])
        self.assertFalse(state["companion_contract_changed"])
        self.assertFalse(state["companion_http_contract_changed"])

    def test_cli_quiet_passes(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/check_overlay_state_source_fixtures.py",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Overlay state-source fixture check passed", completed.stdout)

    def test_cli_write_to_committed_fixture_paths_is_explicit(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/check_overlay_state_source_fixtures.py",
                "--help",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode)
        self.assertIn("--write", completed.stdout)
        self.assertNotIn("--output", completed.stdout)


def _temp_fixture_paths(root: Path) -> dict[str, Path]:
    return {case: root / f"{case.replace('.', '_')}.json" for case in STATE_SOURCE_CASES}


if __name__ == "__main__":
    unittest.main()
