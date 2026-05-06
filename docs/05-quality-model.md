# Quality Model

Quality is not "beautiful Ukrainian at any cost". Quality is contextual faithfulness with playable clarity.

## Score dimensions

Each output gets 1–5 scores:

1. **Semantic accuracy** — no meaning lost or invented.
2. **Voice preservation** — speaker/skill register survives.
3. **Context use** — branch, quest, and previous line context are respected.
4. **Ukrainian naturalness** — sounds like good Ukrainian, not calque.
5. **Literary density** — rhythm, irony, and texture preserved.
6. **Annotation usefulness** — explains only what matters.
7. **Spoiler safety** — no future reveals unless allowed.
8. **Terminology consistency** — names, skills, factions, recurring terms stable.
9. **Cultural adaptation discipline** — Ukrainian idioms used where functional, not decorative.
10. **Overlay brevity** — compact mode does not block gameplay.

## Automatic checks

- glossary violations,
- forbidden Russianisms,
- inconsistent recurring terms,
- hallucinated lore,
- too-long compact translation,
- missing annotation for detected idiom,
- spoiler leakage from future branch context.

## Human review tags

- `golden`: hand-approved.
- `needs-context`: model lacked branch/lore info.
- `too-literal`
- `too-free`
- `bad-voice`
- `ukrainianism-good`
- `ukrainianism-too-much`
- `russianism`
- `spoiler-risk`
