# Next Actions

After Milestone 0:

1. Implement Milestone 1 synthetic vertical slice.
2. Add a fake game event object that produces a context packet from synthetic input only.
3. Add a deterministic mock annotation engine that emits `AnnotationCard` JSON without API or network calls.
4. Add an overlay mock using the synthetic e2e fixture.
5. Keep paid APIs and web retrieval behind opt-in runtime config.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 0. Read AGENTS.md and docs/devlog/*.md, then implement Milestone 1 synthetic vertical slice: fake game event -> context packet -> deterministic mock annotation card -> overlay mock. Keep paid APIs and web retrieval behind opt-in config, use only synthetic fixtures in tests, and run python scripts/check_all.py.`
