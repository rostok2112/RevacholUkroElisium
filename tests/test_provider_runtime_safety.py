from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

from scripts.provider_runtime_safety import (
    REDACTED_PATH,
    REDACTED_VALUE,
    ProviderRuntimeSafetyError,
    build_provider_execution_plan,
    inspect_provider_cache_root,
    redact_sensitive,
    validate_provider_cache_root,
)
from scripts.run_provider_preflight import DEFAULT_OUTPUT_ROOT, ROOT, resolve_output_path
from scripts.schema_validator import load_json
from scripts.validate_config import load_config


EXAMPLE_CONFIG = ROOT / "config/revachol.example.toml"
SUCCESS_RESPONSE = ROOT / "tests/fixtures/provider_annotate.success_response.synthetic.json"
FUTURE_PROVIDER_IDS = {
    "openai_compatible",
    "deepl_glossary",
    "local_model",
    "ensemble_reviewer",
}


class ProviderRuntimeSafetyTests(unittest.TestCase):
    def test_mock_preflight_passes_with_workspace_cache(self) -> None:
        plan = build_provider_execution_plan(load_config(EXAMPLE_CONFIG))

        self.assertTrue(plan["ok"])
        self.assertEqual("mock", plan["active_provider"])
        self.assertTrue(plan["provider_implemented"])
        self.assertTrue(plan["provider_enabled"])
        self.assertEqual("mock_offline_deterministic", plan["provider_mode"])
        self.assertFalse(plan["network_allowed"])
        self.assertFalse(plan["secrets_required"])
        self.assertFalse(plan["external_provider_allowed"])
        self.assertFalse(plan["local_runtime_required"])
        self.assertEqual("workspace/provider-cache", plan["cache_root"])
        self.assertTrue(plan["cache_root_is_private"])
        self.assertTrue(plan["cache_root_is_repo_ignored"])
        self.assertEqual("ukrainian_annotation_v1", plan["prompt_pack_id"])
        self.assertEqual("1.0.0", plan["prompt_pack_version"])
        self.assertTrue(plan["dry_run"])
        self.assertFalse(plan["calls_external_services"])
        self.assertEqual([], plan["blocked_reasons"])

    def test_unknown_provider_fails_clearly(self) -> None:
        with self.assertRaisesRegex(ProviderRuntimeSafetyError, "Unknown provider"):
            build_provider_execution_plan(load_config(EXAMPLE_CONFIG), provider_id="missing")

    def test_disabled_future_provider_blocks_before_external_call(self) -> None:
        plan = build_provider_execution_plan(
            load_config(EXAMPLE_CONFIG),
            provider_id="openai_compatible",
        )

        self.assertFalse(plan["ok"])
        self.assertIn("provider_disabled", plan["blocked_reasons"])
        self.assertIn("external_provider_not_allowed", plan["blocked_reasons"])
        self.assertIn("provider_unimplemented", plan["blocked_reasons"])
        self.assertFalse(plan["network_allowed"])
        self.assertFalse(plan["calls_external_services"])

    def test_enabled_future_provider_still_blocks_as_unimplemented(self) -> None:
        config = _load_temp_config(
            """
            [paths]
            game_install_path = ""
            local_workspace_path = "workspace"

            [translation]
            quality_mode = "maximum_quality"

            [overlay]
            default_mode = "minimal_hint"

            [llm]
            active_provider = "openai_compatible"
            allow_external_providers = true
            provider_cache_dir = "workspace/provider-cache"

            [llm.providers.mock]
            enabled = true

            [llm.providers.openai_compatible]
            enabled = true

            [network_enrichment]
            enabled = false
            lawful_opt_in_required = true
            cache_path = "workspace/network-cache"
            """
        )

        plan = build_provider_execution_plan(config, provider_id="openai_compatible")

        self.assertFalse(plan["ok"])
        self.assertNotIn("provider_disabled", plan["blocked_reasons"])
        self.assertNotIn("external_provider_not_allowed", plan["blocked_reasons"])
        self.assertIn("provider_unimplemented", plan["blocked_reasons"])
        self.assertTrue(plan["external_provider_allowed"])
        self.assertFalse(plan["network_allowed"])

    def test_external_provider_with_opt_in_disabled_blocks(self) -> None:
        config = _load_temp_config(
            """
            [paths]
            game_install_path = ""
            local_workspace_path = "workspace"

            [translation]
            quality_mode = "maximum_quality"

            [overlay]
            default_mode = "minimal_hint"

            [llm]
            active_provider = "openai_compatible"
            allow_external_providers = false
            provider_cache_dir = "workspace/provider-cache"

            [llm.providers.openai_compatible]
            enabled = true

            [network_enrichment]
            enabled = false
            lawful_opt_in_required = true
            cache_path = "workspace/network-cache"
            """
        )

        plan = build_provider_execution_plan(config, provider_id="openai_compatible")

        self.assertFalse(plan["ok"])
        self.assertIn("external_provider_not_allowed", plan["blocked_reasons"])
        self.assertFalse(plan["calls_external_services"])

    def test_workspace_provider_cache_root_is_allowed(self) -> None:
        status = validate_provider_cache_root("workspace/provider-cache")

        self.assertTrue(status["ok"])
        self.assertTrue(status["is_private"])
        self.assertTrue(status["is_repo_ignored"])
        self.assertEqual("workspace/provider-cache", status["display_path"])

    def test_unsafe_cache_root_is_rejected(self) -> None:
        status = inspect_provider_cache_root("docs/provider-cache")

        self.assertFalse(status["ok"])
        self.assertFalse(status["is_private"])
        self.assertIn("provider_cache_root_not_ignored_private_root", status["errors"])
        with self.assertRaisesRegex(ProviderRuntimeSafetyError, "provider_cache_root"):
            validate_provider_cache_root("docs/provider-cache")

    def test_absolute_private_path_is_redacted_in_plan_summary(self) -> None:
        config = _load_temp_config(
            """
            [paths]
            game_install_path = ""
            local_workspace_path = "workspace"

            [translation]
            quality_mode = "maximum_quality"

            [overlay]
            default_mode = "minimal_hint"

            [llm]
            active_provider = "mock"
            provider_cache_dir = "C:/Users/example/private/provider-cache"

            [llm.providers.mock]
            enabled = true

            [network_enrichment]
            enabled = false
            lawful_opt_in_required = true
            cache_path = "workspace/network-cache"
            """
        )

        plan = build_provider_execution_plan(config)

        self.assertTrue(plan["ok"])
        self.assertEqual(REDACTED_PATH, plan["cache_root"])
        self.assertEqual(REDACTED_PATH, plan["redacted_runtime_config"]["provider_cache_dir"])
        rendered = json.dumps(plan, ensure_ascii=True)
        self.assertNotIn("C:/Users/example", rendered)

    def test_output_path_allows_provider_preflight_workspace(self) -> None:
        output = resolve_output_path(
            Path("workspace/synthetic-slice/provider-preflight/summary-test.json")
        )

        self.assertTrue(_is_relative_to(output, DEFAULT_OUTPUT_ROOT))

    def test_output_path_rejects_public_repo_path(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_path(Path("docs/provider-preflight.json"))

    def test_redacts_secret_like_keys_and_values(self) -> None:
        payload = {
            "api_key": "sk-test-secret",
            "nested": {
                "bearer_token": "Bearer abc.def",
                "safe": "synthetic",
                "urlish": "api_key=inline",
            },
        }

        redacted = redact_sensitive(payload)

        self.assertEqual(REDACTED_VALUE, redacted["api_key"])
        self.assertEqual(REDACTED_VALUE, redacted["nested"]["bearer_token"])
        self.assertEqual(REDACTED_VALUE, redacted["nested"]["urlish"])
        self.assertEqual("synthetic", redacted["nested"]["safe"])

    def test_mock_preflight_summary_requires_no_real_runtime_markers(self) -> None:
        plan = build_provider_execution_plan(load_config(EXAMPLE_CONFIG))
        rendered = json.dumps(plan, ensure_ascii=True).lower()

        for marker in ("http://", "https://", "api_key=", "bearer ", "sk-test"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, rendered)

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

    def test_cli_mock_preflight_quiet_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_provider_preflight.py", "--quiet"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("passed", completed.stdout)

    def test_cli_future_provider_exits_nonzero_with_blocked_plan(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_preflight.py",
                "--provider",
                "openai_compatible",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        plan = json.loads(completed.stdout)
        self.assertFalse(plan["ok"])
        self.assertIn("provider_disabled", plan["blocked_reasons"])

    def test_cli_writes_only_to_safe_output_root(self) -> None:
        output = DEFAULT_OUTPUT_ROOT / "summary-test.json"
        if output.exists():
            output.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_preflight.py",
                "--output",
                "workspace/synthetic-slice/provider-preflight/summary-test.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertTrue(output.exists())
        written = json.loads(output.read_text(encoding="utf-8"))
        self.assertTrue(written["ok"])
        output.unlink()

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_preflight.py",
                "--output",
                "docs/provider-preflight.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)


def _load_temp_config(content: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "revachol.toml"
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return load_config(path)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
