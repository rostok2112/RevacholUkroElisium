# ADR 0007: Defer real overlay shell and build the bridge skeleton next

## Status

Accepted.

## Context

Milestones 3A through 3J produced a local overlay contract without implementing a real shell:

- mode-specific overlay view-model fixtures,
- Python contract validators,
- fixture-backed HTML review output,
- structural readability checks,
- declarative action transition previews,
- state-source results and regression fixtures.

These artifacts are enough to let future clients understand the overlay payload shape. The largest
remaining uncertainty is not how to render a static card, but whether a safe game bridge can detect
and emit the current dialogue state without committing proprietary content or destabilizing play.

Building a polished shell before proving that bridge path risks optimizing the wrong UX.

## Options Considered

### A. Keep static HTML review artifacts only

- Enables: continued review of compact, deep, and debug output without runtime UI work.
- Complexity: low.
- Dependencies: none beyond current stdlib tooling.
- Integration risk: low.
- Safety/privacy: strong, because artifacts are synthetic and generated under ignored workspace
  paths.
- Fit: excellent fit with the current stdlib-first contract.
- Defer: live state polling, window behavior, focus, input handling, and player-facing shell polish.

### B. Local browser page consuming the companion server

- Enables: a closer prototype of a live overlay surface using the existing localhost contract.
- Complexity: medium.
- Dependencies: browser runtime and likely JavaScript.
- Integration risk: medium, because live rendering can blur the line between review artifact and
  real UI.
- Safety/privacy: must avoid raw prompts, extracted content, external assets, and accidental logging.
- Fit: possible later, but beyond the current stdlib-only contract.
- Defer: until bridge event shape and update cadence are better understood.

### C. Companion-served local web page

- Enables: one local process can expose both state and a simple UI page.
- Complexity: medium.
- Dependencies: server-side routing and static asset policy.
- Integration risk: medium, because companion service responsibilities expand.
- Safety/privacy: needs careful separation between debug data and player-facing data.
- Fit: moderate, but it would widen companion scope before bridge feasibility is proven.
- Defer: until a real shell need justifies a served page.

### D. Electron shell

- Enables: a desktop shell with packaged web UI, window controls, and eventual always-on-top work.
- Complexity: high.
- Dependencies: Node/Electron stack.
- Integration risk: high, especially around packaging, updates, focus, hotkeys, and native window
  behavior.
- Safety/privacy: larger dependency surface and more places to leak debug or provider data.
- Fit: poor for the current stdlib-first phase.
- Defer: until the bridge proves live state capture and a web shell is clearly the right UX.

### E. Tauri shell

- Enables: a lighter desktop shell than Electron with native window capabilities.
- Complexity: high.
- Dependencies: Rust/Tauri toolchain and web UI surface.
- Integration risk: high for a project that has not yet proven bridge data flow.
- Safety/privacy: smaller than Electron in some ways, but still a real shell with native concerns.
- Fit: poor for the current phase.
- Defer: until shell requirements are stable.

### F. Native overlay or always-on-top later

- Enables: best eventual fit for an in-game companion surface if placement, focus, and input handling
  are solved.
- Complexity: very high.
- Dependencies: platform-specific UI and windowing behavior.
- Integration risk: very high.
- Safety/privacy: must be carefully isolated from provider logs, raw prompts, and local game data.
- Fit: not appropriate before game-state capture is proven.
- Defer: until after bridge, state cadence, and player workflow are understood.

### G. Skip shell for now and build a BepInEx bridge skeleton

- Enables: tests the biggest unknown first: whether a local bridge can communicate safely with the
  companion service.
- Complexity: medium.
- Dependencies: C# project structure and BepInEx references, but no real extraction yet.
- Integration risk: bounded if the first milestone is synthetic/manual only.
- Safety/privacy: acceptable if it sends only invented synthetic fake events and never commits
  extracted text, decompiled code, binaries, screenshots, audio, or assets.
- Fit: best next step, because the current overlay contract is already strong enough for handoff.
- Defer: real current-line detection, real extraction, hotkeys, clipboard, always-on-top behavior,
  and production shell UX.

## Decision

Use option G for the next coding phase.

Near term:

- Keep static JSON and HTML overlay review workflows as the current contract.
- Do not implement Electron, Tauri, native always-on-top UI, global hotkeys, clipboard writes, or a
  production overlay shell yet.
- Make Milestone 4A a BepInEx bridge skeleton.
- The 4A bridge must initially emit manual or synthetic events to the companion server, not real
  extracted game content.
- The bridge must not require the companion server to be available for the game to run.

The 3.x overlay contract is sufficiently complete for now because it already has:

- committed view-model fixtures,
- committed state-source fixtures,
- validators and regression checkers,
- player/debug separation,
- static review output,
- readability guardrails,
- transition previews,
- no-side-effect state-source results.

The next architectural risk is game-state capture. Proving that path should come before investing in
shell polish.

## Milestone 4A Readiness Checklist

Milestone 4A should include:

- C# BepInEx plugin skeleton.
- Configurable localhost companion URL, defaulting to the current companion server base URL.
- Companion `/health` check.
- Manual or synthetic fake event send to the existing companion server contract.
- Safe logging for health, send success, send failure, and disabled/unavailable companion states.
- Graceful behavior when the companion server is unavailable.
- No hard dependency on companion availability.
- No real game text extraction.
- No decompiled game code committed.
- No copyrighted assets, screenshots, audio, extracted databases, or proprietary binaries.
- No OCR.
- No provider calls.
- No production overlay shell.
- Build or static verification stub if feasible.
- Documentation for manual build/install path and local-only test flow.

## Consequences

Pros:

- Focuses the next phase on the highest-risk integration unknown.
- Keeps overlay shell work from outrunning the bridge.
- Preserves the stdlib-first companion and overlay contracts.
- Keeps public repo content synthetic and reviewable.
- Avoids introducing frontend or desktop-shell dependencies too early.

Cons:

- There is still no real overlay window.
- Generated HTML remains a review artifact, not a player-ready UI.
- BepInEx feasibility remains unproven until 4A work begins.
- Future non-Python shell clients may still need a portable schema or generated contract docs.

Boundary:

Future shell work must not initially include global hotkeys, clipboard writes, native always-on-top
behavior, OCR, real provider calls, real extracted game content, browser automation dependencies,
production auth/TLS/persistence, or companion HTTP contract changes.
