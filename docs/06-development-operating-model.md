# Codex-first Development Operating Model

## Principle

Codex should be able to pick up any issue, read `AGENTS.md`, load the relevant skill/design doc, implement a small slice, run checks, and leave a reviewable PR.

## Task shape

Good task:

> Implement `ContextPacket` validation for imported dialogue lines. Use `specs/context-packet.schema.json`, add tests, and update `docs/04-architecture.md` if the schema changes.

Bad task:

> Make the project better.

## Required context in issues

Every implementation issue should include:

- target package,
- relevant design docs,
- acceptance criteria,
- forbidden shortcuts,
- test command,
- sample input/output,
- whether copyrighted/local extracted data is needed.

## Agent routing

- Architecture changes → `architecture-guardian`
- BepInEx work → `bepinex-mod-engineer`
- Overlay work → `overlay-ux-engineer`
- Translation output → `ukrainian-localization-editor`
- Eval changes → `translation-eval-engineer`
- Prompt changes → `prompt-contract-engineer`
- Legal/data handling → `copyright-safety-reviewer`

## PR expectations

- Small diff.
- Design links.
- Tests/evals updated.
- No local game data committed.
- Screenshots/gifs for overlay changes when possible.
