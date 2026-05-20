# Next Actions

After Milestone 3I:

1. Treat overlay view-model fixtures, validator checks, review HTML checks, transition previews, and
   state-source results as the current local overlay UX/state contract.
2. Run `python scripts/check_overlay_viewmodel_fixtures.py --quiet` before changing overlay
   view-model behavior.
3. Run `python scripts/check_overlay_review_accessibility.py --quiet` before accepting review HTML
   changes.
4. Run `python scripts/run_overlay_state_simulator.py --fixture compact --action switch_deep --quiet`
   before accepting action/visibility contract changes.
5. Run `python scripts/run_overlay_state_source.py --self-test --quiet` before accepting
   state-source/client handoff changes.
6. Keep state-source results declarative: no real polling loop, timer, background thread, provider
   call, companion HTTP contract change, UI side effect, or clipboard write.
7. Keep generated overlay HTML, transition summaries, and state-source summaries under ignored
   `workspace/synthetic-slice/` paths.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3I. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, and inspect scripts/local_overlay_prototype.py, scripts/overlay_actions.py, scripts/overlay_viewmodel_validator.py, scripts/overlay_state_simulator.py, scripts/overlay_state_source.py, scripts/run_overlay_state_source.py, scripts/check_overlay_viewmodel_fixtures.py, scripts/render_overlay_review.py, scripts/check_overlay_review_accessibility.py, tests/test_overlay_state_source.py, tests/test_overlay_state_simulator.py, tests/test_overlay_viewmodel_validator.py, tests/test_overlay_viewmodel_fixtures.py, tests/test_overlay_review_renderer.py, and tests/test_overlay_review_accessibility.py. Implement Milestone 3J: overlay state-source fixture regression pack. Add tiny committed synthetic JSON fixtures for ready, no_provider_state, stale, and error state-source results, add a stdlib-only checker/CLI to regenerate or compare current state-source output against those fixtures, validate no side effects or forbidden markers appear, wire the checker into check_all, update overlay docs/devlog, and run python scripts/check_all.py plus schemas, unittest, npm check, fixture checker, review renderer, accessibility checker, state simulator smoke, state-source smoke, and local overlay self-test.`
