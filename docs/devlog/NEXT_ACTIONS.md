# Next Actions

After Milestone 1E:

1. Implement Milestone 2A: provider abstraction and prompt pipeline skeleton.
2. Keep all provider calls mocked by default; do not call real LLMs, paid APIs, or web APIs in tests.
3. Add a provider interface that can later support cloud APIs and local models behind explicit config.
4. Add prompt/input/output contract scaffolding for synthetic context packets only.
5. Add deterministic mock provider outputs that still validate against annotation-card schema and existing quality/eval checks.
6. Keep real extraction, BepInEx, OCR, production overlay work, frontend frameworks, and real game assets out of tests and out of the public repo.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 1E. Read AGENTS.md, docs/devlog/*.md, docs/04-architecture.md, docs/05-quality-model.md, specs/llm-output-contract.md, specs/context-packet.schema.json, and specs/annotation-card.schema.json, then implement Milestone 2A: provider abstraction and prompt pipeline skeleton. Add a stdlib-only or dependency-light provider interface with a deterministic mock provider, prompt/input/output contract helpers for synthetic context packets, and tests proving no real LLMs, paid APIs, web APIs, extraction, OCR, BepInEx, or real game content are required. Keep runtime paid API/local model support as opt-in config only; tests must remain offline and synthetic. Ensure annotation output validates against existing schemas, synthetic evals still run, and python scripts/check_all.py, python scripts/validate_schemas.py, python -m unittest discover -s tests -p "test_*.py", npm run check, python scripts/run_companion_server.py --smoke-test, and python scripts/run_companion_client.py smoke-test pass.`
