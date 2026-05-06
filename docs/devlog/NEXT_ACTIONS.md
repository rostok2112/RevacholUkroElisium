# Next Actions

After Milestone 1C:

1. Implement Milestone 1D as a minimal companion server skeleton using only synthetic events and deterministic mocks.
2. Reuse the existing fake event schema, synthetic slice, review renderer, and eval harness.
3. Add a local stdlib HTTP server or equivalent tiny server module with endpoints for health, synthetic event ingestion, latest context/annotation/overlay model, and synthetic eval summary.
4. Keep all server state in memory by default; optional outputs must stay under ignored `workspace/synthetic-slice/`.
5. Keep paid APIs, web retrieval, extraction, BepInEx, OCR, production overlay work, frontend frameworks, and real game assets out of tests and out of the public repo.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 1C. Read AGENTS.md and docs/devlog/*.md, then implement Milestone 1D: a stdlib-only companion server skeleton that accepts synthetic fake game events, runs the existing synthetic slice, exposes health/latest context/latest annotation/latest overlay demo/latest synthetic eval summary endpoints, and uses in-memory state by default. Do not call APIs, web services, LLMs, BepInEx, OCR, extraction, or use real game content. Do not add frontend frameworks or production overlay work. Add tests for endpoints and run python scripts/check_all.py plus npm run check.`
