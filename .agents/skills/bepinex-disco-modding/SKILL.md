---
name: bepinex-disco-modding
description: Work on the BepInEx/Unity/IL2CPP game bridge and extraction concepts without bundling proprietary content.
---

# BepInEx Disco Modding Skill

Use for C# plugin work, Unity/IL2CPP integration, game event emission, and extraction hooks.

## Rules

- The plugin observes and emits game state; it should not call translation APIs.
- Keep the first milestone non-destructive: no full text replacement.
- Use localhost communication to the companion service.
- Keep debug logs explicit.
- Do not commit game binaries, extracted databases, audio, or images.

## Design targets

- Detect current dialogue line.
- Emit line metadata.
- Support debug console.
- Support future audio reference mapping.
- Support future live reload if needed.

## Useful files

- `packages/bepinex-plugin/DESIGN.md`
- `docs/adr/0001-use-game-specific-context-over-ocr-first-translation.md`
