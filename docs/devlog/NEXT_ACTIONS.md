# Next Actions

After Milestone 4I:

1. Keep `MetadataProbeEnabled=false` and `MetadataProbeLogOnStart=false` as source defaults.
2. Use `docs/manual-smoke/bepinex-metadata-probe-smoke.md` only for user-local manual observation of
   the disabled metadata probe.
3. Generate optional blank report templates with
   `scripts/write_bepinex_metadata_probe_report.py`; keep completed reports under
   `workspace/synthetic-slice/bepinex-bridge/metadata-probe/`.
4. Validate only synthetic or redacted metadata probe reports with
   `scripts/check_bepinex_metadata_probe_report.py`.
5. Do not commit completed real metadata probe reports, raw BepInEx/game logs, screenshots, private
   paths, payload dumps, save files, OCR output, stack traces, or real game text.
6. Treat a valid metadata probe report as evidence that the report stayed metadata-only, not as
   approval for current-line capture.
7. Keep current-line capture, UI text reading, game hooks, Harmony patches, Unity object scanning,
   OCR, extraction, provider execution, companion HTTP changes, and shell work out of the bridge.
8. Defer metadata probe report readiness review to Milestone 4J.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4I. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-metadata-probe-gate.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, docs/bepinex-bridge.md, packages/bepinex-plugin/README.md, packages/bepinex-plugin/DESIGN.md, and inspect scripts/check_bepinex_metadata_probe_report.py, scripts/write_bepinex_metadata_probe_report.py, scripts/check_bepinex_bridge_safety.py, tests/test_bepinex_metadata_probe_report.py, tests/test_bepinex_bridge_safety.py, packages/bepinex-plugin/src/MetadataProbe.cs, and tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json. Implement Milestone 4J: metadata probe report review/readiness helper. Add a stdlib-only reviewer for redacted local metadata probe reports under workspace/synthetic-slice/bepinex-bridge/metadata-probe/, produce a redacted readiness summary without reading logs/game files/screenshots/companion/provider state, write optional review artifacts only under ignored workspace review paths, keep readiness as discussion-only and not approval for text capture, update docs/tests/devlog, and run the full validation suite. Do not implement real text capture, dialogue detection, game hooks, Harmony patches, Unity object scanning, UI text reading, OCR, extraction, decompiled-code integration, provider execution, companion HTTP contract changes, shell work, keyboard hooks, clipboard writes, committed logs, committed screenshots, committed real reports, downloads, or new dependencies.`
