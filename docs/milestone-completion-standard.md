# Milestone Completion Standard

The current roadmap source is `tasks/milestones.md`.

The roadmap is not immutable. Milestone criteria may be amended, split, or clarified during
development when existing criteria are obviously insufficient or unsafe. Any amendment must update
`tasks/milestones.md`, relevant docs, and the applicable fixture/checker evidence.

A roadmap milestone is fully complete only when:

- its automated repository checks pass;
- its required manual or local verification evidence is documented;
- that evidence is redacted and reviewed;
- no private/generated artifacts are committed.

Tracked closeouts must distinguish these fields:

```text
automated_complete
manual_verification_required
manual_verification_complete
fully_complete
```

`fully_complete=true` is forbidden while `manual_verification_required=true` and
`manual_verification_complete=false`.

## Manual Evidence Boundaries

Manual evidence may be represented in tracked fixtures only as redacted booleans and short status
labels. Do not commit private paths, real extracted text, generated DBs, indexes, context graphs,
logs, screenshots, provider payloads, game files, `bin`, or `obj`.

The aggregate guardrail is:

```text
tests/fixtures/m0_closeout.synthetic.json
scripts/check_m0_closeout.py
tests/fixtures/roadmap_governance_review.synthetic.json
scripts/check_roadmap_governance_review.py
tests/fixtures/m0_manual_verification_report.synthetic.json
scripts/review_m0_manual_verification.py
tests/fixtures/m1_closeout.synthetic.json
scripts/check_m1_closeout.py
tests/fixtures/milestone_completion_status.synthetic.json
scripts/check_milestone_completion_status.py
```

Until M0-M4 are fully complete under this standard, the next step remains:

```text
m1_manual_synthetic_slice_review
```
