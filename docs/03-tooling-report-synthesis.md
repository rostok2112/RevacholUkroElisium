# Tooling Report Synthesis

This file distills the previous research report into design decisions.

## Findings

### Official Ukrainian support

The game has official multilingual support, but not Ukrainian. Therefore a high-quality Ukrainian experience requires fan tooling or a custom companion.

### Existing Ukrainian AI translation

A Ukrainian mod exists, but it should be treated as a rough corpus or emergency fallback, not as the primary first-playthrough experience.

### LunaTranslator

Useful as a reference and fallback because it has hook/OCR modes, dictionary lookup, local pages, translation history, and API endpoints. Its `/page/manyinone` idea is especially close to the desired "original + history + dictionary" reading panel.

Design reuse:
- copy the concept of a combined reading/lookup panel,
- optionally integrate Luna as a fallback translator/dictionary service,
- do not rely on Luna as the core source of game-specific context.

### Game-Changing Translator / OCR overlays

Useful for visual seamlessness and on-source overlays. Less ideal as the core for Disco Elysium because the game is long-form, branch-heavy, and context-sensitive.

Design reuse:
- click-through overlay ideas,
- screen-region fallback for non-dialogue UI,
- not the primary source of truth.

### Disco Translator 2 / DiscoTranslatorFinalCut

Best foundation for a true game-specific pipeline because they work with actual game resources rather than screenshots.

Design reuse:
- local extraction of database,
- BepInEx plugin communication,
- `.transl`/PO-like editable translation assets,
- live reload concepts,
- potential audio extraction.

### DeepL API

Useful baseline and glossary tool, not sufficient alone. Glossary enforcement is valuable for names, skills, factions, recurring jokes, and political terms.

### Disco Elysium Scribe

Closest existing reference for "Genius for Disco": searchable dialogue trees, audio playback, variables, modifiers, bookmarks, and shareable line URLs.

Design reuse:
- dialogue tree browser,
- audio line playback,
- variable/modifier visibility,
- line IDs and bookmarks,
- spoiler controls.

## Design conclusion

The ideal custom solution is:

**BepInEx/Disco-specific extraction + local Scribe-like context graph + LLM/DeepL ensemble + Ukrainian localization style guide + transparent overlay.**
