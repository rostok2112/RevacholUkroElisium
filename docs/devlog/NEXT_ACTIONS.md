# Next Actions

After Milestone 4E:

1. Treat ADR 0008 as the current-line capture boundary: manual/synthetic bridge events remain the
   only implemented path.
2. Review any user-local runtime smoke evidence through redacted reports only; keep raw BepInEx/game
   logs, screenshots, private paths, payload dumps, save files, OCR output, and stack traces out of
   git.
3. Keep `check_all` independent of a real runtime report, `dotnet`, BepInEx binaries, and any local
   game install.
4. Do not begin game hooks, dialogue detection, Unity object scanning, OCR, extraction, decompiled
   integration, or real text capture in 4F.
5. If any later probe is scoped, require metadata-only local output first: booleans, safe counters,
   synthetic event ids, bridge-generated line ids, and redacted reports.
6. Keep Electron, Tauri, native always-on-top, global hotkey, clipboard, JavaScript shell, and
   production overlay work deferred.
7. Make the next milestone 4F: runtime smoke execution guide and local evidence review before any
   metadata-only current-line probe is approved.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4E. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/adr/0008-current-line-capture-research.md, docs/bepinex-bridge.md, docs/manual-smoke/bepinex-bridge-runtime-smoke.md, docs/manual-smoke/bepinex-bridge-log-contract.md, docs/manual-smoke/bepinex-bridge-runtime-smoke-report.md, packages/bepinex-plugin/README.md, packages/bepinex-plugin/DESIGN.md, and inspect scripts/check_bepinex_runtime_smoke_report.py, scripts/check_bepinex_bridge_safety.py, tests/test_bepinex_runtime_smoke_report.py, tests/test_bepinex_bridge_safety.py, and tests/fixtures/bepinex_bridge.runtime_smoke_report.synthetic.json. Implement Milestone 4F: runtime smoke execution guide and local evidence review. Add a docs/checker workflow for reviewing a user-supplied redacted runtime smoke report and producing a safe local readiness summary under ignored workspace paths. Keep 4F manual/synthetic and evidence-review only: no real text capture, no hooks, no Harmony patches, no Unity object scanning, no OCR, no extraction, no decompiled-code integration, no provider execution, no companion HTTP contract changes, no shell work, no keyboard hooks, no clipboard writes, no committed logs, no committed screenshots, no committed runtime reports, no downloads, and no new dependencies. Update docs/devlog and run the relevant validation suite.`
