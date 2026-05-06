from pathlib import Path
import unittest

from scripts.schema_validator import collect_errors, load_json


ROOT = Path(__file__).resolve().parents[1]


class SchemaValidationTests(unittest.TestCase):
    def test_good_fixtures_validate(self) -> None:
        cases = [
            ("specs/context-packet.schema.json", "tests/fixtures/context_packet.synthetic.json"),
            ("specs/annotation-card.schema.json", "tests/fixtures/annotation_card.synthetic.json"),
            ("specs/glossary-entry.schema.json", "tests/fixtures/glossary_entry.synthetic.json"),
        ]
        for schema_path, fixture_path in cases:
            with self.subTest(fixture=fixture_path):
                errors = collect_errors(load_json(ROOT / fixture_path), load_json(ROOT / schema_path))
                self.assertEqual([], errors)

    def test_bad_fixtures_reject(self) -> None:
        cases = [
            ("specs/context-packet.schema.json", "tests/fixtures/context_packet.invalid.synthetic.json"),
            ("specs/annotation-card.schema.json", "tests/fixtures/annotation_card.invalid.synthetic.json"),
            ("specs/glossary-entry.schema.json", "tests/fixtures/glossary_entry.invalid.synthetic.json"),
        ]
        for schema_path, fixture_path in cases:
            with self.subTest(fixture=fixture_path):
                errors = collect_errors(load_json(ROOT / fixture_path), load_json(ROOT / schema_path))
                self.assertTrue(errors)

    def test_synthetic_e2e_parts_validate(self) -> None:
        fixture = load_json(ROOT / "tests/fixtures/synthetic_e2e_example.json")
        context_schema = load_json(ROOT / "specs/context-packet.schema.json")
        annotation_schema = load_json(ROOT / "specs/annotation-card.schema.json")

        self.assertEqual([], collect_errors(fixture["context_packet"], context_schema))
        self.assertEqual([], collect_errors(fixture["annotation_card"], annotation_schema))
        self.assertEqual(
            fixture["input"]["source_text"],
            fixture["context_packet"]["current_line"]["source_text"],
        )


if __name__ == "__main__":
    unittest.main()
