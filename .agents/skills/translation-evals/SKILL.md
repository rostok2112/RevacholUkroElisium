---
name: translation-evals
description: Create and maintain translation quality evals, rubrics, golden sets, and regression checks.
---

# Translation Evals Skill

Use when adding evals, rubrics, QA checks, or test fixtures.

## Rules

- Public eval fixtures must be synthetic.
- Private local eval packs may reference extracted game content but must stay ignored.
- Evals should catch:
  - meaning errors,
  - lost voice,
  - Russianisms,
  - overlocalization,
  - spoiler leaks,
  - glossary inconsistencies,
  - too-long overlay text.

## Useful files

- `evals/README.md`
- `evals/rubrics/translation-quality-rubric.md`
- `evals/golden-set.synthetic.jsonl`
