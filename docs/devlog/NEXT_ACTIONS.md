# Next Actions

After Milestone 4G:

1. Treat `docs/bepinex-metadata-probe-gate.md` as the boundary for any future metadata-only bridge
   probe.
2. Validate only synthetic or redacted metadata probe reports with
   `scripts/check_bepinex_metadata_probe_report.py`.
3. Keep optional local metadata probe reports under
   `workspace/synthetic-slice/bepinex-bridge/metadata-probe/`.
4. Do not treat a valid metadata probe report as approval for text capture; it only proves the report
   stayed metadata-only.
5. Require a separate approved milestone before adding any probe code.
6. Keep raw BepInEx/game logs, screenshots, private paths, payload dumps, save files, OCR output,
   stack traces, real runtime reports, and real metadata probe reports out of git.
7. Keep Electron, Tauri, native always-on-top, global hotkey, clipboard, JavaScript shell, and
   production overlay work deferred.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4G. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-metadata-probe-gate.md, docs/adr/0008-current-line-capture-research.md, docs/bepinex-bridge.md, docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md, and inspect scripts/check_bepinex_metadata_probe_report.py, scripts/check_bepinex_bridge_safety.py, tests/test_bepinex_metadata_probe_report.py, tests/test_bepinex_bridge_safety.py, and tests/fixtures/bepinex_bridge.metadata_probe_report.synthetic.json. Implement Milestone 4H: disabled metadata-only bridge probe design handoff. Decide whether to add a disabled-by-default metadata probe stub or keep it docs-only based on available redacted runtime smoke evidence. If code is added, it may emit only booleans, safe counters, synthetic ids, safe status/error codes, current_line_capture_enabled=false, and real_text_captured=false. Do not implement real text capture, dialogue detection, game hooks, Harmony patches, Unity object scanning, OCR, extraction, decompiled-code integration, provider execution, companion HTTP contract changes, shell work, keyboard hooks, clipboard writes, committed logs, committed screenshots, committed real reports, downloads, or new dependencies. Update docs/devlog and run the relevant validation suite.`
