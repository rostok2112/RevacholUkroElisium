# Runtime Targeted Hook Candidate Decision Contract

## Decision

The runtime-first path may move from redacted hook research review to a static hook-candidate
decision boundary:

```text
selected_strategy: targeted_hook_research_first
contract_status: contract_defined_only
recommended_next_step: runtime_private_hook_descriptor_contract
```

This is a contract only. It does not implement hooks, capture real text, inspect game UI, parse
logs, call providers, change companion HTTP contracts, or alter BepInEx runtime behavior.

## Required Prior Evidence

The decision boundary requires a passing redacted review from:

```text
scripts/review_runtime_targeted_hook_candidate_research_report.py
tests/fixtures/runtime_targeted_hook_candidate_research_review_decision.synthetic.json
```

Tracked evidence may contain only booleans, aggregate counts, status labels, blocker categories,
and safe next-step values.

## Allowed Outcomes

The only allowed tracked outcomes are:

```text
ready_for_private_hook_descriptor_contract
repeat_targeted_hook_research
```

`ready_for_private_hook_descriptor_contract` allows only a later static contract for private hook
descriptors. `repeat_targeted_hook_research` means the local/private research report must be
repeated or improved.

## Forbidden Tracked Evidence

Tracked docs, fixtures, tests, and reports must not include candidate identifiers, method names,
class names, signatures, decompiled identifiers, raw logs, screenshots, source text, payload dumps,
private paths, provider data, or real runtime evidence.

Hook implementation, real text capture, UI inspection, log parsing, OCR, broad Unity scanning,
game-file reads, BepInEx log parsing, provider execution, companion contract changes, and committed
runtime artifacts remain blocked.

## Guardrail

Machine-readable evidence is tracked by:

```text
tests/fixtures/runtime_targeted_hook_candidate_decision_contract.synthetic.json
scripts/check_runtime_targeted_hook_candidate_decision_contract.py
```

The private descriptor boundary, when separately approved, must keep descriptor files ignored under:

```text
workspace/local-private/runtime-capture/hook-descriptors/
```
