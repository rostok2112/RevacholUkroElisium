# Current Session Plan

Goal: implement Milestone 3F overlay interaction state and action contract.

- Add a stdlib-only declarative action catalog for compact/deep/debug overlay view models.
- Add mode-specific visibility state and action lists to committed overlay JSON fixtures.
- Keep compact/deep player-facing, Ukrainian, and free of raw debug/provider metadata.
- Keep debug developer-facing, redacted, and allowed to expose the full declarative action catalog.
- Extend the overlay view-model validator for visibility state, known action ids, Ukrainian labels and
  hints, debug-only action separation, and no key-binding fields.
- Render action hints in static review HTML without JavaScript, keyboard hooks, or a live overlay
  shell.
- Update docs/devlog and run the full local validation suite.
