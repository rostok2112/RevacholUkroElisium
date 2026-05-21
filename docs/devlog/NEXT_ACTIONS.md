# Next Actions

After Milestone 4F:

1. Use `scripts/review_bepinex_runtime_smoke_report.py` only on redacted reports under
   `workspace/synthetic-slice/bepinex-bridge/runtime-smoke/`.
2. Treat `ready_for_next_phase = true` as readiness to discuss a later metadata-only probe, not as
   approval for current-line capture.
3. Keep `check_all` independent of a real runtime report, `dotnet`, BepInEx binaries, and any local
   game install.
4. Keep raw BepInEx/game logs, screenshots, private paths, payload dumps, save files, OCR output,
   stack traces, and real runtime reports out of git.
5. If 4G scopes any probe work, keep it metadata-only, disabled by default, and limited to booleans,
   safe counters, synthetic event ids, bridge-generated line ids, and redacted reports.
6. Do not begin real text capture, game hooks, Harmony patches, Unity object scanning, OCR,
   extraction, decompiled integration, provider execution, or companion HTTP contract changes.
7. Keep Electron, Tauri, native always-on-top, global hotkey, clipboard, JavaScript shell, and
   production overlay work deferred.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4F. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/adr/0008-current-line-capture-research.md, docs/bepinex-bridge.md, docs/manual-smoke/bepinex-bridge-runtime-smoke.md, docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md, and inspect scripts/review_bepinex_runtime_smoke_report.py, scripts/check_bepinex_runtime_smoke_report.py, scripts/check_bepinex_bridge_safety.py, tests/test_bepinex_runtime_smoke_review.py, tests/test_bepinex_runtime_smoke_report.py, and tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json. Implement Milestone 4G: metadata-only bridge probe contract planning and safety gate. Add a docs/ADR or contract note plus optional static checker/tests for a future disabled-by-default probe that can emit only booleans, safe counters, synthetic event ids, and bridge-generated line ids. Do not implement real text capture, game hooks, Harmony patches, Unity object scanning, OCR, extraction, decompiled-code integration, provider execution, companion HTTP contract changes, shell work, keyboard hooks, clipboard writes, committed logs, committed screenshots, committed runtime reports, downloads, or new dependencies. Update docs/devlog and run the relevant validation suite.`
