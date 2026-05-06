---
name: disco-context-engine
description: Build and reason about spoiler-aware Disco Elysium context packets, dialogue graphs, line IDs, variables, and audio metadata.
---

# Disco Context Engine Skill

Use this skill when working on context retrieval, dialogue graph import, line matching, Scribe-like browsing, or spoiler-aware annotations.

## Instructions

1. Treat local extracted game data as private.
2. Do not commit extracted lines/assets.
3. Build context packets from:
   - current line,
   - speaker,
   - skill voice,
   - conversation,
   - location,
   - visible history,
   - nearby tree,
   - player options,
   - glossary hits,
   - spoiler budget.
4. Prefer exact line IDs over fuzzy text matching.
5. When fuzzy matching is needed, store confidence and alternatives.
6. Keep future branches out unless spoiler budget allows them.

## Useful files

- `specs/context-packet.schema.json`
- `docs/04-architecture.md`
- `docs/adr/0006-spoiler-aware-context-retrieval.md`
