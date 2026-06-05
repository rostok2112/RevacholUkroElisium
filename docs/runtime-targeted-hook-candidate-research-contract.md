# Runtime Targeted Hook Candidate Research Contract

## Decision

The runtime-first path may move from strategy selection to a local/private targeted hook candidate
research report boundary:

```text
selected_strategy: targeted_hook_research_first
contract_status: contract_defined_only
recommended_next_step: runtime_targeted_hook_candidate_research_local_report
```

This is a contract only. It does not implement hooks, capture real text, inspect game UI, parse
logs, call providers, change companion HTTP contracts, or alter BepInEx runtime behavior.

## Allowed Future Research Boundary

A later local report helper may summarize whether the user performed targeted hook candidate
research locally. Tracked evidence may contain only redacted booleans, counts, status labels, and
blocker categories.

Any local notes, raw observations, or private reports must stay ignored under:

```text
workspace/local-private/runtime-capture/hook-research/
```

## Forbidden Tracked Evidence

Tracked docs, fixtures, tests, and reports must not include candidate identifiers, decompiled
method names, signatures, class names, raw logs, screenshots, source text, payload dumps, private
paths, provider data, or real runtime evidence.

Hook implementation, real text capture, OCR, broad Unity scanning, game-file reads, BepInEx log
parsing, provider execution, companion contract changes, and committed runtime artifacts remain
blocked until a later contract explicitly scopes them.

## Guardrail

Machine-readable evidence is tracked by:

```text
tests/fixtures/runtime_targeted_hook_candidate_research_contract.synthetic.json
scripts/check_runtime_targeted_hook_candidate_research_contract.py
```

This contract follows the strategy decision in:

```text
docs/runtime-current-line-capture-strategy-decision.md
```
