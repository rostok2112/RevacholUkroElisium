# Current Session Plan

Goal: implement Milestone 3G overlay static readability and accessibility review checks.

- Add a stdlib-only checker for fixture-rendered compact/deep/debug overlay HTML.
- Inspect rendered HTML with `html.parser`, not a browser or JavaScript runtime.
- Check language metadata, title, h1, heading flow, expected section ids, action hint visibility,
  compact brevity, deep grouping, debug metadata, and redaction.
- Keep the checker structural only; it is not WCAG certification, visual testing, or production
  overlay readiness.
- Integrate the checker into `scripts/check_all.py`.
- Add tests for passing modes and clear failures for missing metadata, bad heading flow, raw flags,
  game-title leakage, unescaped script tags, and excessive compact text.
- Update overlay docs and devlog handoff.
