# Next Actions

After Milestone 1A:

1. Implement Milestone 1B as a small synthetic presentation/review loop, not a production overlay.
2. Reuse `scripts/synthetic_slice.py` and the fake event schema instead of restarting the pipeline.
3. Add a minimal static overlay/demo renderer or review artifact for compact/deep modes under ignored `workspace/synthetic-slice/`.
4. Add tests that assert the rendered demo exposes original text, Ukrainian translation fields, annotation sections, risk flags, and glossary terms.
5. Keep paid APIs, web retrieval, extraction, BepInEx, OCR, and real game assets out of tests and out of the public repo.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 1A. Read AGENTS.md and docs/devlog/*.md, then implement Milestone 1B: a minimal synthetic overlay/review demo renderer that consumes the existing overlay_demo model from scripts/synthetic_slice.py and writes only ignored workspace artifacts. Do not call APIs, web services, BepInEx, OCR, or extraction. Use only synthetic fixtures, add tests for compact/deep presentation fields, and run python scripts/check_all.py plus npm run check.`
