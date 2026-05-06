# ADR 0004: Use translation ensemble for maximum quality mode

## Status

Proposed.

## Decision

Maximum quality mode uses multiple steps:
- glossary-aware baseline,
- context-rich literary translator,
- annotation agent,
- QA reviewer,
- consistency check,
- optional human approval.

## Consequences

Higher cost and latency, but better quality and explainability.
