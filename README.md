# Revachol Ukrainian Companion

**Codex-first vibe-coding project for a context-first Ukrainian companion layer for Disco Elysium: The Final Cut.**

This repository is not a finished mod. It is a maintainable design/development scaffold for building one:
a BepInEx-based game bridge, a local context engine, a high-quality translation/annotation pipeline,
and an in-game/always-on-top overlay that behaves more like a "Genius for Disco Elysium" than a raw OCR translator.

## North Star

Preserve the English original as the canonical text, then add Ukrainian understanding where it helps:
translation, idiom decoding, subtext, sarcasm, skill-voice interpretation, lore context, and optional Ukrainian cultural resonance.

This project optimizes for:

1. **Context correctness over literal speed.**
2. **Original-first playthrough over full text replacement.**
3. **Annotation on demand over noisy over-explanation.**
4. **Repeatable evaluation over vibes-only prompt tweaking.**
5. **No Russian dependency.**
6. **No copyrighted game text/assets in the public repository.**

## Proposed Stack

- Game bridge: BepInEx IL2CPP plugin, starting from lessons in Disco Translator 2 / DiscoTranslatorFinalCut.
- Local service: TypeScript or Python service with WebSocket ingestion, SQLite/Postgres, vector retrieval, and task queue.
- Overlay: Tauri/React or native Windows overlay, always-on-top, transparent/click-through modes.
- Translation engines: pluggable adapters for DeepL glossary baseline, top-tier LLM APIs, and local OpenAI-compatible models.
- Context source: user's local extracted game database/audio only; repository stores schemas and tooling, not copyrighted data.
- Quality: golden-set evals, back-translation checks, terminology consistency, regression tests, and human review UI.

## First Implementation Milestone

Build a vertical slice for one early-game conversation:

1. Extract the game dialogue database locally.
2. Detect current dialogue node in-game.
3. Build a context packet with speaker, line, branch neighbors, skill voice, location, variables, and recent player choices.
4. Generate Ukrainian translation + short annotation.
5. Display it in the overlay without alt-tabbing.
6. Score it with the eval rubric and save the translation memory entry.

## Repository Map

- `AGENTS.md` — short, high-priority instructions for Codex and other coding agents.
- `docs/` — product, architecture, ADRs, research synthesis, legal notes.
- `specs/` — machine-readable contracts and schemas.
- `.agents/skills/` — Codex/open Agent Skills.
- `.claude/agents/` and `.claude/skills/` — Claude Code compatible subagents and skills.
- `prompts/` — LLM prompt contracts and examples.
- `packages/` — intended code packages.
- `evals/` — quality rubrics and golden-set examples.
- `data/` — non-copyrighted seed glossaries and style rules.
- `tasks/` — milestones and issue seeds.
