# ADR 0008: Current-line capture research and safety boundaries

## Status

Accepted.

## Context

Milestones 4A through 4D produced a synthetic/manual bridge skeleton, optional local build helper,
manual runtime smoke checklist, safe log contract, and redacted report workflow. The bridge still
does not detect the current visible line, inspect runtime UI, patch game methods, extract text, run
OCR, or send real game content.

Before any capture implementation exists, the project needs a conservative decision record for the
possible approaches and the legal/privacy boundary around future experiments.

## Options Considered

### A. Manual or synthetic event trigger only

- Enables: continued bridge verification through invented events and user-controlled smoke tests.
- Complexity: low.
- Legal/copyright/data risk: low, because committed data remains synthetic.
- Privacy/logging risk: low when logs stay metadata-only.
- Brittleness: low, because it does not depend on game internals.
- Testing feasibility: high with the existing companion server and synthetic fixtures.
- Decompiled names/code required: no.
- Real copyrighted text capture risk: no, if kept synthetic/manual.
- Synthetic-only start: yes.
- Recommended status: allowed now.

### B. User-assisted copy or manual input

- Enables: user-controlled experiments where the user provides text outside automated capture.
- Complexity: low to medium.
- Legal/copyright/data risk: medium, because users could paste real text into local private flows.
- Privacy/logging risk: medium; all payloads and logs must remain local, ignored, and redacted.
- Brittleness: low.
- Testing feasibility: medium with synthetic manual examples.
- Decompiled names/code required: no.
- Real copyrighted text capture risk: possible if users provide it.
- Synthetic-only start: yes, if limited to invented examples.
- Recommended status: research only; not a default runtime path.

### C. Observe Unity UI text objects

- Enables: possible runtime discovery of visible text without patching a specific method.
- Complexity: high.
- Legal/copyright/data risk: high if observed text is logged, committed, or sent as raw payloads.
- Privacy/logging risk: high because visible text can include copyrighted content and user context.
- Brittleness: high across UI layout, localization, engine, and version changes.
- Testing feasibility: low without local private runtime experiments.
- Decompiled names/code required: not necessarily, but object names or component structures may still
  become legally sensitive if recorded.
- Real copyrighted text capture risk: high.
- Synthetic-only start: only if probes report booleans and counters, not text.
- Recommended status: defer; metadata-only research later if runtime smoke is proven.

### D. Patch dialogue or UI update methods

- Enables: precise current-line events if the correct local runtime method is identified.
- Complexity: high.
- Legal/copyright/data risk: high if decompiled names, signatures, or captured text are committed.
- Privacy/logging risk: high because hooks can expose real text at the exact moment of display.
- Brittleness: high across game versions and mod-loader/runtime versions.
- Testing feasibility: low in public CI; only local private verification is realistic.
- Decompiled names/code required: likely, and those details must not be committed if legally risky.
- Real copyrighted text capture risk: high.
- Synthetic-only start: only through a dummy/local metadata probe that emits no real text.
- Recommended status: research only after manual smoke evidence review; no implementation now.

### E. Save, state, or event observation

- Enables: possible context inference from local runtime state rather than visible UI text.
- Complexity: medium to high.
- Legal/copyright/data risk: high if save files, extracted state, or proprietary identifiers are
  committed.
- Privacy/logging risk: high because saves/state can include broad user and game progress data.
- Brittleness: medium to high across versions and user state.
- Testing feasibility: low without private local fixtures that must remain ignored.
- Decompiled names/code required: maybe, depending on the observation route.
- Real copyrighted text capture risk: medium to high.
- Synthetic-only start: possible with booleans, counters, and bridge-generated ids only.
- Recommended status: defer; metadata-only local research after runtime smoke evidence.

### F. OCR fallback

- Enables: screen-text capture without game-specific integration.
- Complexity: high.
- Legal/copyright/data risk: very high because screenshots and OCR output can contain copyrighted
  text and visual assets.
- Privacy/logging risk: very high because screen capture can include unrelated private user data.
- Brittleness: very high across resolution, font, language, overlays, and accessibility settings.
- Testing feasibility: poor without committing screenshots or OCR outputs, which this repo must not
  do.
- Decompiled names/code required: no.
- Real copyrighted text capture risk: very high.
- Synthetic-only start: possible only with synthetic screenshots, but not useful for game feasibility.
- Recommended status: forbidden for near-term project work.

### G. External screen capture or accessibility APIs

- Enables: possible OS-level observation outside game integration.
- Complexity: high.
- Legal/copyright/data risk: very high if screenshots, OCR-like text, or accessibility text are
  stored.
- Privacy/logging risk: very high because OS-level capture can include unrelated applications.
- Brittleness: high across platforms, permissions, focus, display mode, and accessibility settings.
- Testing feasibility: poor without sensitive local artifacts.
- Decompiled names/code required: no.
- Real copyrighted text capture risk: high.
- Synthetic-only start: possible only as a generic metadata probe, not as useful line capture.
- Recommended status: defer; do not use for early bridge work.

## Decision

Stay conservative:

- Continue with manual and synthetic bridge events until a redacted runtime smoke report is reviewed.
- Do not implement OCR.
- Do not implement broad Unity object scanning yet.
- Do not implement game method patches yet.
- Do not commit decompiled names, method signatures, extracted text, screenshots, audio, save files,
  runtime logs containing game text, private paths, OCR output, or raw companion payloads with real
  game text.
- If hook or UI research becomes necessary, keep it local-only, metadata-only, and disabled by
  default at first.
- Any future probe must emit synthetic/manual metadata before it is allowed to emit real text.
- Any future real text capture must be explicit opt-in, private, ignored, and covered by a later
  safety review.

## Runtime-First Strategy Decision

The current runtime-first follow-up decision is now tracked in:

```text
docs/runtime-current-line-capture-strategy-decision.md
tests/fixtures/runtime_current_line_capture_strategy_decision.synthetic.json
scripts/check_runtime_current_line_capture_strategy_decision.py
```

The selected strategy is:

```text
targeted_hook_research_first
```

The next step is:

```text
runtime_targeted_hook_candidate_research_contract
```

This does not change the ADR boundary: hook implementation, real text capture, OCR, screenshots,
broad Unity scanning, game-file reads, BepInEx log parsing, provider calls, companion contract
changes, decompiled identifiers, method signatures, class names, raw logs, private paths, payload
dumps, and committed runtime evidence remain blocked.

## Targeted Hook Candidate Research Contract

The selected strategy is now bounded by:

```text
docs/runtime-targeted-hook-candidate-research-contract.md
tests/fixtures/runtime_targeted_hook_candidate_research_contract.synthetic.json
scripts/check_runtime_targeted_hook_candidate_research_contract.py
```

The contract keeps `targeted_hook_research_first` as the selected strategy and allows only a later
local/private redacted report step:

```text
runtime_targeted_hook_candidate_research_local_report
```

The report step still must not implement hooks, capture real text, inspect game UI, parse logs,
commit candidate identifiers, emit private paths, call providers, or change companion contracts.

## Targeted Hook Candidate Research Local Report

The local report gate is tracked by:

```text
tests/fixtures/runtime_targeted_hook_candidate_research_report.synthetic.json
scripts/check_runtime_targeted_hook_candidate_research_report.py
```

It validates only redacted local/private report summaries under the ignored hook research workspace.
It does not perform research, inspect game UI, parse logs, capture text, call providers, or change
bridge/companion behavior.

The next step is:

```text
runtime_targeted_hook_candidate_research_review_gate
```

## Targeted Hook Candidate Research Review Gate

The redacted report review gate is tracked by:

```text
scripts/review_runtime_targeted_hook_candidate_research_report.py
tests/fixtures/runtime_targeted_hook_candidate_research_review_decision.synthetic.json
```

The reviewer reads only the redacted local/private report JSON under the ignored hook research
workspace. It does not read raw notes, raw logs, screenshots, source text, candidate identifiers,
method names, signatures, class names, provider data, private paths, or real runtime evidence.

A passing review allows only a later static decision contract:

```text
runtime_targeted_hook_candidate_decision_contract
```

Hook implementation, real text capture, Unity UI inspection, OCR, screenshots, game-file reads,
BepInEx log parsing, provider calls, companion HTTP contract changes, and committed runtime
artifacts remain blocked.

## Targeted Hook Candidate Decision Contract

The static decision contract is tracked by:

```text
docs/runtime-targeted-hook-candidate-decision-contract.md
tests/fixtures/runtime_targeted_hook_candidate_decision_contract.synthetic.json
scripts/check_runtime_targeted_hook_candidate_decision_contract.py
```

It requires prior redacted review evidence from:

```text
scripts/review_runtime_targeted_hook_candidate_research_report.py
```

The selected strategy remains:

```text
targeted_hook_research_first
```

The next step is:

```text
runtime_private_hook_descriptor_contract
```

The decision contract allows only a later private descriptor contract. Candidate identifiers,
method names, signatures, class names, decompiled identifiers, raw logs, screenshots, source text,
payload dumps, private paths, provider data, and real runtime evidence remain forbidden in tracked
files. Hook implementation and real text capture remain blocked.

Allowed future local experiment outputs are limited to redacted metadata and booleans such as:

```json
{
  "plugin_loaded": true,
  "ui_probe_attempted": false,
  "current_line_capture_enabled": false,
  "real_text_captured": false,
  "synthetic_event_sent": true
}
```

Other allowed local outputs include bridge-generated synthetic event ids, bridge-generated line ids,
safe counters, and redacted runtime smoke reports under ignored workspace paths.

## Milestone 4F Readiness Checklist

Milestone 4F should be runtime smoke execution guide and local evidence review, not first capture
implementation.

4F should include:

- Review process for a user-supplied redacted runtime smoke report.
- Clear pass/partial/fail interpretation for build, plugin load, health check, unavailable companion,
  optional synthetic send, and game-continues observations.
- A redacted review helper may summarize readiness, but it must not read logs, screenshots, game
  files, companion state, or provider outputs.
- No real text capture by default.
- No game hooks unless a later milestone explicitly approves them.
- No OCR.
- No extraction.
- No committed logs, screenshots, save files, private paths, or real runtime reports.
- No companion HTTP contract changes.
- A decision gate before any metadata-only current-line probe is scoped.

## Milestone 4G Metadata Gate

Milestone 4G adds the decision gate in `docs/bepinex-metadata-probe-gate.md`. The gate does not
approve capture or add runtime probe code. It only defines a reportable metadata boundary for a
later disabled-by-default probe:

- booleans, safe counters, synthetic ids, and safe status/error codes are allowed;
- `current_line_capture_enabled` must remain `false`;
- `real_text_captured` must remain `false`;
- local reports must stay under ignored workspace paths;
- probe implementation still requires a later approved milestone.

## Milestone 4J Metadata Report Review

Milestone 4J adds a redacted metadata probe report reviewer:

```text
scripts/review_bepinex_metadata_probe_report.py
```

The reviewer can mark a report `ready` only for discussion of a later metadata-only extension. It
does not approve current-line capture, real text capture, UI text reading, hooks, OCR, extraction,
provider execution, or companion HTTP contract changes. It does not read logs, screenshots, game
files, companion state, or provider output.

## Milestone 4K Extension Gate

Milestone 4K records the next decision in:

```text
docs/adr/0009-metadata-only-extension-gate.md
```

The decision allows metadata-only extension discussion only. Implementation still needs a later
approved milestone, a ready local metadata probe review or documented no-review exception, disabled
defaults, no text capture, and no companion HTTP contract changes.

## Consequences

Pros:

- Keeps the public repository free of proprietary text and local runtime artifacts.
- Avoids building a fragile capture mechanism before manual runtime viability is known.
- Keeps the bridge smoke path testable with current synthetic fixtures and redacted reports.
- Makes future capture work reviewable by forcing metadata-only experiments first.

Cons:

- Current-line capture remains unimplemented.
- Manual/synthetic events remain the only safe bridge behavior for now.
- Real feasibility remains unknown until a local runtime report is reviewed.
- Any useful capture path will need another milestone and likely local-only testing.
