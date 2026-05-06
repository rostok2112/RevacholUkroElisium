# ADR 0001: Use game-specific context over OCR-first translation

## Status

Accepted.

## Context

OCR translation is easy to prototype, but Disco Elysium is dialogue-tree-heavy and context-sensitive. OCR sees text pixels; it does not naturally know branch structure, speaker history, skill checks, variables, or audio identity.

## Decision

Build the core around local game extraction and a BepInEx bridge. OCR remains fallback only.

## Consequences

Pros:
- better context,
- lower hallucination risk,
- richer annotations,
- line-level translation memory,
- less repetitive API usage.

Cons:
- harder setup,
- game-version fragility,
- BepInEx/IL2CPP complexity.
