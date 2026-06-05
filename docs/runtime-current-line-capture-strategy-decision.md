# Runtime Current-Line Capture Strategy Decision

## Decision

The runtime-first path now selects targeted hook research as the next strategy:

```text
selected_strategy: targeted_hook_research_first
recommended_next_step: runtime_targeted_hook_candidate_research_contract
```

This is a strategy decision only. It does not implement hooks, read game text, inspect Unity UI,
scan objects, parse logs, call providers, or change companion HTTP contracts.

## Why This Strategy

Manual/synthetic runtime transport is already proven by the disabled-by-default BepInEx startup
send, the companion `POST /runtime/current-line` endpoint, and runtime translation-memory lookup.
The original M2 private export path remains unavailable because there is no local export source.
Automatic current-line capture is therefore likely to require targeted local runtime observation
after another contract defines how candidates may be identified safely.

## Boundary

The next contract may define only how to identify candidate hook points locally. It must not commit
candidate identifiers, decompiled method names, signatures, class names, raw logs, screenshots,
game text, private paths, payload dumps, provider payloads, or real runtime evidence.

Any local notes or reports for future hook research must stay ignored under:

```text
workspace/local-private/runtime-capture/hook-research/
```

OCR, screenshots, broad Unity scanning, save-file reads, game-file reads, BepInEx log parsing,
provider execution, companion contract changes, and real text capture remain blocked until a later
contract explicitly scopes them.

## Guardrail

Machine-readable evidence is tracked by:

```text
tests/fixtures/runtime_current_line_capture_strategy_decision.synthetic.json
scripts/check_runtime_current_line_capture_strategy_decision.py
```

The active next step is:

```text
runtime_targeted_hook_candidate_research_contract
```
