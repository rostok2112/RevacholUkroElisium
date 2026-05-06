# AGENTS.md

You are working on **Revachol Ukrainian Companion**, a Codex-first project for building a high-quality Ukrainian context/translation companion for Disco Elysium.

## Mission

Build a context-first Ukrainian companion layer, not a cheap full replacement patch. The English original remains canonical. Ukrainian output must help the player understand meaning, tone, idiom, sarcasm, lore, and character voice.

## Non-negotiable priorities

1. Preserve gameplay flow and immersion.
2. Maximize contextual accuracy.
3. Avoid Russian-language dependencies and Russian cultural defaults.
4. Do not commit copyrighted game dialogue, audio, images, extracted databases, or proprietary assets.
5. Keep public repo data limited to schemas, tooling, prompts, tiny synthetic examples, and user-generated config.
6. Prefer reversible overlays and local extraction over destructive game-file replacement.
7. Add tests/evals for any translation pipeline behavior.
8. Keep prompts and design docs versioned.

## Architecture direction

Use a hybrid architecture:

- BepInEx plugin emits current dialogue state and local extraction metadata.
- Companion service builds context packets and calls pluggable translation/annotation engines.
- Overlay renders original text, Ukrainian translation, and click-to-expand explanations.
- Offline/local models are optional fallback; cloud APIs may be used for best quality.
- Scribe-like context browser is a design reference, but do not scrape/bundle copyrighted content into this repo.

## Coding rules

- Make small, reviewable PRs.
- Update docs/ADRs when architectural decisions change.
- Add tests for parsers, schemas, prompt contracts, and eval scoring.
- Never hard-code API keys or local game paths.
- Place generated/local/private game data under ignored directories only.
- Prefer explicit JSON schemas for inter-process contracts.

## Validation

Before finishing a code change, run the narrowest relevant checks. If checks cannot run, explain exactly why and what remains unvalidated.
