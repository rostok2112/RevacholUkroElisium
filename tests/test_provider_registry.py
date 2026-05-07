from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.provider_pipeline import run_provider_pipeline
from scripts.provider_registry import (
    DEFAULT_PROVIDER_ID,
    ProviderRegistryError,
    get_provider_definition,
    list_provider_definitions,
    provider_ids,
    provider_summary,
    resolve_provider_selection,
)
from scripts.schema_validator import load_json
from scripts.synthetic_slice import build_context_packet


ROOT = Path(__file__).resolve().parents[1]
VALID_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
SUCCESS_RESPONSE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"
FUTURE_PROVIDER_IDS = {
    "openai_compatible",
    "deepl_glossary",
    "local_model",
    "ensemble_reviewer",
}


class ProviderRegistryTests(unittest.TestCase):
    def test_registry_lists_mock_as_only_enabled_implemented_default(self) -> None:
        definitions = {item.provider_id: item for item in list_provider_definitions()}

        self.assertEqual("mock", DEFAULT_PROVIDER_ID)
        self.assertEqual({"mock", *FUTURE_PROVIDER_IDS}, set(definitions))
        self.assertTrue(definitions["mock"].implemented)
        self.assertTrue(definitions["mock"].enabled_by_default)
        self.assertTrue(definitions["mock"].offline)
        self.assertTrue(definitions["mock"].deterministic)
        self.assertFalse(definitions["mock"].external)
        self.assertFalse(definitions["mock"].requires_secret)

    def test_future_provider_roles_are_disabled_and_unimplemented(self) -> None:
        for provider_id in FUTURE_PROVIDER_IDS:
            with self.subTest(provider_id=provider_id):
                definition = get_provider_definition(provider_id)
                self.assertFalse(definition.implemented)
                self.assertFalse(definition.enabled_by_default)
                self.assertTrue(definition.external or definition.requires_local_runtime)

    def test_provider_ids_are_stable_registry_ids(self) -> None:
        self.assertEqual(
            ("mock", "openai_compatible", "deepl_glossary", "local_model", "ensemble_reviewer"),
            provider_ids(),
        )

    def test_default_mock_resolution_succeeds(self) -> None:
        selected = resolve_provider_selection()

        self.assertEqual("mock", selected.provider_id)

    def test_unknown_provider_fails_clearly(self) -> None:
        with self.assertRaisesRegex(ProviderRegistryError, "Unknown provider"):
            resolve_provider_selection("missing_provider")

    def test_empty_provider_does_not_silently_fallback_to_mock(self) -> None:
        with self.assertRaisesRegex(ProviderRegistryError, "non-empty"):
            resolve_provider_selection("")

    def test_disabled_provider_fails_clearly(self) -> None:
        with self.assertRaisesRegex(ProviderRegistryError, "disabled"):
            resolve_provider_selection("openai_compatible")

    def test_enabled_external_provider_requires_explicit_external_opt_in(self) -> None:
        with self.assertRaisesRegex(ProviderRegistryError, "allow_external_providers"):
            resolve_provider_selection(
                "openai_compatible",
                enabled_overrides={"openai_compatible": True},
                allow_external_providers=False,
            )

    def test_enabled_future_provider_still_fails_as_unimplemented(self) -> None:
        with self.assertRaisesRegex(ProviderRegistryError, "not implemented"):
            resolve_provider_selection(
                "openai_compatible",
                enabled_overrides={"openai_compatible": True},
                allow_external_providers=True,
            )

    def test_enabled_local_runtime_provider_still_fails_as_unimplemented(self) -> None:
        with self.assertRaisesRegex(ProviderRegistryError, "not implemented"):
            resolve_provider_selection(
                "local_model",
                enabled_overrides={"local_model": True},
                allow_external_providers=False,
            )

    def test_registry_summary_is_roadmap_metadata_only(self) -> None:
        summary = provider_summary()

        self.assertEqual("provider-registry.v1", summary["schema_version"])
        self.assertTrue(summary["runtime_default_mock_only"])
        self.assertEqual("mock", summary["default_provider"])
        self.assertEqual(
            list(provider_ids()), [item["provider_id"] for item in summary["providers"]]
        )

    def test_registry_cli_summary_runs_without_provider_calls(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_provider_registry.py", "--summary"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual("provider-registry.v1", payload["schema_version"])
        self.assertIn("openai_compatible", completed.stdout)

    def test_registry_cli_quiet_smoke_runs(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_provider_registry.py", "--summary", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout)

    def test_public_annotation_metadata_contains_no_future_provider_ids(self) -> None:
        card = run_provider_pipeline(_context_packet())
        rendered = json.dumps(card["provider"], ensure_ascii=True).lower()

        for provider_id in FUTURE_PROVIDER_IDS:
            with self.subTest(provider_id=provider_id):
                self.assertNotIn(provider_id, rendered)

    def test_public_success_fixture_contains_no_future_provider_ids(self) -> None:
        fixture = load_json(SUCCESS_RESPONSE)
        annotation_card = fixture["data"]["annotation_card"]
        rendered = json.dumps(
            {
                "provider": annotation_card["provider"],
                "provider_debug": annotation_card["provider_debug"],
                "prompt_pack": annotation_card["prompt_pack"],
            },
            ensure_ascii=True,
        ).lower()

        for provider_id in FUTURE_PROVIDER_IDS:
            with self.subTest(provider_id=provider_id):
                self.assertNotIn(provider_id, rendered)


def _context_packet() -> dict[str, object]:
    return build_context_packet(load_json(VALID_EVENT))


if __name__ == "__main__":
    unittest.main()
