# Next Actions

After Milestone 4M:

1. Treat the C# metadata probe extension as implemented but still disabled by default.
2. Verify any local manual run only through redacted metadata reports under ignored workspace paths.
3. Keep the new counters limited to `metadata_snapshot_created_count`,
   `health_check_observed_count`, and `synthetic_send_configured_count`.
4. Keep text capture, current-line capture, UI text reading, Unity scanning, hooks, OCR, extraction,
   provider calls, and companion contract changes disallowed.
5. Do not add companion metadata payloads or new companion endpoints for the probe.
6. Do not commit completed real metadata probe reports, raw BepInEx/game logs, screenshots, private
   paths, payload dumps, save files, OCR output, stack traces, or real game text.
7. Use Milestone 4N to align manual verification/report review around the 4M counters before any
   broader metadata-only extension is discussed.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4M. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-metadata-only-extension-scope.md, docs/bepinex-metadata-probe-gate.md, docs/bepinex-bridge.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, packages/bepinex-plugin/DESIGN.md, packages/bepinex-plugin/src/MetadataProbe.cs, scripts/check_bepinex_metadata_probe_report.py, scripts/review_bepinex_metadata_probe_report.py, tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json, and tests/test_bepinex_metadata_probe_review.py. Implement Milestone 4N: metadata-only extension manual verification and report/review alignment. Update the manual smoke workflow, report template/checker, review helper, fixtures, tests, and docs so the 4M inert counters are clearly reported and reviewed, still without runtime capture, UI text reading, Unity scanning, hooks, OCR, extraction, provider execution, companion HTTP contract changes, companion metadata payloads, committed logs, committed screenshots, committed real reports, downloads, or new dependencies.`
