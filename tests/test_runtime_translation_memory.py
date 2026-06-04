from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_runtime_translation_memory_contract import (
    CACHE_ROOT,
    RECOMMENDED_NEXT_STEP,
    collect_runtime_translation_memory_contract_errors,
)
from scripts.run_runtime_translation_memory import (
    PRIVATE_ANNOTATION_ROOT,
    PRIVATE_CACHE_ROOT,
    PRIVATE_EVENT_ROOT,
    PRIVATE_SUMMARY_ROOT,
    RuntimeTranslationMemoryError,
    resolve_cache_root,
    resolve_private_file_path,
    resolve_summary_output_path,
    run_self_test,
    run_translation_memory,
    write_summary,
)
from scripts.schema_validator import load_json
from scripts.synthetic_slice import ROOT


FIXTURE = ROOT / "tests/fixtures/runtime_translation_memory_contract.synthetic.json"
CHECK_ALL = ROOT / "scripts/check_all.py"
PRIVATE_SOURCE = "PRIVATE_SOURCE_TEXT_SHOULD_NOT_APPEAR"
PRIVATE_UK = "PRIVATE_UKRAINIAN_TRANSLATION_SHOULD_NOT_APPEAR"


class RuntimeTranslationMemoryContractTests(unittest.TestCase):
    def test_contract_fixture_is_valid(self) -> None:
        self.assertEqual([], collect_runtime_translation_memory_contract_errors())
        fixture = load_json(FIXTURE)
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual([CACHE_ROOT], fixture["allowed_private_cache_roots"])

    def test_contract_rejects_provider_on_hit(self) -> None:
        payload = load_json(FIXTURE)
        payload["provider_call_required_on_cache_hit"] = True
        self.assertIn(
            "provider_call_required_on_cache_hit",
            "\n".join(_errors_for_payload(payload)),
        )

    def test_contract_rejects_unsafe_marker(self) -> None:
        payload = load_json(FIXTURE)
        payload["notes"] = "provider execution approved"
        self.assertIn("forbidden marker", "\n".join(_errors_for_payload(payload)))

    def test_check_all_registration(self) -> None:
        text = CHECK_ALL.read_text(encoding="utf-8")
        self.assertIn("scripts/check_runtime_translation_memory_contract.py", text)
        self.assertIn("scripts/run_runtime_translation_memory.py", text)


class RuntimeTranslationMemoryHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "repo"
        self.event_dir = self.root / PRIVATE_EVENT_ROOT
        self.annotation_dir = self.root / PRIVATE_ANNOTATION_ROOT
        self.event_dir.mkdir(parents=True)
        self.annotation_dir.mkdir(parents=True)
        self.event_path = self.event_dir / "event.json"
        self.annotation_path = self.annotation_dir / "annotation.json"
        self.event_path.write_text(json.dumps(_event()), encoding="utf-8")
        self.annotation_path.write_text(json.dumps(_annotation()), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_first_lookup_is_miss_and_requires_provider(self) -> None:
        summary = run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            None,
            Path(PRIVATE_CACHE_ROOT),
            mode="lookup",
            root=self.root,
        )
        self.assertFalse(summary["cache_hit"])
        self.assertTrue(summary["provider_call_required"])
        self.assertEqual("line_id", summary["key_kind"])
        self.assert_summary_redacted(summary)

    def test_store_then_lookup_is_hit_and_skips_provider(self) -> None:
        stored = run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            Path(PRIVATE_ANNOTATION_ROOT) / "annotation.json",
            Path(PRIVATE_CACHE_ROOT),
            mode="store",
            root=self.root,
        )
        self.assertTrue(stored["cache_hit"])
        self.assertFalse(stored["provider_call_required"])

        lookup = run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            None,
            Path(PRIVATE_CACHE_ROOT),
            mode="lookup",
            root=self.root,
        )
        self.assertTrue(lookup["cache_hit"])
        self.assertFalse(lookup["provider_call_required"])
        self.assert_summary_redacted(lookup)

    def test_line_id_key_is_preferred_over_text(self) -> None:
        event = _event()
        event["source_text"] = "changed private source"
        self.event_path.write_text(json.dumps(event), encoding="utf-8")
        summary = run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            Path(PRIVATE_ANNOTATION_ROOT) / "annotation.json",
            Path(PRIVATE_CACHE_ROOT),
            mode="lookup-or-store",
            root=self.root,
        )
        self.assertEqual("line_id", summary["key_kind"])

    def test_fallback_key_is_private_and_not_rendered(self) -> None:
        event = _event()
        del event["line_id"]
        self.event_path.write_text(json.dumps(event), encoding="utf-8")
        summary = run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            Path(PRIVATE_ANNOTATION_ROOT) / "annotation.json",
            Path(PRIVATE_CACHE_ROOT),
            mode="lookup-or-store",
            root=self.root,
        )
        self.assertEqual("fallback_private_content", summary["key_kind"])
        rendered = json.dumps(summary, sort_keys=True)
        self.assertNotIn(PRIVATE_SOURCE, rendered)
        self.assertNotRegex(rendered, r"[a-f0-9]{64}")

    def test_unsafe_paths_are_rejected(self) -> None:
        with self.assertRaises(RuntimeTranslationMemoryError):
            resolve_private_file_path(
                Path("workspace/local-private/runtime-events/../event.json"),
                PRIVATE_EVENT_ROOT,
                "event",
                root=self.root,
            )
        with self.assertRaises(RuntimeTranslationMemoryError):
            resolve_cache_root(Path("docs/cache"), root=self.root)
        with self.assertRaises(RuntimeTranslationMemoryError):
            resolve_summary_output_path(Path("docs/summary.json"), root=self.root)

    def test_summary_output_is_private_and_redacted(self) -> None:
        summary = run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            Path(PRIVATE_ANNOTATION_ROOT) / "annotation.json",
            Path(PRIVATE_CACHE_ROOT),
            mode="lookup-or-store",
            root=self.root,
        )
        output = resolve_summary_output_path(
            Path(PRIVATE_SUMMARY_ROOT) / "summary.json",
            root=self.root,
        )
        write_summary(summary, output)
        rendered = output.read_text(encoding="utf-8")
        for forbidden in (PRIVATE_SOURCE, PRIVATE_UK, "runtime.line.001", str(self.root)):
            self.assertNotIn(forbidden, rendered)

    def test_cache_files_are_only_under_allowed_root(self) -> None:
        run_translation_memory(
            Path(PRIVATE_EVENT_ROOT) / "event.json",
            Path(PRIVATE_ANNOTATION_ROOT) / "annotation.json",
            Path(PRIVATE_CACHE_ROOT),
            mode="lookup-or-store",
            root=self.root,
        )
        cache_root = self.root / PRIVATE_CACHE_ROOT
        files = list(cache_root.glob("*.json"))
        self.assertEqual(1, len(files))
        self.assertTrue(str(files[0]).startswith(str(cache_root)))

    def test_self_test(self) -> None:
        run_self_test()

    def assert_summary_redacted(self, summary: dict[str, object]) -> None:
        rendered = json.dumps(summary, sort_keys=True)
        for forbidden in (PRIVATE_SOURCE, PRIVATE_UK, "runtime.line.001", str(self.root)):
            self.assertNotIn(forbidden, rendered)
        self.assertFalse(summary["paths_included"])
        self.assertFalse(summary["source_text_included"])
        self.assertFalse(summary["translated_text_included"])
        self.assertFalse(summary["provider_payloads_included"])


def _event() -> dict[str, object]:
    return {
        "schema_version": "runtime-current-line-event.v1",
        "line_id": "runtime.line.001",
        "source_text": PRIVATE_SOURCE,
        "speaker": "PRIVATE_SPEAKER_SHOULD_NOT_APPEAR",
    }


def _annotation() -> dict[str, object]:
    return {
        "schema_version": "runtime-annotation.v1",
        "line_id": "runtime.line.001",
        "compact_translation_uk": PRIVATE_UK,
        "provider_payload": {"private": "PRIVATE_PAYLOAD_SHOULD_NOT_APPEAR"},
    }


def _errors_for_payload(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "fixture.json"
        path.write_text(json.dumps(copy.deepcopy(payload)), encoding="utf-8")
        return collect_runtime_translation_memory_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
