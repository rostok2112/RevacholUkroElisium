from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.run_m3_line_id_match import (
    EVENT_INPUT_ROOT,
    MATCH_OUTPUT_ROOT,
    PRIVATE_LINE_INDEX_ROOT,
    collect_event_errors,
    run_m3_line_id_match,
    run_self_test,
    write_summary,
    resolve_match_output_path,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class M3LineIdMatchTests(unittest.TestCase):
    def test_fixture_records_line_id_matching_done_only(self) -> None:
        fixture = load_json(ROOT / "tests/fixtures/m3_line_id_matching.synthetic.json")

        self.assertEqual("m3-line-id-matching.v1", fixture["schema_version"])
        self.assertIs(fixture["m3_current_line_event_done"], True)
        self.assertIs(fixture["m3_line_id_matching_done"], True)
        self.assertIs(fixture["m3_debug_console_done"], False)
        self.assertEqual("m3_debug_console", fixture["recommended_next_step"])
        self.assertIs(fixture["exact_line_id_matching_only"], True)
        self.assertIs(fixture["fuzzy_matching_allowed"], False)

    def test_exact_match_is_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            marker = "PRIVATE_EXACT_LINE_ID"
            _write_event_and_index(root, marker, marker)

            summary = run_m3_line_id_match(
                Path(EVENT_INPUT_ROOT) / "event.json",
                Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json",
                root=root,
            )

            self.assertEqual("matched", summary["match_status"])
            self.assertIs(summary["exact_line_id_match"], True)
            self.assertIs(summary["m3_line_id_matching_done"], True)
            rendered = json.dumps(summary, sort_keys=True)
            self.assertNotIn(marker, rendered)
            self.assertNotIn(str(root), rendered)

    def test_unmatched_id_is_blocked_but_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            _write_event_and_index(root, "PRIVATE_EVENT_ID", "PRIVATE_INDEX_ID")

            summary = run_m3_line_id_match(
                Path(EVENT_INPUT_ROOT) / "event.json",
                Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json",
                root=root,
            )

            self.assertEqual("unmatched", summary["match_status"])
            self.assertIn("exact_line_id_not_found", summary["blocker_categories"])
            self.assertIs(summary["m3_line_id_matching_done"], False)
            rendered = json.dumps(summary, sort_keys=True)
            self.assertNotIn("PRIVATE_EVENT_ID", rendered)
            self.assertNotIn("PRIVATE_INDEX_ID", rendered)

    def test_rejects_event_with_raw_text_or_provider_flags(self) -> None:
        event = _event("id")
        event["raw_text_included"] = True
        event["provider_called"] = True

        errors = collect_event_errors(event)

        self.assertIn("event_raw_text_included", errors)
        self.assertIn("event_provider_called", errors)

    def test_rejects_unsafe_paths_and_output_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            _write_event_and_index(root, "id", "id")

            with self.assertRaises(Exception):
                run_m3_line_id_match(
                    Path("../event.json"),
                    Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json",
                    root=root,
                )
            with self.assertRaises(Exception):
                resolve_match_output_path(
                    Path("workspace/local-private/bepinex/out.json"), root=root
                )

    def test_writes_allowed_private_output_without_leaks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            marker = "PRIVATE_OUTPUT_LINE_ID"
            _write_event_and_index(root, marker, marker)
            summary = run_m3_line_id_match(
                Path(EVENT_INPUT_ROOT) / "event.json",
                Path(PRIVATE_LINE_INDEX_ROOT) / "line-index.json",
                root=root,
            )
            output = resolve_match_output_path(Path(MATCH_OUTPUT_ROOT) / "summary.json", root=root)
            write_summary(summary, output)

            written = output.read_text(encoding="utf-8")
            self.assertNotIn(marker, written)
            self.assertNotIn(str(root), written)

    def test_self_test(self) -> None:
        run_self_test()

    def test_check_all_registers_self_test(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/run_m3_line_id_match.py", text)


def _write_event_and_index(root: Path, event_id: str, index_id: str) -> None:
    event_path = root / EVENT_INPUT_ROOT / "event.json"
    index_path = root / PRIVATE_LINE_INDEX_ROOT / "line-index.json"
    event_path.parent.mkdir(parents=True)
    index_path.parent.mkdir(parents=True)
    event_path.write_text(json.dumps(_event(event_id)), encoding="utf-8")
    index_path.write_text(json.dumps(_line_index(index_id)), encoding="utf-8")


def _event(line_id: str) -> dict[str, object]:
    return {
        "schema_version": "m3-current-line-event.v1",
        "event_kind": "current_line",
        "bridge_source": "bepinex",
        "emitted_at_unix_ms": 1,
        "line_id": line_id,
        "conversation_id": "redacted",
        "source": "synthetic",
        "capture_enabled": False,
        "raw_text_included": False,
        "private_paths_included": False,
        "provider_called": False,
    }


def _line_index(line_id: str) -> dict[str, object]:
    return {
        "schema_version": "m2-line-index.v1",
        "entries": [
            {
                "record_id": line_id,
                "line_id": line_id,
                "conversation_id": line_id,
                "speaker_id": line_id,
                "context_placeholder": line_id,
                "source_text": line_id,
                "context_tags": [line_id],
            }
        ],
        "context_graph_constructed": False,
        "retrieval_bucket_mapping_used": False,
    }


if __name__ == "__main__":
    unittest.main()
