# Runtime Private Hook Descriptor Contract

## Decision

The runtime-first path may move from the hook-candidate decision contract to a private hook
descriptor boundary:

```text
selected_strategy: targeted_hook_research_first
contract_status: contract_defined_only
recommended_next_step: runtime_private_hook_descriptor_local_validation
```

This is a contract only. It does not read descriptor files, implement hooks, capture real text,
inspect game UI, parse logs, call providers, change companion HTTP contracts, or alter BepInEx
runtime behavior.

## Required Prior Evidence

The descriptor boundary requires the prior decision contract:

```text
docs/runtime-targeted-hook-candidate-decision-contract.md
tests/fixtures/runtime_targeted_hook_candidate_decision_contract.synthetic.json
scripts/check_runtime_targeted_hook_candidate_decision_contract.py
```

## Private Descriptor Boundary

Future hook descriptor files may exist only under the ignored local-private root:

```text
workspace/local-private/runtime-capture/hook-descriptors/
```

The descriptor intent is local/private candidate target metadata needed for future hook work.
Tracked files must not contain descriptor values or any hook target identifiers.

## Future Local Validation Boundary

A later helper may validate one explicitly selected private descriptor under the ignored root. That
helper may emit only redacted booleans, counts, compatibility labels, and blocker categories.

The later helper must not print, hash, normalize, compare, or commit descriptor values. It must not
approve hook implementation or real text capture.

## Local Validation Implementation

The local validation helper is now:

```text
scripts/run_runtime_private_hook_descriptor_local_validation.py
```

It validates one explicit private descriptor under the ignored descriptor root and may write a
redacted validation summary only under:

```text
workspace/local-private/runtime-capture/hook-descriptors/validation/
```

Tracked evidence is limited to:

```text
tests/fixtures/runtime_private_hook_descriptor_local_validation_summary.synthetic.json
```

The next safe step is `runtime_private_hook_descriptor_local_validation_review_gate`, which may
review only the redacted summary. It must not reopen descriptor files or approve hook
implementation.

## Forbidden Tracked Evidence

Tracked docs, fixtures, tests, and reports must not include descriptor contents, candidate
identifiers, method names, class names, signatures, decompiled identifiers, raw logs, screenshots,
source text, payload dumps, private paths, provider data, or real runtime evidence.

Hook implementation, real text capture, UI inspection, log parsing, OCR, broad Unity scanning,
game-file reads, BepInEx log parsing, provider execution, companion contract changes, and committed
runtime artifacts remain blocked.

## Guardrail

Machine-readable evidence is tracked by:

```text
tests/fixtures/runtime_private_hook_descriptor_contract.synthetic.json
scripts/check_runtime_private_hook_descriptor_contract.py
```
