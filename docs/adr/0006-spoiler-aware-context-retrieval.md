# ADR 0006: Spoiler-aware context retrieval

## Status

Accepted.

## Decision

The context engine must track spoiler budget. Default retrieval uses player-visible and local-neighborhood context, not arbitrary future lines.

## Consequences

This protects first playthrough integrity while still enabling deep context when explicitly requested.
