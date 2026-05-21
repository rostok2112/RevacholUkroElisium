# Next Actions

After Milestone 4J:

1. Review only redacted metadata probe reports with
   `scripts/review_bepinex_metadata_probe_report.py`.
2. Keep completed metadata probe reports and review artifacts under
   `workspace/synthetic-slice/bepinex-bridge/metadata-probe/`.
3. Treat `readiness_status = "ready"` as discussion-only. It does not approve current-line capture,
   UI text reading, real text capture, hooks, OCR, extraction, provider execution, or companion
   contract changes.
4. Keep `MetadataProbeEnabled=false` and `MetadataProbeLogOnStart=false` as source defaults.
5. Do not commit completed real metadata probe reports, raw BepInEx/game logs, screenshots, private
   paths, payload dumps, save files, OCR output, stack traces, or real game text.
6. Keep `scripts/check_all.py` independent of any real metadata probe report.
7. Use Milestone 4K to decide whether a reviewed metadata-only report is sufficient to scope a later
   extension, still without capture or runtime inspection.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4J. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-metadata-probe-gate.md, docs/manual-smoke/bepinex-metadata-probe-smoke.md, docs/adr/0008-current-line-capture-research.md, docs/bepinex-bridge.md, packages/bepinex-plugin/README.md, packages/bepinex-plugin/DESIGN.md, and inspect scripts/review_bepinex_metadata_probe_report.py, scripts/check_bepinex_metadata_probe_report.py, scripts/check_bepinex_bridge_safety.py, tests/test_bepinex_metadata_probe_review.py, tests/test_bepinex_metadata_probe_report.py, packages/bepinex-plugin/src/MetadataProbe.cs, and tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json. Implement Milestone 4K: metadata-only probe extension decision gate. Decide and document whether a reviewed metadata probe report is sufficient to scope a later metadata-only extension, define the exact allowed extension shape if approved for planning, keep current-line capture and real text capture forbidden, update safety docs/tests/devlog, and run the full validation suite. Do not implement capture, dialogue detection, game hooks, Harmony patches, Unity object scanning, UI text reading, OCR, extraction, decompiled-code integration, provider execution, companion HTTP contract changes, shell work, keyboard hooks, clipboard writes, committed logs, committed screenshots, committed real reports, downloads, or new dependencies.`
