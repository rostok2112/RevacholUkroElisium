# Next Actions

After Milestone 4N:

1. Treat the 4M counters as manually verifiable through the 4N smoke/report workflow only.
2. Keep local manual evidence redacted and under ignored workspace report paths.
3. Keep `metadata_snapshot_created_count`, `health_check_observed_count`, and
   `synthetic_send_configured_count` as metadata-only startup counters, not game-state evidence.
4. Keep text capture, current-line capture, UI text reading, Unity scanning, hooks, OCR, extraction,
   provider calls, and companion contract changes disallowed.
5. Do not add companion metadata payloads or new companion endpoints for the probe.
6. Do not commit completed real metadata probe reports, raw BepInEx/game logs, screenshots, private
   paths, payload dumps, save files, OCR output, stack traces, or real game text.
7. Use Milestone 4O to decide whether the redacted counter verification workflow is sufficient for
   a later metadata-only discussion milestone, still without runtime capture.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4N. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-metadata-only-extension-scope.md, docs/bepinex-metadata-probe-gate.md, docs/bepinex-bridge.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, scripts/check_bepinex_metadata_probe_report.py, scripts/review_bepinex_metadata_probe_report.py, tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json, tests/test_bepinex_metadata_probe_report.py, and tests/test_bepinex_metadata_probe_review.py. Implement Milestone 4O: metadata counter verification decision gate. Add docs/static-contract guidance that defines when a redacted local report containing the 4M counters is sufficient for discussion of a later metadata-only milestone, update report/review checks only if needed, keep all capture flags false, and do not add C# behavior, current-line capture, real text capture, UI text reading, Unity scanning, hooks, OCR, extraction, provider execution, companion HTTP contract changes, companion metadata payloads, committed logs, committed screenshots, committed real reports, downloads, or new dependencies.`
