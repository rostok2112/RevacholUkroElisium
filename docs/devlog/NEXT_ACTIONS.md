# Next Actions

After Milestone 3F:

1. Treat the Python validator plus the three committed overlay view-model JSON fixtures as the
   current overlay UX contract, including visibility state and declarative actions.
2. Keep overlay actions declarative only. Do not add key bindings, keyboard hooks, clipboard effects,
   always-on-top behavior, or a live overlay shell without a new milestone.
3. Run `python scripts/check_overlay_viewmodel_fixtures.py --quiet` before changing overlay
   view-model behavior.
4. Regenerate overlay view-model fixtures only with
   `python scripts/check_overlay_viewmodel_fixtures.py --write`, and review the JSON diff
   intentionally.
5. Use `python scripts/render_overlay_review.py --quiet` to regenerate local HTML review artifacts
   from validated fixtures.
6. Keep compact/deep modes player-facing and Ukrainian by default; raw provider flags, provider
   internals, and debug-only actions belong in debug mode only.
7. Keep generated overlay HTML under ignored `workspace/synthetic-slice/overlay-prototype/review/`;
   do not commit generated HTML snapshots.
8. Future overlay clients should consume validated JSON view models, not parse generated review HTML.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3F. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, and inspect scripts/local_overlay_prototype.py, scripts/overlay_actions.py, scripts/overlay_viewmodel_validator.py, scripts/check_overlay_viewmodel_fixtures.py, scripts/render_overlay_review.py, tests/fixtures/overlay_prototype.compact.viewmodel.synthetic.json, tests/fixtures/overlay_prototype.deep.viewmodel.synthetic.json, tests/fixtures/overlay_prototype.debug.viewmodel.synthetic.json, tests/test_local_overlay_prototype.py, tests/test_overlay_viewmodel_validator.py, tests/test_overlay_viewmodel_fixtures.py, and tests/test_overlay_review_renderer.py. Implement Milestone 3G: overlay static readability and accessibility review checks. Add stdlib-only checks for fixture-rendered compact/deep/debug HTML structure, language metadata, heading order, action hint visibility, compact-mode brevity, player/debug separation, escaping, and generated-output safety. Keep generated HTML uncommitted, no frontend framework, no JavaScript, no production overlay, no keyboard hooks, no companion HTTP contract changes, no BepInEx/OCR/extraction, no web/API/LLM/provider calls, update docs/devlog, and run python scripts/check_all.py plus schemas, unittest, npm check, fixture checker, review renderer, and local overlay self-test.`
