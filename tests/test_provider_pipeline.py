from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import unittest

from scripts.provider_pipeline import (
    MOCK_PROVIDER_METADATA,
    QUALITY_PRIORITIES,
    REQUESTED_OUTPUT_FIELDS,
    MockAnnotationProvider,
    ProviderPipelineError,
    ProviderResponse,
    build_provider_request,
    normalize_provider_response,
    run_provider_pipeline,
)
from scripts.run_provider_pipeline import ROOT, resolve_output_path
from scripts.schema_validator import collect_errors, load_json
from scripts.synthetic_slice import ANNOTATION_CARD_SCHEMA, build_context_packet


VALID_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"


class ProviderPipelineTests(unittest.TestCase):
    def test_provider_request_includes_context_and_priorities(self) -> None:
        context_packet = _context_packet()
        request = build_provider_request(context_packet)

        self.assertEqual("mock", request.provider_name)
        self.assertEqual(context_packet["packet_id"], request.context_packet_id)
        self.assertEqual(
            context_packet["current_line"]["source_text"],
            request.original_english,
        )
        self.assertEqual(context_packet["current_line"]["speaker"], request.speaker)
        self.assertEqual(context_packet["current_line"]["location"], request.scene_id)
        self.assertEqual(context_packet["spoiler_budget"], request.spoiler_budget)
        self.assertIn("committee", request.glossary_hints)
        self.assertIn("translation_uk", request.requested_output_fields)
        self.assertEqual(REQUESTED_OUTPUT_FIELDS, request.requested_output_fields)
        self.assertEqual(QUALITY_PRIORITIES, request.quality_priorities)
        self.assertEqual(1, len(request.visible_history))
        self.assertEqual(1, len(request.player_options))

    def test_mock_provider_response_is_deterministic(self) -> None:
        request = build_provider_request(_context_packet())
        provider = MockAnnotationProvider()

        first = provider.annotate(request)
        second = provider.annotate(request)

        self.assertEqual(first, second)
        self.assertTrue(first.metadata.offline)
        self.assertFalse(first.metadata.requires_api_key)
        self.assertEqual(request.line_id, first.line_id)
        self.assertIn("deterministic_mock_provider", first.output["risk_flags"])

    def test_output_parser_produces_valid_annotation_card(self) -> None:
        context_packet = _context_packet()
        card = run_provider_pipeline(context_packet)

        self.assertEqual(
            context_packet["current_line"]["source_text"],
            card["original_english"],
        )
        self.assertEqual(
            context_packet["current_line"]["source_text"],
            card["source_text"],
        )
        self.assertIn("translation_uk", card)
        self.assertIn("concise_meaning_uk", card)
        self.assertIn("literary_rendering_uk", card)
        self.assertIn("explanation_uk", card)
        self.assertIn("character_voice_note_uk", card)
        self.assertIn("committee", card["glossary_terms"])
        self.assertIn("deterministic_mock_provider", card["risk_flags"])
        self.assertEqual([], collect_errors(card, load_json(ANNOTATION_CARD_SCHEMA)))

    def test_normalizer_preserves_original_even_if_provider_echo_differs(self) -> None:
        context_packet = _context_packet()
        request = build_provider_request(context_packet)
        response = MockAnnotationProvider().annotate(request)
        response.output["original_english"] = "Synthetic provider tried to change this."

        card = normalize_provider_response(context_packet, response)

        self.assertEqual(
            context_packet["current_line"]["source_text"],
            card["original_english"],
        )

    def test_malformed_provider_output_fails_clearly(self) -> None:
        context_packet = _context_packet()
        request = build_provider_request(context_packet)
        response = ProviderResponse(
            metadata=MOCK_PROVIDER_METADATA,
            request_id=request.request_id,
            line_id=request.line_id,
            output={"line_id": request.line_id},
        )

        with self.assertRaisesRegex(ProviderPipelineError, "translation_uk"):
            normalize_provider_response(context_packet, response)

    def test_line_id_mismatch_fails_clearly(self) -> None:
        context_packet = _context_packet()
        request = build_provider_request(context_packet)
        response = MockAnnotationProvider().annotate(request)
        response = ProviderResponse(
            metadata=response.metadata,
            request_id=response.request_id,
            line_id="synthetic.wrong.line",
            output=response.output,
        )

        with self.assertRaisesRegex(ProviderPipelineError, "line_id"):
            normalize_provider_response(context_packet, response)

    def test_pipeline_requires_no_private_paths_network_or_secrets(self) -> None:
        request = build_provider_request(_context_packet())
        response = MockAnnotationProvider().annotate(request)
        payload = json.dumps(
            {
                "request": request.to_dict(),
                "response": response.to_dict(),
                "card": run_provider_pipeline(_context_packet()),
            },
            ensure_ascii=True,
        ).lower()

        forbidden = [
            "data/extracted",
            "data/local",
            ".local-game",
            "private-data",
            "llm-cache",
            "http://",
            "https://",
            "steamapps",
            "openai_api_key",
            "deepl_api_key",
            "anthropic_api_key",
        ]
        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, payload)

    def test_output_path_allows_workspace_synthetic_slice(self) -> None:
        output = resolve_output_path(Path("workspace/synthetic-slice/provider-output-test.json"))

        self.assertTrue(_is_relative_to(output, ROOT / "workspace/synthetic-slice"))

    def test_output_path_rejects_public_repo_path(self) -> None:
        with self.assertRaises(ValueError):
            resolve_output_path(Path("docs/provider-output.json"))

    def test_cli_mock_provider_run_writes_workspace_output(self) -> None:
        output = ROOT / "workspace/synthetic-slice/provider-output-test.json"
        if output.exists():
            output.unlink()

        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_pipeline.py",
                "--output",
                "workspace/synthetic-slice/provider-output-test.json",
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
        self.assertEqual(
            _context_packet()["current_line"]["source_text"],
            written["original_english"],
        )
        output.unlink()

    def test_cli_rejects_unsafe_output_path(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/run_provider_pipeline.py",
                "--output",
                "docs/provider-output.json",
                "--quiet",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, completed.returncode)
        self.assertIn("Unsafe output path", completed.stderr)


def _context_packet() -> dict[str, object]:
    return build_context_packet(load_json(VALID_EVENT))


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    unittest.main()
