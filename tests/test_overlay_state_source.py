from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.companion_client import CompanionConnectionError
from scripts.overlay_state_simulator import simulate_overlay_action
from scripts.overlay_state_source import (
    assert_valid_overlay_state_source,
    build_overlay_state_from_client,
    build_overlay_state_source,
    collect_overlay_state_source_errors,
)
from scripts.overlay_viewmodel_validator import assert_valid_overlay_view_model
from scripts.run_overlay_state_source import DEFAULT_OUTPUT_ROOT, resolve_output_path
from scripts.schema_validator import load_json
from scripts.synthetic_slice import ROOT


PROVIDER_SUCCESS_FIXTURE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"

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


class OverlayStateSourceTests(unittest.TestCase):
    def test_ready_state_from_latest_provider_payloads(self) -> None:
        context_packet, annotation_card = _provider_payloads()

        state = build_overlay_state_source(context_packet, annotation_card, mode="compact")

        self.assertEqual("overlay-state-source.v1", state["schema_version"])
        self.assertEqual("ready", state["source_status"])
        self.assertEqual("compact", state["current_mode"])
        self.assertEqual(context_packet["current_line"]["line_id"], state["line_id"])
        self.assertEqual(context_packet["current_line"]["line_id"], state["last_update_id"])
        self.assertEqual(state["view_model"]["compact"]["visibility"], state["visibility"])
        self.assertEqual(state["view_model"]["compact"]["actions"], state["available_actions"])
        self.assertFalse(state["polling_loop_started"])
        self.assertFalse(state["timer_started"])
        self.assertFalse(state["background_thread_started"])
        self.assertFalse(state["calls_provider"])
        self.assertFalse(state["companion_http_contract_changed"])
        self.assertFalse(state["ui_side_effects"])
        assert_valid_overlay_state_source(state)

    def test_no_provider_state_when_latest_provider_data_is_absent(self) -> None:
        state = build_overlay_state_source(None, None, mode="compact")

        self.assertEqual("no_provider_state", state["source_status"])
        self.assertIsNone(state["view_model"])
        self.assertEqual([], state["available_actions"])
        self.assertEqual("no_provider_state", state["error"]["code"])
        assert_valid_overlay_state_source(state)

    def test_partial_provider_state_is_error(self) -> None:
        context_packet, _annotation_card = _provider_payloads()

        state = build_overlay_state_source(context_packet, None, mode="compact")

        self.assertEqual("error", state["source_status"])
        self.assertEqual("partial_provider_state", state["error"]["code"])
        self.assertIsNone(state["view_model"])

    def test_compact_deep_debug_modes_validate_view_models(self) -> None:
        context_packet, annotation_card = _provider_payloads()

        for mode in ("compact", "deep", "debug"):
            with self.subTest(mode=mode):
                state = build_overlay_state_source(context_packet, annotation_card, mode=mode)
                self.assertEqual("ready", state["source_status"])
                assert_valid_overlay_view_model(state["view_model"], expected_mode=mode)
                assert_valid_overlay_state_source(state)
                if mode == "debug":
                    self.assertIsInstance(state["debug_summary"], dict)
                    self.assertEqual("mock", state["debug_summary"]["provider_name"])
                else:
                    self.assertIsNone(state["debug_summary"])

    def test_state_source_output_excludes_forbidden_markers(self) -> None:
        state = build_overlay_state_source(*_provider_payloads(), mode="debug")
        rendered = json.dumps(state, ensure_ascii=False, sort_keys=True)

        for marker in FORBIDDEN_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker.lower(), rendered.lower())

    def test_stale_state_can_be_represented_deterministically(self) -> None:
        context_packet, annotation_card = _provider_payloads()

        state = build_overlay_state_source(
            context_packet,
            annotation_card,
            mode="deep",
            stale=True,
            stale_after_seconds=12,
        )

        self.assertEqual("stale", state["source_status"])
        self.assertEqual(12, state["stale_after_seconds"])
        self.assertEqual("stale", state["error"]["code"])
        self.assertEqual("deep", state["current_mode"])
        assert_valid_overlay_state_source(state)

    def test_previous_state_becomes_stale_when_provider_state_disappears(self) -> None:
        ready = build_overlay_state_source(*_provider_payloads(), mode="compact")

        stale = build_overlay_state_source(None, None, mode="compact", previous_state=ready)

        self.assertEqual("stale", stale["source_status"])
        self.assertEqual(ready["view_model"], stale["view_model"])
        self.assertEqual("stale", stale["error"]["code"])

    def test_fake_client_ready_and_no_provider_state(self) -> None:
        context_packet, annotation_card = _provider_payloads()
        ready_client = FakeClient(context_packet, annotation_card)
        empty_client = FakeClient(None, None)

        ready = build_overlay_state_from_client(ready_client, mode="compact")
        empty = build_overlay_state_from_client(empty_client, mode="compact")

        self.assertEqual("ready", ready["source_status"])
        self.assertEqual("no_provider_state", empty["source_status"])

    def test_client_error_becomes_error_state(self) -> None:
        state = build_overlay_state_from_client(RaisingClient(), mode="compact")

        self.assertEqual("error", state["source_status"])
        self.assertEqual("companion_client_error", state["error"]["code"])
        self.assertFalse(state["polling_loop_started"])

    def test_transition_simulator_can_consume_ready_state_view_model(self) -> None:
        state = build_overlay_state_source(*_provider_payloads(), mode="compact")

        preview = simulate_overlay_action(state["view_model"], "switch_deep")

        self.assertTrue(preview["allowed"])
        self.assertEqual("deep", preview["next_mode"])

    def test_malformed_provider_payload_returns_error_state(self) -> None:
        context_packet, annotation_card = _provider_payloads()
        broken_context = deepcopy(context_packet)
        del broken_context["current_line"]["source_text"]

        state = build_overlay_state_source(broken_context, annotation_card, mode="compact")

        self.assertEqual("error", state["source_status"])
        self.assertEqual("invalid_provider_state", state["error"]["code"])

    def test_invalid_state_source_validation_reports_forbidden_game_title(self) -> None:
        state = build_overlay_state_source(*_provider_payloads(), mode="compact")
        state["view_model"]["source"]["original_english"] = "Disco Elysium: The Final Cut"

        errors = collect_overlay_state_source_errors(state)

        self.assertTrue(_contains(errors, "Disco Elysium: The Final Cut"))

    def test_output_path_allows_state_workspace(self) -> None:
        output = resolve_output_path(
            Path("workspace/synthetic-slice/overlay-prototype/state/source-state.json")
        )

        self.assertTrue(_is_relative_to(output, DEFAULT_OUTPUT_ROOT))

    def test_output_path_rejects_public_repo_path(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_path(Path("docs/source-state.json"))

    def test_cli_self_test_starts_and_stops_server_cleanly(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_state_source.py",
                "--self-test",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("Overlay state source self-test passed", completed.stdout)

    def test_cli_writes_safe_output_path(self) -> None:
        output = DEFAULT_OUTPUT_ROOT / "test-state-source" / "source-state.json"
        if output.exists():
            output.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_state_source.py",
                "--self-test",
                "--output",
                "workspace/synthetic-slice/overlay-prototype/state/test-state-source/source-state.json",
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
            self.assertEqual("ready", payload["source_status"])
        finally:
            if output.exists():
                output.unlink()

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_overlay_state_source.py",
                "--self-test",
                "--output",
                "docs/source-state.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)


class FakeClient:
    def __init__(
        self,
        context_packet: dict[str, object] | None,
        annotation_card: dict[str, object] | None,
    ) -> None:
        self.context_packet = context_packet
        self.annotation_card = annotation_card

    def latest_provider_context(self) -> dict[str, object] | None:
        return self.context_packet

    def latest_provider_annotation(self) -> dict[str, object] | None:
        return self.annotation_card


class RaisingClient:
    def latest_provider_context(self) -> None:
        raise CompanionConnectionError("Could not reach companion server")

    def latest_provider_annotation(self) -> None:
        raise AssertionError("latest_provider_annotation should not be called")


def _provider_payloads() -> tuple[dict[str, object], dict[str, object]]:
    envelope = load_json(PROVIDER_SUCCESS_FIXTURE)
    return (
        deepcopy(envelope["data"]["context_packet"]),
        deepcopy(envelope["data"]["annotation_card"]),
    )


def _contains(errors: list[str], needle: str) -> bool:
    return any(needle in error for error in errors)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
