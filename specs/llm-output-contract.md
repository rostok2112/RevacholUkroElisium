# LLM Output Contract

All translation/annotation model calls must return strict JSON.

Runtime providers may include paid APIs or local OpenAI-compatible models when
the user explicitly configures them. Tests and CI must use deterministic mocks
only: no paid calls, no scraping, and no network access.

## Translation payload

```json
{
  "line_id": "synthetic.line.001",
  "translation_uk": "...",
  "literal_gloss": "...",
  "quick_note": "...",
  "deep_notes": [
    {"kind": "idiom", "text": "..."},
    {"kind": "reference", "text": "..."}
  ],
  "ukrainian_cultural_equivalents": ["..."],
  "glossary_terms": ["..."],
  "confidence": 0.0,
  "risk_flags": ["synthetic_low_context"],
  "needs_human_review": false
}
```

## Rules

- No Markdown in JSON fields unless explicitly requested.
- No invented lore.
- No future spoilers beyond `spoiler_budget`.
- Do not silently normalize Russianisms into Ukrainian.
- If uncertain, set `needs_human_review: true`.
- Web retrieval is an opt-in future runtime feature for lawful enrichment
  sources only. Do not use it for game script mirrors, fan dialogue databases,
  audio, images, screenshots, or localization tables.
- Runtime caches that may contain game text, model outputs, prompts, or
  web-derived material must stay under ignored private paths.
