# Next Actions

After Milestone 1B:

1. Implement Milestone 1C as a small synthetic quality/eval harness for the existing fake-event -> context -> annotation -> review flow.
2. Reuse `scripts/synthetic_slice.py` and `scripts/synthetic_review_renderer.py`; do not restart or replace them.
3. Add a tiny synthetic scenario pack or inline cases that exercise overlay brevity, glossary presence, risk flags, spoiler safety defaults, and annotation section coverage.
4. Emit deterministic eval output to stdout by default, with optional writes only under ignored `workspace/synthetic-slice/`.
5. Keep paid APIs, web retrieval, extraction, BepInEx, OCR, production overlay work, and real game assets out of tests and out of the public repo.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 1B. Read AGENTS.md and docs/devlog/*.md, then implement Milestone 1C: a stdlib-only synthetic quality/eval harness for the existing synthetic slice and review renderer. It should run multiple invented synthetic cases or checks, score overlay brevity/section coverage/glossary presence/risk flags/spoiler safety defaults, write optional outputs only under workspace/synthetic-slice/, add tests, and run python scripts/check_all.py plus npm run check. Do not call APIs, web services, LLMs, BepInEx, OCR, extraction, or use real game content.`
