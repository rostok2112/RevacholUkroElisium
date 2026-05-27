from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_overlay_refresh_readiness_contract import (
    BEPINEX_DOC,
    DOC_PATH,
    FIXTURE_PATH,
    FORBIDDEN_PERMISSION_FIELDS,
    OVERLAY_DOC,
    READINESS_STATES,
    RECOMMENDED_NEXT_STEP,
    collect_overlay_refresh_readiness_contract_errors,
)
from scripts.schema_validator import load_json


ROOT = Path(__file__).resolve().parents[1]


class OverlayRefreshReadinessContractTests(unittest.TestCase):
    def test_fixture_validates(self) -> None:
        self.assertEqual([], collect_overlay_refresh_readiness_contract_errors())

    def test_fixture_shape_is_metadata_only(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        self.assertEqual("overlay-refresh-readiness-contract.v1", fixture["schema_version"])
        self.assertTrue(fixture["bridge_to_overlay_smoke_passed"])
        self.assertTrue(fixture["metadata_only"])
        self.assertEqual(RECOMMENDED_NEXT_STEP, fixture["recommended_next_step"])
        self.assertEqual(list(READINESS_STATES), fixture["readiness_states"])
        self.assertIn("companion_health_status", fixture["allowed_metadata_inputs"])
        self.assertIn("overlay_view_model_validation_status", fixture["allowed_metadata_inputs"])
        self.assertIn("accessibility_validation_status", fixture["allowed_metadata_inputs"])

    def test_fixture_keeps_dangerous_permissions_false(self) -> None:
        fixture = load_json(FIXTURE_PATH)

        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                self.assertIs(fixture[field], False)

    def test_rejects_unknown_or_missing_readiness_states(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = dict(fixture)
        mutated["readiness_states"] = list(READINESS_STATES) + ["capturing"]

        self.assertNotEqual([], _errors_for(mutated))

        mutated = dict(fixture)
        mutated["readiness_states"] = list(READINESS_STATES[:-1])

        self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_metadata_only_false(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        mutated = dict(fixture)
        mutated["metadata_only"] = False

        self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_forbidden_permissions_true(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for field in FORBIDDEN_PERMISSION_FIELDS:
            with self.subTest(field=field):
                mutated = dict(fixture)
                mutated[field] = True

                self.assertNotEqual([], _errors_for(mutated))

    def test_rejects_unsafe_markers(self) -> None:
        fixture = load_json(FIXTURE_PATH)
        for marker in (
            "raw_provider_payload_dump",
            "C:\\Users\\local\\secret",
            "api_key=secret",
            "https://example.invalid",
            "current-line capture approved",
        ):
            with self.subTest(marker=marker):
                mutated = dict(fixture)
                mutated["allowed_metadata_inputs"] = list(fixture["allowed_metadata_inputs"]) + [
                    marker
                ]

                self.assertNotEqual([], _errors_for(mutated))

    def test_docs_link_fixture_and_checker(self) -> None:
        fixture_ref = "tests/fixtures/overlay_refresh_readiness_contract.synthetic.json"
        checker_ref = "scripts/check_overlay_refresh_readiness_contract.py"

        for path in (DOC_PATH, OVERLAY_DOC, BEPINEX_DOC):
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn(fixture_ref, text)
                self.assertIn(checker_ref, text)

    def test_docs_do_not_approve_capture(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in (DOC_PATH, OVERLAY_DOC, BEPINEX_DOC)
        ).lower()

        self.assertNotIn("current-line capture is approved", combined)
        self.assertNotIn("real text capture is approved", combined)
        self.assertIn("does not implement polling", combined)
        self.assertIn("does not approve current-line capture", combined)


def _errors_for(payload: dict[str, object]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "overlay-refresh-readiness.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return collect_overlay_refresh_readiness_contract_errors(path)


if __name__ == "__main__":
    unittest.main()
