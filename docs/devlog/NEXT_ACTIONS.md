# Next Actions

After Milestone 3H:

1. Treat overlay view-model fixtures, the Python validator, fixture-rendered review HTML, static
   readability checks, and transition previews as the current local overlay UX/state contract.
2. Run `python scripts/check_overlay_viewmodel_fixtures.py --quiet` before changing overlay
   view-model behavior.
3. Run `python scripts/check_overlay_review_accessibility.py --quiet` before accepting review HTML
   changes.
4. Run `python scripts/run_overlay_state_simulator.py --fixture compact --action switch_deep --quiet`
   before accepting action/visibility contract changes.
5. Keep compact/deep player-facing, Ukrainian, brief enough for reading flow, and free of raw flags,
   provider internals, and debug-only action metadata.
6. Keep transition previews side-effect-free: no clipboard writes, no keyboard hooks, no global
   hotkeys, no server calls, no provider calls, and no mutation of input view models.
7. Keep generated overlay HTML and transition summaries under ignored `workspace/synthetic-slice/`
   paths; do not commit generated HTML or transition output artifacts.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3H. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, and inspect scripts/local_overlay_prototype.py, scripts/overlay_actions.py, scripts/overlay_viewmodel_validator.py, scripts/overlay_state_simulator.py, scripts/run_overlay_state_simulator.py, scripts/check_overlay_viewmodel_fixtures.py, scripts/render_overlay_review.py, scripts/check_overlay_review_accessibility.py, tests/fixtures/overlay_prototype.compact.viewmodel.synthetic.json, tests/fixtures/overlay_prototype.deep.viewmodel.synthetic.json, tests/fixtures/overlay_prototype.debug.viewmodel.synthetic.json, tests/test_overlay_state_simulator.py, tests/test_overlay_viewmodel_validator.py, tests/test_overlay_viewmodel_fixtures.py, tests/test_overlay_review_renderer.py, and tests/test_overlay_review_accessibility.py. Implement Milestone 3I: overlay transition preview fixture regression pack. Add tiny committed synthetic JSON fixtures for representative allowed and blocked transition previews, add a stdlib-only checker/CLI to regenerate or compare current simulator output against those fixtures, validate no side effects or forbidden markers appear, wire the checker into check_all, update overlay docs/devlog, and run python scripts/check_all.py plus schemas, unittest, npm check, fixture checker, review renderer, accessibility checker, state simulator smoke, and local overlay self-test.`
