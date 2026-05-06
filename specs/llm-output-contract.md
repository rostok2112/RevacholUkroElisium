# LLM Output Contract

All translation/annotation model calls must return strict JSON.

## Translation payload

```json
{
  "line_id": "synthetic.line.001",
  "translation_uk": "…",
  "literal_gloss": "…",
  "quick_note": "…",
  "deep_notes": [
    {"kind": "idiom", "text": "…"}
  ],
  "ukrainian_cultural_equivalents": ["…"],
  "glossary_terms": ["…"],
  "confidence": 0.0,
  "needs_human_review": false
}
```

## Rules

- No Markdown in JSON fields unless explicitly requested.
- No invented lore.
- No future spoilers beyond `spoiler_budget`.
- Do not silently normalize Russianisms into Ukrainian.
- If uncertain, set `needs_human_review: true`.
