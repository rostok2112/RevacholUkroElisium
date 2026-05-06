---
name: prompt-contracts
description: Design schema-bound prompts, model adapters, JSON contracts, retries, and validation.
---

# Prompt Contracts Skill

Use for LLM call design.

## Rules

- Production prompts must return strict JSON.
- Validate output against schemas.
- Keep prompts model-agnostic.
- Add deterministic mocks for tests.
- Include uncertainty fields.
- Never let prompt output bypass glossary/safety checks.

## Useful files

- `specs/llm-output-contract.md`
- `specs/annotation-card.schema.json`
- `prompts/system/`
