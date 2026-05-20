# Next Actions

After Milestone 3J:

1. Treat overlay view-model fixtures, state-source fixtures, validator checks, review HTML checks,
   transition previews, and state-source results as the current local overlay UX/state contract.
2. Run `python scripts/check_overlay_state_source_fixtures.py --quiet` before changing
   state-source behavior.
3. Run `python scripts/check_overlay_viewmodel_fixtures.py --quiet` before changing overlay
   view-model behavior.
4. Run `python scripts/check_overlay_review_accessibility.py --quiet` before accepting review HTML
   changes.
5. Run `python scripts/run_overlay_state_simulator.py --fixture compact --action switch_deep --quiet`
   before accepting action/visibility contract changes.
6. Keep state-source and transition fixtures declarative: no polling loop, timer, background thread,
   provider call, companion HTTP contract change, UI side effect, clipboard write, or real game data.
7. Keep generated overlay HTML, transition summaries, and state-source summaries under ignored
   `workspace/synthetic-slice/` paths.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3J. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, and inspect scripts/overlay_state_simulator.py, scripts/run_overlay_state_simulator.py, scripts/check_overlay_state_source_fixtures.py, scripts/overlay_state_source.py, tests/test_overlay_state_simulator.py, tests/test_overlay_state_source_fixtures.py, and the committed overlay state-source fixtures. Implement Milestone 3K: overlay transition preview fixture regression pack. Add committed synthetic JSON fixtures for representative allowed and blocked transition previews, add a stdlib-only checker with --write and --quiet, validate no side effects or forbidden markers appear, wire it into check_all, update overlay docs/devlog, and run the full validation suite.`
