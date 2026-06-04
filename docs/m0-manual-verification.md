# M0 Manual Verification

M0 can be fully complete only after the owner confirms, in chat or equivalent redacted evidence,
that the repository mission, current roadmap source, roadmap amendment policy, data-safety rules,
schema approach, and generated artifact policy match the intended project governance.

The manual evidence contract is:

```text
tests/fixtures/m0_manual_verification_report.synthetic.json
scripts/review_m0_manual_verification.py
```

The review helper accepts only redacted evidence with:

```text
schema_version: "m0-manual-verification-report.v1"
evidence_kind: "chat_attestation"
recommended_next_step: "m1_manual_synthetic_slice_review"
```

It rejects private paths, real game text, extracted databases, screenshots, logs, provider payloads,
generated private artifacts, URLs, and secret-looking strings.

The owner approval text is:

```text
M0 manual verification approved.

I confirm that:
- AGENTS.md matches the intended project mission and safety policy.
- tasks/milestones.md is the current roadmap source, and milestone criteria may be amended during
  development when they are obviously insufficient or need clarification.
- The repo policy correctly forbids committing copyrighted game text, extracted DBs, screenshots,
  logs, provider payloads, private paths, game files, bin, obj, and generated private artifacts.
- The JSON schema and safety-check approach is acceptable for M0.
- M0 may be marked fully complete under the strict completion standard.
```

Until that approval exists, M0 remains:

```text
manual_verification_complete: false
fully_complete: false
```
