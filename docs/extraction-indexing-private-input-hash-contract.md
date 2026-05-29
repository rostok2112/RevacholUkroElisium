# Extraction Indexing Private Input Hash Contract

Milestone 5A.5 decides the next hash boundary after the private input adapter dry-run and
redacted dry-run review. It is a contract/decision milestone only. It does not implement hashing.

This contract does not approve real extraction, private index construction, file content reads,
automatic game-install scanning, BepInEx log reads, save parsing, screenshots, OCR, current-line
capture, UI text reading, Unity scanning, hooks/Harmony, decompiled game-code work, companion HTTP
contract changes, provider execution, or committed real extracted text.

## Why Hashes Are Being Considered

Milestone 5A.3 deliberately emitted dry-run summaries with `hashes_computed=false`. Milestone 5A.4
added a review gate where `ready_for_hash_decision=true` may mean that the summary is redacted
enough to discuss a later hash contract.

Hashes are useful because they can help detect unchanged private diagnostics without storing raw
input details. They are also risky because stable hashes can identify known files, path strings, or
private local structures. This contract keeps those risks closed until a narrower hash contract
exists.

## Decision

Milestone 5A.5 does not allow hash implementation.

The only future hash topic left open is a later contract for hashing an already-redacted dry-run
summary object. That future contract must define canonical JSON inputs, excluded fields, redaction
requirements, output locations, and review rules before any hash is computed.

Blocked in 5A.5:

- file content hashing;
- path string hashing;
- hashing verbose summaries that include private paths;
- hashing original private input files;
- hashing BepInEx logs, screenshots, save files, decompiled output, or provider payloads;
- private index construction from private input;
- real extraction or committed extracted text.

If dry-run summary hashing is later approved, it may consider only canonicalized, redacted metadata
that already passed the 5A.4 review helper. It must not include private path fields, raw file
contents, raw payloads, raw logs, generated indexes, provider payloads, or game text.

## Private Output Boundary

Any future local hash summary remains private and ignored under:

```text
workspace/local-private/extraction-indexing/
```

No future hash output from real private input may be committed unless a later checker defines a
synthetic/redacted committed fixture shape. 5A.5 adds no such committed real-input shape.

## Fixture And Checker

This contract file is:

```text
docs/extraction-indexing-private-input-hash-contract.md
```

The machine-readable 5A.5 decision fixture is:

```text
tests/fixtures/private_input_hash_decision.synthetic.json
```

Validate it with:

```powershell
python scripts/check_private_input_hash_decision_contract.py --quiet
```

The fixture records that hash implementation remains blocked, file content hashing and path string
hashing are forbidden, and private index construction remains blocked. Its recommended next step is
a separate dry-run summary hash contract, not hash implementation.

## Milestone 5A.6 Dry-Run Summary Hash Contract

Milestone 5A.6 defines that next contract in:

```text
docs/extraction-indexing-dry-run-summary-hash-contract.md
tests/fixtures/dry_run_summary_hash_contract.synthetic.json
scripts/check_dry_run_summary_hash_contract.py
```

The 5A.6 contract defines only what a later implementation may hash: canonical redacted summary
metadata after the 5A.4 review rules pass. It still keeps hash implementation blocked. File content
hashing, path string hashing, filename hashing, raw payload/log hashing, private index construction,
real extraction, and committed real text remain forbidden.

## Relationship To Earlier 5A Contracts

Milestone 5A.2 defines the explicit workspace-private input boundary in
`docs/extraction-indexing-private-input-adapter-contract.md`.

Milestone 5A.3 implements `scripts/run_private_input_adapter_dry_run.py`, which reads metadata only
and keeps `hashes_computed=false`.

Milestone 5A.4 implements `scripts/review_private_input_adapter_dry_run.py`, which can mark a
redacted dry-run summary ready for a hash decision discussion. That readiness does not approve
hashing.

Milestone 5A.1 defines the synthetic-only private index contract in
`docs/extraction-indexing-private-index-contract.md`. Private index construction from real input
remains blocked after 5A.5.
