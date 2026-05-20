# Next Actions

After Milestone 4B:

1. Treat the BepInEx bridge as buildable only through the optional local helper when user-local
   BepInEx references are supplied.
2. Keep `check_all` independent of `dotnet`, BepInEx binaries, and any local game install.
3. Keep `MSB3277` warnings visible and counted; do not hide them unless a later runtime milestone
   deliberately pins/cleans references.
4. Keep the bridge localhost-only and fake-event-only until manual runtime logging is verified.
5. Do not begin current-line detection, game hooks, Unity object scanning, OCR, extraction, or
   decompiled-code research yet.
6. Keep Electron, Tauri, native always-on-top, global hotkey, clipboard, JavaScript shell, and
   production overlay work deferred.
7. Make the next milestone 4C: manual runtime smoke/log contract and synthetic event verification
   before any real game-state capture.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 4B. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/bepinex-bridge.md, packages/bepinex-plugin/README.md, packages/bepinex-plugin/DESIGN.md, and inspect packages/bepinex-plugin/src/, scripts/build_bepinex_bridge.py, scripts/check_bepinex_bridge_safety.py, tests/test_bepinex_bridge_build.py, and tests/test_bepinex_bridge_safety.py. Implement Milestone 4C: manual runtime smoke/log contract and synthetic event verification. Add a synthetic/manual runtime verification contract for the BepInEx bridge logs and companion interactions, including expected startup, health-check, unavailable-server, and optional synthetic-send log metadata. Keep it localhost-only and fake-event-only; do not add real game hooks, current-line detection, Unity object scanning, OCR, extraction, decompiled game code, provider calls, production overlay, keyboard hooks, clipboard writes, companion HTTP contract changes, downloads, or new heavy dependencies. Add docs/checks/tests where feasible and run the relevant validation suite.`
