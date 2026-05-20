# Next Actions

After Milestone 3K:

1. Treat the 3.x overlay JSON fixtures, state-source fixtures, transition previews, review HTML, and
   readability checks as the current overlay contract.
2. Do not start Electron, Tauri, native always-on-top, global hotkey, clipboard, JavaScript shell, or
   production overlay work yet.
3. Move the next coding phase to Milestone 4A: a synthetic/manual BepInEx bridge skeleton.
4. Keep 4A bridge work non-destructive and synthetic first: companion `/health`, manual synthetic
   fake event send, safe logging, and graceful unavailable-server behavior.
5. Do not extract real game dialogue, commit decompiled game code, bundle assets, run OCR, call
   providers, or change the companion HTTP contract in 4A.
6. Keep generated overlay artifacts and bridge test output under ignored workspace paths.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3K. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/adr/0007-overlay-shell-path.md, docs/api/companion-server-contract.md, docs/09-legal-and-data-safety.md, and inspect the repository for existing package/build layout. Implement Milestone 4A: BepInEx bridge skeleton. Add a minimal C# BepInEx plugin skeleton that can be built or at least statically reviewed, uses a configurable localhost companion URL, performs a companion /health check, and can manually send a synthetic fake event to the existing companion server contract. Keep it synthetic/manual only: no real game text extraction, no decompiled game code, no copyrighted assets, no OCR, no provider calls, no production overlay, no keyboard hooks, no clipboard writes, no companion HTTP contract changes, and no new dependencies unless clearly justified. Add docs for manual install/build path, safe logging, unavailable-server behavior, tests or build stub if feasible, update devlog, and run the relevant validation suite.`
