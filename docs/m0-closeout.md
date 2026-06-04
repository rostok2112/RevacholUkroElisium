# M0 Closeout

Original `M0 - Repo and contracts` criteria:

```text
AGENTS.md, skills, agents, docs.
JSON schemas.
Safety checks.
```

M0 is automated-complete at the repository-contract level. The strict completion standard still
requires owner confirmation that the mission, legal/data safety rules, schema policy, and repository
safety checks match the intended project governance.

Tracked M0 status fields:

```text
automated_complete
manual_verification_required
manual_verification_complete
fully_complete
```

## Verification

Automated guardrail:

```text
tests/fixtures/m0_closeout.synthetic.json
scripts/check_m0_closeout.py
```

Manual attestation guardrail:

```text
docs/m0-manual-verification.md
tests/fixtures/m0_manual_verification_report.synthetic.json
scripts/review_m0_manual_verification.py
```

Manual verification required:

```text
owner_confirms_repo_contracts_and_safety_policy
```

M0 is not fully complete until that redacted manual confirmation is recorded.

The next strict completion step is:

```text
m0_manual_verification
```

After a passing chat-attestation review, the next strict completion step becomes:

```text
m1_manual_synthetic_slice_review
```
