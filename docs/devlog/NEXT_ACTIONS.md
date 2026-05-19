# Next Actions

After Milestone 3G:

1. Treat the Python validator, committed overlay JSON fixtures, fixture-rendered review HTML, and the
   static readability checker as the current local overlay UX contract.
2. Run `python scripts/check_overlay_viewmodel_fixtures.py --quiet` before changing overlay
   view-model behavior.
3. Run `python scripts/check_overlay_review_accessibility.py --quiet` before accepting review HTML
   changes.
4. Keep compact/deep player-facing, Ukrainian, brief enough for reading flow, and free of raw flags,
   provider internals, and debug-only action metadata.
5. Keep debug developer-facing and redacted. It may show raw mock flags, provider metadata, prompt
   pack metadata, privacy/cache dry-run details, and declarative actions.
6. Keep generated overlay HTML under ignored `workspace/synthetic-slice/overlay-prototype/review/`;
   do not commit generated HTML snapshots.
7. The 3G checker is structural only. Do not treat it as browser testing, visual regression testing,
   real accessibility certification, or production overlay readiness.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 3G. First inspect git status, read AGENTS.md, docs/devlog/*.md, docs/overlay-prototype.md, docs/08-overlay-ux.md, and inspect scripts/local_overlay_prototype.py, scripts/overlay_actions.py, scripts/overlay_viewmodel_validator.py, scripts/check_overlay_viewmodel_fixtures.py, scripts/render_overlay_review.py, scripts/check_overlay_review_accessibility.py, tests/fixtures/overlay_prototype.compact.viewmodel.synthetic.json, tests/fixtures/overlay_prototype.deep.viewmodel.synthetic.json, tests/fixtures/overlay_prototype.debug.viewmodel.synthetic.json, tests/test_local_overlay_prototype.py, tests/test_overlay_viewmodel_validator.py, tests/test_overlay_viewmodel_fixtures.py, tests/test_overlay_review_renderer.py, and tests/test_overlay_review_accessibility.py. Implement Milestone 3H: declarative overlay action/state transition simulator. Add stdlib-only simulation helpers that consume validated overlay view models and action ids, produce next mode/visibility previews for switch/toggle/hide/copy actions without side effects, validate impossible or debug-only actions fail clearly in player modes, keep clipboard/keyboard/global hooks unimplemented, render optional fixture-based transition summaries if useful, update docs/devlog, and run python scripts/check_all.py plus schemas, unittest, npm check, fixture checker, review renderer, accessibility checker, and local overlay self-test.`
