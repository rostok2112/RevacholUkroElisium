from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.prompt_pack import (
    DEFAULT_PACK_ID,
    DEFAULT_PACKS_ROOT,
    REQUIRED_POLICY_KEYS,
    PromptPackError,
    load_prompt_pack,
)
from scripts.synthetic_slice import ROOT


class PromptPackTests(unittest.TestCase):
    def test_prompt_pack_metadata_loads(self) -> None:
        pack = load_prompt_pack()

        self.assertEqual(DEFAULT_PACK_ID, pack.metadata.pack_id)
        self.assertEqual("1.0.0", pack.metadata.version)
        self.assertEqual("uk", pack.metadata.language)
        self.assertIn("translation_uk", pack.metadata.required_output_fields)
        self.assertIn("avoid_russianisms", pack.metadata.quality_priorities)
        self.assertEqual(set(REQUIRED_POLICY_KEYS), set(pack.metadata.policy_files))

    def test_all_required_markdown_files_load(self) -> None:
        pack = load_prompt_pack()

        for key in REQUIRED_POLICY_KEYS:
            with self.subTest(policy=key):
                self.assertIn(key, pack.policy_texts)
                self.assertGreater(len(pack.policy_texts[key].strip()), 20)
        self.assertIn("Synthetic Examples", pack.synthetic_examples)

    def test_missing_required_file_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            shutil.copytree(DEFAULT_PACKS_ROOT / DEFAULT_PACK_ID, temp_root / DEFAULT_PACK_ID)
            (temp_root / DEFAULT_PACK_ID / "style_guide.md").unlink()

            with self.assertRaisesRegex(PromptPackError, "style_guide.md"):
                load_prompt_pack(DEFAULT_PACK_ID, packs_root=temp_root)

    def test_malformed_metadata_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pack_dir = Path(temp_dir) / DEFAULT_PACK_ID
            pack_dir.mkdir()
            (pack_dir / "pack.json").write_text('{"pack_id": "ukrainian_annotation_v1"}')

            with self.assertRaisesRegex(PromptPackError, "missing required key"):
                load_prompt_pack(DEFAULT_PACK_ID, packs_root=Path(temp_dir))

    def test_prompt_pack_loading_is_deterministic(self) -> None:
        first = load_prompt_pack()
        second = load_prompt_pack()

        self.assertEqual(first.summary(), second.summary())
        self.assertEqual(first.sections_for_provider(), second.sections_for_provider())

    def test_prompt_pack_examples_are_synthetic_only(self) -> None:
        pack = load_prompt_pack()
        payload = json.dumps(
            {
                "summary": pack.summary(),
                "sections": pack.sections_for_provider(),
            },
            ensure_ascii=False,
        ).lower()

        self.assertIn("synthetic", payload)
        forbidden_markers = [
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
            "disco elysium dialogue",
        ]
        for marker in forbidden_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, payload)

    def test_synthetic_examples_keep_required_structure(self) -> None:
        examples = load_prompt_pack().synthetic_examples
        headings = list(re.finditer(r"^## \d+\. .+$", examples, flags=re.MULTILINE))
        required_fields = [
            "1. Source",
            "2. What makes it difficult",
            "3. Bad literal or bad over-localized rendering",
            "4. Good concise Ukrainian meaning",
            "5. Good literary Ukrainian rendering",
            "6. Deep annotation",
            "7. Tone / character voice note",
            "8. Risk flags if relevant",
            "9. Why this is better",
        ]

        self.assertGreaterEqual(len(headings), 10)
        for index, heading in enumerate(headings):
            next_start = headings[index + 1].start() if index + 1 < len(headings) else len(examples)
            block = examples[heading.start() : next_start]
            for field in required_fields:
                with self.subTest(example=heading.group(), field=field):
                    self.assertIn(field, block)
            field_sections = re.split(
                r"\n(?=\d+\. (?:Source|What makes it difficult|Bad literal or bad over-localized rendering|"
                r"Good concise Ukrainian meaning|Good literary Ukrainian rendering|Deep annotation|"
                r"Tone / character voice note|Risk flags if relevant|Why this is better)\n)",
                block,
            )
            self.assertGreaterEqual(len(field_sections), len(required_fields))
            for section in field_sections[1:]:
                label, _, body = section.partition("\n")
                with self.subTest(example=heading.group(), field_body=label):
                    self.assertGreater(len(body.strip()), 20)

            ukrainian_fields = [
                "Good concise Ukrainian meaning",
                "Good literary Ukrainian rendering",
            ]
            for field in ukrainian_fields:
                pattern = rf"{re.escape(field)}\n\n(?P<body>.*?)(?=\n\d+\.|\Z)"
                match = re.search(pattern, block, flags=re.DOTALL)
                with self.subTest(example=heading.group(), ukrainian_field=field):
                    self.assertIsNotNone(match)
                    self.assertRegex(match.group("body"), r"[А-Яа-яІіЇїЄєҐґ]")

    def test_player_facing_annotations_default_to_ukrainian_policy_exists(self) -> None:
        developer_policy = load_prompt_pack().policy_texts["developer"]

        self.assertIn("player-facing", developer_policy)
        self.assertIn("must default to Ukrainian", developer_policy)
        self.assertIn("debug or developer mode", developer_policy)

    def test_prompt_pack_cli_summary(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/run_prompt_pack.py", "--summary"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        summary = json.loads(completed.stdout)
        self.assertEqual(DEFAULT_PACK_ID, summary["pack_id"])
        self.assertEqual(len(REQUIRED_POLICY_KEYS), summary["loaded_policy_count"])


if __name__ == "__main__":
    unittest.main()
