# Roadmap Governance Review

`tasks/milestones.md` is the current canonical roadmap source, but it is not immutable. Milestone
criteria may be expanded, split, or clarified during development when the existing criteria are
obviously insufficient, unsafe, or too vague for real completion.

Roadmap changes must be deliberate:

- update `tasks/milestones.md` when a top-level milestone criterion changes;
- update the relevant closeout or scope docs;
- add or update fixture/checker evidence for the changed boundary;
- keep generated/private artifacts out of git;
- do not mark a milestone fully complete until automated checks and required manual/local
  verification pass under the current criteria.

## Current M0-M7 Review

The current roadmap remains a valid high-level plan:

```text
M0 - Repo and contracts
M1 - Synthetic vertical slice
M2 - Local extraction import
M3 - BepInEx bridge
M4 - Real overlay
M5 - Maximum quality pipeline
M6 - Voice/audio context
M7 - Review studio
```

The criteria are intentionally compact. They are sufficient as headings, but not sufficient by
themselves as strict completion evidence. Each milestone may need implementation contracts,
review gates, manual/local verification, and closeout evidence before it can be called complete.

## M0 Decision Impact

M0 manual verification must confirm both:

```text
tasks/milestones.md is the current canonical roadmap source
roadmap criteria may be amended when development proves they are insufficient
```

This resolves the rejected interpretation where "canonical" could be read as "never change."
