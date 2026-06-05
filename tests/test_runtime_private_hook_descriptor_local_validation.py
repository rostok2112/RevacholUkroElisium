from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.run_runtime_private_hook_descriptor_local_validation import (
    DESCRIPTOR_ROOT,
    DESCRIPTOR_SCHEMA_VERSION,
    READY_NEXT_STEP,
    REPEAT_NEXT_STEP,
    REQUIRED_SAFETY_FALSE_FIELDS,
    SUMMARY_SCHEMA_VERSION,
    VALIDATION_ROOT,
    RuntimePrivateHookDescriptorValidationError,
    default_descriptor_template,
    ensure_safe_descriptor_path,
    ensure_safe_validation_output_path,
    main,
    run_self_test,
    validate_private_hook_descriptor,
)
from scripts.schema_validator import load_json
from scripts.synthetic_slice import ROOT


SUMMARY_FIXTURE = (
    ROOT / "tests/fixtures/runtime_private_hook_descriptor_local_validation_summary.synthetic.json"
)
CHECK_ALL = ROOT / "scripts/check_all.py"
PRIVATE_ALIAS = "PrivateCandidate.Controller"
PRIVATE_SIGNATURE = "private string BuildRuntimeLineCandidate()"
PRIVATE_CLASS = "PrivateRuntimeLineCandidate"


class RuntimePrivateHookDescriptorLocalValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        DESCRIPTOR_ROOT.mkdir(parents=True, exist_ok=True)
        self._workspace = Path(tempfile.mkdtemp(prefix="descriptor-test-", dir=DESCRIPTOR_ROOT))
        self.descriptor_path = self._workspace / "private-descriptor.json"

    def tearDown(self) -> None:
        shutil.rmtree(self._workspace, ignore_errors=True)

    def test_summary_fixture_is_valid_and_redacted(self) -> None:
        summary = load_json(SUMMARY_FIXTURE)

        self.assertEqual(SUMMARY_SCHEMA_VERSION, summary["schema_version"])
        self.assertEqual(READY_NEXT_STEP, summary["recommended_next_step"])
        self.assertEqual("compatible", summary["validation_status"])
        self.assertTrue(summary["descriptor_values_redacted"])
        self.assert_summary_redacted(summary)

    def test_valid_private_descriptor_summary_is_redacted(self) -> None:
        self.write_descriptor(_valid_descriptor())

        summary = validate_private_hook_descriptor(self.descriptor_path)

        self.assertEqual("compatible", summary["validation_status"])
        self.assertEqual(READY_NEXT_STEP, summary["recommended_next_step"])
        self.assertEqual(3, summary["candidate_top_level_field_count"])
        self.assert_summary_redacted(summary)

    def test_missing_or_wrong_fields_are_incompatible(self) -> None:
        descriptor = _valid_descriptor()
        del descriptor["candidate"]
        self.write_descriptor(descriptor)

        summary = validate_private_hook_descriptor(self.descriptor_path)

        self.assertEqual("incompatible", summary["validation_status"])
        self.assertIn("candidate_shape_invalid", summary["blocker_categories"])
        self.assertEqual(REPEAT_NEXT_STEP, summary["recommended_next_step"])

    def test_dangerous_safety_flags_are_blocked(self) -> None:
        descriptor = _valid_descriptor()
        descriptor["safety"]["provider_execution_enabled"] = True
        self.write_descriptor(descriptor)

        summary = validate_private_hook_descriptor(self.descriptor_path)

        self.assertEqual("incompatible", summary["validation_status"])
        self.assertIn("forbidden_capability_enabled", summary["blocker_categories"])
        self.assert_summary_redacted(summary)

    def test_unsafe_markers_are_blocked_without_leaking_values(self) -> None:
        descriptor = _valid_descriptor()
        descriptor["candidate"]["private_bad_note"] = "LogOutput.log provider payload source_text"
        self.write_descriptor(descriptor)

        summary = validate_private_hook_descriptor(self.descriptor_path)

        self.assertEqual("incompatible", summary["validation_status"])
        self.assertIn("unsafe_runtime_evidence_marker", summary["blocker_categories"])
        self.assert_summary_redacted(summary)

    def test_malformed_json_is_decode_failed_summary(self) -> None:
        self.descriptor_path.write_text("{", encoding="utf-8")

        summary = validate_private_hook_descriptor(self.descriptor_path)

        self.assertEqual("decode_failed", summary["validation_status"])
        self.assertIn("json_decode_failed", summary["blocker_categories"])
        self.assert_summary_redacted(summary)

    def test_unsafe_paths_are_rejected(self) -> None:
        with self.assertRaises(RuntimePrivateHookDescriptorValidationError):
            ensure_safe_descriptor_path(Path("docs/private-descriptor.json"), must_exist=False)
        with self.assertRaises(RuntimePrivateHookDescriptorValidationError):
            ensure_safe_descriptor_path(
                Path("workspace/local-private/runtime-capture/hook-descriptors/../x.json"),
                must_exist=False,
            )
        with self.assertRaises(RuntimePrivateHookDescriptorValidationError):
            ensure_safe_validation_output_path(Path("docs/validation.json"))

    def test_directory_and_symlink_are_rejected(self) -> None:
        with self.assertRaises(RuntimePrivateHookDescriptorValidationError):
            ensure_safe_descriptor_path(self._workspace, must_exist=True)

        target = self._workspace / "target.json"
        link = self._workspace / "link.json"
        target.write_text(json.dumps(_valid_descriptor()), encoding="utf-8")
        try:
            link.symlink_to(target)
        except OSError:
            self.skipTest("Symlinks are unavailable in this environment.")
        with self.assertRaises(RuntimePrivateHookDescriptorValidationError):
            ensure_safe_descriptor_path(link, must_exist=True)

    def test_template_writing_stays_private_and_is_redacted(self) -> None:
        template_path = self._workspace / "template.json"
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            self.assertEqual(0, main(["--write-template", str(template_path)]))

        self.assertTrue(template_path.exists())
        rendered_stdout = stdout.getvalue()
        self.assertNotIn(str(template_path), rendered_stdout)
        template = load_json(template_path)
        self.assertEqual(DESCRIPTOR_SCHEMA_VERSION, template["schema_version"])

    def test_cli_output_is_redacted_and_optional_output_is_private(self) -> None:
        self.write_descriptor(_valid_descriptor())
        output_path = VALIDATION_ROOT / f"{self._workspace.name}-summary.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        stdout = io.StringIO()

        try:
            with contextlib.redirect_stdout(stdout):
                result = main(
                    [
                        "--descriptor",
                        str(self.descriptor_path),
                        "--output",
                        str(output_path),
                    ]
                )
            self.assertEqual(0, result)
            self.assertTrue(output_path.exists())
            self.assert_summary_redacted(json.loads(stdout.getvalue()))
            self.assert_summary_redacted(load_json(output_path))
        finally:
            output_path.unlink(missing_ok=True)

    def test_quiet_cli_does_not_print_private_values(self) -> None:
        self.write_descriptor(_valid_descriptor())
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            self.assertEqual(0, main(["--descriptor", str(self.descriptor_path), "--quiet"]))

        self.assertIn("compatible", stdout.getvalue())
        self.assertNotIn(PRIVATE_ALIAS, stdout.getvalue())
        self.assertNotIn(PRIVATE_SIGNATURE, stdout.getvalue())

    def test_self_test(self) -> None:
        run_self_test()

    def test_check_all_registration(self) -> None:
        text = CHECK_ALL.read_text(encoding="utf-8")

        self.assertIn("scripts/run_runtime_private_hook_descriptor_local_validation.py", text)

    def write_descriptor(self, descriptor: dict[str, object]) -> None:
        self.descriptor_path.write_text(json.dumps(descriptor, indent=2), encoding="utf-8")

    def assert_summary_redacted(self, summary: dict[str, object]) -> None:
        rendered = json.dumps(summary, sort_keys=True)
        for marker in (
            PRIVATE_ALIAS,
            PRIVATE_SIGNATURE,
            PRIVATE_CLASS,
            str(DESCRIPTOR_ROOT),
            str(VALIDATION_ROOT),
            "private-descriptor.json",
            "LogOutput.log",
            "provider payload",
        ):
            self.assertNotIn(marker, rendered)
        for field in (
            "descriptor_path_included",
            "descriptor_filename_included",
            "candidate_identifiers_included",
            "method_names_included",
            "method_signatures_included",
            "source_text_included",
            "payload_dumps_included",
            "raw_logs_included",
            "screenshots_included",
            "provider_data_included",
            "private_paths_included",
        ):
            self.assertFalse(summary[field])


def _valid_descriptor() -> dict[str, object]:
    descriptor = default_descriptor_template()
    descriptor.update(
        {
            "research_review_passed": True,
            "candidate": {
                "private_candidate_alias": PRIVATE_ALIAS,
                "private_signature_hint": PRIVATE_SIGNATURE,
                "private_class_hint": PRIVATE_CLASS,
            },
            "recommended_next_step": READY_NEXT_STEP,
        }
    )
    descriptor["safety"] = {field: False for field in copy.deepcopy(REQUIRED_SAFETY_FALSE_FIELDS)}
    return descriptor


if __name__ == "__main__":
    unittest.main()
