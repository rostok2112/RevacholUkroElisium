from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_extraction_indexing_5a_closeout import (
    COMPLETED_SAFE_FIELDS,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_CAPABILITY_FIELDS,
    NEXT_ACTIONS_PATH,
    RECOMMENDED_NEXT_STEP,
    SCHEMA_VERSION,
    SESSION_SUMMARY_PATH,
    collect_extraction_indexing_5a_closeout_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class ExtractionIndexing5ACloseoutTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_extraction_indexing_5a_closeout_errors())

    def test_fixture_shape_records_safe_closeout(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual(SCHEMA_VERSION, fixture["schema_version"])
        self.assertEqual("5A", fixture["milestone"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        for field in COMPLETED_SAFE_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], True)
        for field in FORBIDDEN_CAPABILITY_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_missing_safe_evidence(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in COMPLETED_SAFE_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = False

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_forbidden_capability_true(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in FORBIDDEN_CAPABILITY_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = True

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_next_step(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = dict(fixture)
        mutated["recommended_next_step"] = "real_extraction_implementation"

        self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_marker_values(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "real extraction approved",
            "current-line capture approved",
            "ui text reading approved",
            "unity scanning approved",
            "ocr approved",
            "raw payload dump",
            "LogOutput.log",
            "api_key=secret",
            "https://example.invalid",
            "C:\\Users\\local\\secret",
            "screenshot archive",
            "steamapps/common",
            "savegame.sav",
            "decompiled output",
        ):
            with self.subTest(marker=marker):
                mutated = dict(fixture)
                mutated["unsafe_note"] = marker

                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_fixture_checker_and_closeout(self) -> None:
        fixture_ref = "tests/fixtures/extraction_indexing_5a_closeout.synthetic.json"
        checker_ref = "scripts/check_extraction_indexing_5a_closeout.py"
        doc_ref = "docs/extraction-indexing-milestone-5a-closeout.md"

        for path in (DOC_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8").replace("\\", "/")
                self.assertIn(fixture_ref, text)
                self.assertIn(checker_ref, text)
                self.assertIn(doc_ref, text)

    def test_docs_do_not_approve_real_extraction_or_capture(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (DOC_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH)
        ).lower()

        self.assertNotIn("real extraction is approved", combined)
        self.assertNotIn("game file reads are approved", combined)
        self.assertNotIn("current-line capture is approved", combined)
        self.assertNotIn("ui text reading is approved", combined)
        self.assertNotIn("unity scanning is approved", combined)
        self.assertNotIn("ocr is approved", combined)
        self.assertNotIn("provider execution is approved", combined)
        self.assertIn("does not claim real extraction", combined)

    def test_check_all_registers_closeout_checker(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")

        self.assertIn("scripts/check_extraction_indexing_5a_closeout.py", text)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "extraction-indexing-5a-closeout.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_extraction_indexing_5a_closeout_errors(path)


if __name__ == "__main__":
    unittest.main()
