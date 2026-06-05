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

## Local Report Boundary

The local report helper may summarize whether the user performed targeted hook candidate research
locally. Tracked evidence may contain only redacted booleans, counts, status labels, and blocker
categories.

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
tests/fixtures/runtime_targeted_hook_candidate_research_report.synthetic.json
scripts/check_runtime_targeted_hook_candidate_research_report.py
```

This contract follows the strategy decision in:

```text
docs/runtime-current-line-capture-strategy-decision.md
```

The active next step after the local report gate is:

```text
runtime_targeted_hook_candidate_research_review_gate
```

## Review Gate

The review gate is tracked by:

```text
scripts/review_runtime_targeted_hook_candidate_research_report.py
tests/fixtures/runtime_targeted_hook_candidate_research_review_decision.synthetic.json
```

It reads only the redacted report JSON under the ignored hook research workspace and emits only
redacted review status, aggregate counts, blocker categories, and a safe next-step value. A passing
review allows only:

```text
runtime_targeted_hook_candidate_decision_contract
```

Hook implementation, real text capture, UI inspection, log parsing, provider execution, companion
contract changes, candidate identifiers, method/class names, signatures, source text, private
paths, raw logs, screenshots, payload dumps, and real runtime evidence remain blocked.

## Decision Contract

The next decision boundary is tracked by:

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

The next step after the decision contract is:

```text
runtime_private_hook_descriptor_contract
```
