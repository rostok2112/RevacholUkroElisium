from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.run_runtime_current_line_smoke import (
    OUTPUT_ROOT,
    RuntimeCurrentLineSmokeError,
    resolve_output_path,
    run_smoke,
    write_summary,
)
from scripts.synthetic_slice import ROOT


class RuntimeCurrentLineSmokeTests(unittest.TestCase):
    def test_smoke_summary_is_redacted(self) -> None:
        summary = run_smoke()

        self.assertTrue(summary["runtime_current_line_endpoint_available"])
        self.assertTrue(summary["event_received"])
        self.assertTrue(summary["translation_memory_checked"])
        self.assertFalse(summary["provider_called"])
        rendered = json.dumps(summary, sort_keys=True)
        self.assertNotIn("Invented runtime smoke line", rendered)
        self.assertNotIn("synthetic.runtime.smoke.001", rendered)

    def test_output_path_must_stay_private(self) -> None:
        with self.assertRaises(RuntimeCurrentLineSmokeError):
            resolve_output_path(Path("docs/runtime-smoke.json"))

    def test_writes_private_redacted_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir) / "repo"
            summary = run_smoke(root=root)
            output = resolve_output_path(Path(OUTPUT_ROOT) / "summary.json", root=root)
            write_summary(summary, output)

            rendered = output.read_text(encoding="utf-8")
            self.assertNotIn("Invented runtime smoke line", rendered)
            self.assertTrue(output.exists())

    def test_check_all_registration(self) -> None:
        text = (ROOT / "scripts/check_all.py").read_text(encoding="utf-8")
        self.assertIn("scripts/run_runtime_current_line_smoke.py", text)


if __name__ == "__main__":
    unittest.main()
