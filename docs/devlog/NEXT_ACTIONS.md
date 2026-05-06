# Next Actions

After Milestone 2B:

1. Implement Milestone 2C: provider pipeline uses prompt pack in mock annotation flow and structural evals.
2. Make the deterministic mock provider derive more of its response metadata/risk flags from the loaded prompt pack.
3. Add provider-pipeline structural eval checks without real model calls.
4. Consider a low-risk companion server/client provider endpoint only if the provider contract remains stable.
5. Keep the richer `synthetic_examples.md` structure intact; tests now require all numbered examples to include the full review field set with non-empty bodies and Ukrainian concise/literary fields.
6. Keep all tests offline, deterministic, synthetic-only, and free of real game content or provider calls.

Exact resume prompt:

`Continue in revachol-ukro-elisium after Milestone 2B. Read AGENTS.md, docs/devlog/*.md, docs/05-quality-model.md, specs/llm-output-contract.md, scripts/prompt_pack.py, scripts/provider_pipeline.py, prompts/packs/ukrainian_annotation_v1/pack.json, and tests/test_prompt_pack.py, then implement Milestone 2C: provider pipeline uses prompt pack in mock annotation flow and structural evals. Make the deterministic mock provider consume prompt-pack metadata/policies for risk flags, quality priorities, and debug/provider metadata; add structural eval checks proving prompt-pack compatibility, policy presence, spoiler discipline, Russianism/overlocalization rules, and annotation-card validity. Do not call real LLMs, paid APIs, web APIs, DeepL, local model runtimes, OCR, extraction, BepInEx, or use real game content. Keep all examples synthetic. Run python scripts/check_all.py, python scripts/validate_schemas.py, python -m unittest discover -s tests -p "test_*.py", npm run check, python scripts/run_companion_server.py --smoke-test, python scripts/run_companion_client.py smoke-test, python scripts/run_prompt_pack.py --summary, and python scripts/run_provider_pipeline.py --output workspace/synthetic-slice/provider-output.json --quiet.`
