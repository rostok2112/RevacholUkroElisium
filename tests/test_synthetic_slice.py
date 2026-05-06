from pathlib import Path
import json
import unittest

from scripts.schema_validator import SchemaValidationError, collect_errors, load_json
from scripts.synthetic_slice import (
    ANNOTATION_CARD_SCHEMA,
    CONTEXT_PACKET_SCHEMA,
    build_context_packet,
    build_mock_annotation_card,
    build_overlay_demo_model,
    run_synthetic_slice,
    validate_fake_game_event,
)


ROOT = Path(__file__).resolve().parents[1]
VALID_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
INVALID_EVENT = ROOT / "tests/fixtures/fake_game_event.invalid.synthetic.json"


class SyntheticSliceTests(unittest.TestCase):
    def test_fake_event_validation_accepts_synthetic_fixture(self) -> None:
        validate_fake_game_event(load_json(VALID_EVENT))

    def test_fake_event_validation_rejects_bad_fixture(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_fake_game_event(load_json(INVALID_EVENT))

    def test_context_packet_builder_preserves_original_and_validates(self) -> None:
        event = load_json(VALID_EVENT)
        packet = build_context_packet(event)

        self.assertEqual(event["raw_english_text"], packet["current_line"]["source_text"])
        self.assertEqual(event["synthetic_line_id"], packet["current_line"]["line_id"])
        self.assertEqual("none", packet["spoiler_budget"])
        self.assertEqual(["synthetic_fake_game_event"], packet["retrieval"]["sources"])
        self.assertEqual(1, len(packet["visible_history"]))
        self.assertEqual(1, len(packet["player_options"]))
        self.assertIn("committee", packet["glossary_hits"])

        errors = collect_errors(packet, load_json(CONTEXT_PACKET_SCHEMA))
        self.assertEqual([], errors)

    def test_mock_annotation_is_deterministic_and_schema_valid(self) -> None:
        packet = build_context_packet(load_json(VALID_EVENT))
        first = build_mock_annotation_card(packet)
        second = build_mock_annotation_card(packet)

        self.assertEqual(first, second)
        self.assertEqual(packet["current_line"]["source_text"], first["original_english"])
        self.assertEqual(first["translation_uk"], first["literary_rendering_uk"])
        self.assertIn("concise_meaning_uk", first)
        self.assertIn("explanation_uk", first)
        self.assertIn("character_voice_note_uk", first)
        self.assertIn("deterministic_mock_pipeline", first["risk_flags"])
        self.assertIn("committee", first["glossary_terms"])
        self.assertEqual(
            {"idiom", "reference", "skill_voice", "translation_choice"},
            {note["kind"] for note in first["deep_notes"]},
        )

        errors = collect_errors(first, load_json(ANNOTATION_CARD_SCHEMA))
        self.assertEqual([], errors)

    def test_overlay_demo_model_exposes_compact_and_deep_modes(self) -> None:
        packet = build_context_packet(load_json(VALID_EVENT))
        card = build_mock_annotation_card(packet)
        overlay = build_overlay_demo_model(packet, card)

        self.assertEqual("overlay-demo.v1", overlay["schema_version"])
        self.assertEqual(packet["current_line"]["source_text"], overlay["source"]["original_english"])
        self.assertTrue(overlay["toggles"]["show_original"])
        self.assertTrue(overlay["toggles"]["show_translation"])
        self.assertIn("compact", overlay["modes"])
        self.assertIn("deep_explanation", overlay["modes"])
        self.assertTrue(overlay["modes"]["compact"]["annotation_available"])
        self.assertGreaterEqual(len(overlay["modes"]["deep_explanation"]["sections"]), 4)

    def test_full_synthetic_vertical_slice(self) -> None:
        result = run_synthetic_slice(load_json(VALID_EVENT))

        self.assertEqual(
            result["fake_game_event"]["raw_english_text"],
            result["context_packet"]["current_line"]["source_text"],
        )
        self.assertEqual(
            result["context_packet"]["current_line"]["source_text"],
            result["annotation_card"]["original_english"],
        )
        self.assertEqual(
            result["annotation_card"]["translation_uk"],
            result["overlay_demo"]["modes"]["compact"]["translation_uk"],
        )

    def test_slice_requires_no_real_or_private_paths(self) -> None:
        result = run_synthetic_slice(load_json(VALID_EVENT))
        payload = json.dumps(result, ensure_ascii=True)

        forbidden_path_markers = [
            "data/extracted",
            "data/local",
            ".local-game",
            "private-data",
            "llm-cache",
            "http://",
            "https://",
        ]
        for marker in forbidden_path_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, payload)


if __name__ == "__main__":
    unittest.main()
