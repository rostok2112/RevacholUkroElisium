from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.provider_pipeline import build_provider_request
from scripts.provider_privacy import (
    CACHE_KEY_PREFIX,
    build_cache_write_plan,
    build_provider_privacy_envelope,
    compute_provider_cache_key,
    envelope_contains_prompt_text,
    envelope_contains_raw_text,
)
from scripts.provider_runtime_safety import (
    REDACTED_PATH,
    REDACTED_VALUE,
    build_provider_execution_plan,
)
from scripts.run_provider_privacy_check import DEFAULT_OUTPUT_ROOT, ROOT, resolve_output_path
from scripts.schema_validator import load_json
from scripts.synthetic_slice import build_context_packet
from scripts.validate_config import load_config


EXAMPLE_CONFIG = ROOT / "config/revachol.example.toml"
VALID_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
SUCCESS_RESPONSE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"
FUTURE_PROVIDER_IDS = {
    "openai_compatible",
    "deepl_glossary",
    "local_model",
    "ensemble_reviewer",
}


class ProviderPrivacyTests(unittest.TestCase):
    def test_privacy_envelope_omits_raw_source_and_prompt_text(self) -> None:
        request = _provider_request()
        envelope = build_provider_privacy_envelope(request, _config())

        self.assertFalse(envelope_contains_raw_text(envelope, request.original_english))
        self.assertFalse(envelope_contains_prompt_text(envelope, request))
        rendered = json.dumps(envelope, ensure_ascii=False)
        self.assertNotIn(request.original_english, rendered)
        self.assertNotIn(request.prompt_pack_sections["synthetic_examples"], rendered)

    def test_privacy_envelope_contains_expected_summary_fields(self) -> None:
        request = _provider_request()
        envelope = build_provider_privacy_envelope(request, _config())

        self.assertTrue(envelope["ok"])
        self.assertEqual("provider-privacy-envelope.v1", envelope["schema_version"])
        self.assertEqual("mock", envelope["provider_id"])
        self.assertEqual("mock_offline_deterministic", envelope["provider_mode"])
        self.assertEqual(request.prompt_pack_id, envelope["prompt_pack_id"])
        self.assertEqual(request.prompt_pack_version, envelope["prompt_pack_version"])
        self.assertEqual(request.context_packet_id, envelope["context_packet_id"])
        self.assertEqual(request.line_id, envelope["line_id"])
        self.assertTrue(envelope["synthetic"])
        self.assertTrue(envelope["mock"])
        self.assertTrue(envelope["request_field_presence"]["original_english"])
        self.assertEqual(
            len(request.original_english), envelope["text_metadata"]["original_english_length"]
        )
        self.assertEqual(1, envelope["text_metadata"]["visible_history_count"])
        self.assertTrue(envelope["cache_key"].startswith(CACHE_KEY_PREFIX + "."))
        self.assertEqual("workspace/provider-cache", envelope["cache_root"])
        self.assertTrue(envelope["cache_write_plan"]["dry_run"])
        self.assertFalse(envelope["cache_write_plan"]["would_write"])
        self.assertFalse(envelope["cache_write_plan"]["writes_raw_payload"])
        self.assertFalse(envelope["calls_external_services"])
        self.assertTrue(envelope["dry_run"])

    def test_cache_key_is_stable_and_omits_raw_text(self) -> None:
        request = _provider_request()

        first = compute_provider_cache_key(request)
        second = compute_provider_cache_key(request)

        self.assertEqual(first, second)
        self.assertRegex(first, r"^provider-cache-v1\.[0-9a-f]{32}$")
        self.assertNotIn(request.original_english, first)

    def test_cache_key_changes_when_request_identity_changes(self) -> None:
        request = _provider_request()
        changed = replace(request, request_id=request.request_id + ".changed")

        self.assertNotEqual(
            compute_provider_cache_key(request), compute_provider_cache_key(changed)
        )

    def test_cache_dry_run_plan_uses_private_ignored_cache_root(self) -> None:
        request = _provider_request()
        plan = build_cache_write_plan(request, _config())

        self.assertTrue(plan["ok"])
        self.assertEqual("workspace/provider-cache", plan["cache_root"])
        self.assertTrue(plan["cache_root_is_private"])
        self.assertTrue(plan["cache_root_is_repo_ignored"])
        self.assertTrue(plan["planned_relative_path"].startswith("workspace/provider-cache/mock/"))
        self.assertTrue(plan["planned_relative_path"].endswith(".json"))
        self.assertFalse(plan["would_write"])
        self.assertFalse(plan["writes_raw_payload"])

    def test_unsafe_cache_root_blocks_cache_plan(self) -> None:
        config = _config()
        config["llm"]["provider_cache_dir"] = "docs/provider-cache"  # type: ignore[index]
        request = _provider_request()

        plan = build_cache_write_plan(request, config)

        self.assertFalse(plan["ok"])
        self.assertFalse(plan["write_allowed"])
        self.assertIn("provider_cache_root_not_ignored_private_root", plan["blocked_reasons"])

    def test_redacts_secret_like_config_and_absolute_paths(self) -> None:
        config = _config()
        config["llm"]["provider_cache_dir"] = "C:/Users/example/private/provider-cache"  # type: ignore[index]
        config["llm"]["providers"]["mock"]["api_key"] = "sk-test-secret"  # type: ignore[index]
        config["llm"]["providers"]["mock"]["token_value"] = "Bearer abc.def"  # type: ignore[index]
        request = _provider_request()

        envelope = build_provider_privacy_envelope(request, config)
        provider_config = envelope["redacted_config_summary"]["llm"]["providers"]["mock"]

        self.assertEqual(REDACTED_PATH, envelope["cache_root"])
        self.assertEqual(REDACTED_VALUE, provider_config["api_key"])
        self.assertEqual(REDACTED_VALUE, provider_config["token_value"])
        rendered = json.dumps(envelope, ensure_ascii=True)
        self.assertNotIn("C:/Users/example", rendered)
        self.assertNotIn("sk-test-secret", rendered)
        self.assertNotIn("Bearer abc.def", rendered)

    def test_output_path_allows_provider_privacy_workspace(self) -> None:
        output = resolve_output_path(
            Path("workspace/synthetic-slice/provider-privacy/summary-test.json")
        )

        self.assertTrue(_is_relative_to(output, DEFAULT_OUTPUT_ROOT))

    def test_output_path_rejects_public_repo_path(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_path(Path("docs/provider-privacy.json"))

    def test_cli_mock_provider_privacy_check_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_provider_privacy_check.py", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout)

    def test_cli_future_provider_blocks_before_request_envelope(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_privacy_check.py",
                "--provider",
                "openai_compatible",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        payload = json.loads(completed.stdout)
        self.assertFalse(payload["ok"])
        self.assertIsNone(payload["privacy_envelope"])
        self.assertIn("provider_disabled", payload["execution_plan"]["blocked_reasons"])
        self.assertFalse(payload["execution_plan"]["calls_external_services"])

    def test_cli_writes_redacted_summary_only_under_allowed_workspace(self) -> None:
        output = DEFAULT_OUTPUT_ROOT / "summary-test.json"
        if output.exists():
            output.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_privacy_check.py",
                "--output",
                "workspace/synthetic-slice/provider-privacy/summary-test.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(output.exists())
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(payload["ok"])
        self.assertFalse(
            envelope_contains_raw_text(
                payload["privacy_envelope"], _provider_request().original_english
            )
        )
        output.unlink()

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_privacy_check.py",
                "--output",
                "docs/provider-privacy.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)

    def test_preflight_advertises_privacy_dry_run_availability(self) -> None:
        plan = build_provider_execution_plan(_config())

        self.assertTrue(plan["privacy_envelope_available"])
        self.assertTrue(plan["cache_write_dry_run_available"])
        self.assertFalse(plan["raw_payload_persistence"])

    def test_runtime_annotation_fixture_still_omits_future_provider_ids(self) -> None:
        annotation_card = load_json(SUCCESS_RESPONSE)["data"]["annotation_card"]
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

    def test_privacy_envelope_requires_no_external_services_or_secrets(self) -> None:
        envelope = build_provider_privacy_envelope(_provider_request(), _config())
        rendered = json.dumps(envelope, ensure_ascii=True).lower()

        for marker in ("http://", "https://", "api_key=", "bearer ", "sk-test"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, rendered)
        self.assertFalse(envelope["calls_external_services"])
        self.assertFalse(envelope["raw_provider_payload_persisted"])


def _provider_request():
    return build_provider_request(build_context_packet(load_json(VALID_EVENT)))


def _config() -> dict[str, object]:
    return load_config(EXAMPLE_CONFIG)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
