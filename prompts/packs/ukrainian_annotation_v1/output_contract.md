# Output Contract

The provider output must normalize into `specs/annotation-card.schema.json`.

Required fields:
- `line_id`
- `original_english`
- `translation_uk`
- `concise_meaning_uk`
- `literary_rendering_uk`
- `literal_gloss`
- `quick_note`
- `explanation_uk`
- `character_voice_note_uk`
- `deep_notes`
- `ukrainian_cultural_equivalents`
- `glossary_terms`
- `confidence`
- `risk_flags`
- `quality`

Rules:
- `quick_note` must stay compact.
- `deep_notes` should use kinds such as `idiom`, `reference`, `sarcasm`, `politics`,
  `skill_voice`, `tone`, `cultural_equivalent`, or `translation_choice`.
- `confidence` is a number from 0 to 1.
- `risk_flags` must include clear reasons when output is synthetic, uncertain, low-context,
  spoiler-sensitive, or requires human review.
