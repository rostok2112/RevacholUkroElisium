# ADR 0009: Metadata-only extension decision gate

## Status

Accepted.

## Context

Milestones 4G through 4J created a conservative metadata-only bridge path:

- a static metadata probe gate;
- a disabled-by-default C# metadata probe skeleton;
- a manual smoke workflow for enabling the probe locally;
- a redacted report checker, template writer, and review helper.

Those pieces make it possible to discuss a later metadata-only extension, but they do not prove a
runtime extension should be implemented immediately. The repository still has no committed real
runtime report and must not treat review readiness as approval for current-line capture, real text
capture, UI text reading, Unity scanning, hooks, OCR, extraction, provider execution, shell work, or
companion HTTP contract changes.

## Decision

The project is currently:

```text
ready_for_metadata_only_extension_discussion
```

It is not yet ready for metadata-only extension implementation.

Readiness states are:

- `not_ready`: the metadata probe safety contracts, report workflow, or review helper are missing
  or unsafe.
- `ready_for_metadata_only_extension_discussion`: the static contracts exist and a later extension
  may be scoped in docs, but no runtime expansion is approved.
- `ready_for_metadata_only_extension_implementation`: a later milestone may implement a strictly
  metadata-only extension after explicit approval and a ready local review, or after a documented
  decision to proceed without one.

Even the strongest state does not approve current-line capture, real text capture, UI text reading,
Unity scanning, hooks, OCR, extraction, provider execution, companion HTTP contract changes, or
production overlay work.

## Allowed Later Extension Scope

A later approved metadata-only extension may include only safe metadata such as:

- probe execution count;
- plugin lifecycle booleans;
- companion health booleans;
- synthetic-send booleans;
- bridge-generated synthetic ids;
- redacted status codes;
- zero/default counters;
- explicit `real_text_captured = false`;
- explicit `current_line_capture_enabled = false`.

It must not include:

- text strings from the game;
- UI text;
- runtime scene or object names;
- screenshots;
- OCR output;
- save data;
- asset names from runtime;
- stack traces;
- raw logs;
- private paths;
- companion payloads containing real text.

## Required Gate Before Implementation

A later implementation milestone must have:

- a local metadata probe report review with `readiness_status = "ready"`, or a documented decision
  explaining why the review is not required;
- no forbidden markers in the report or review;
- explicit developer approval for implementation;
- source defaults that keep the extension disabled by default;
- no companion HTTP contract changes;
- no text capture.

The committed machine-readable gate fixture is:

```text
tests/fixtures/bepinex_bridge.metadata_extension_gate.synthetic.json
```

The fixture records the current decision and keeps implementation and capture permissions closed.

## Milestone 4L Scope Follow-up

Milestone 4L adds a narrower scope contract for a possible 4M implementation:

```text
docs/bepinex-metadata-only-extension-scope.md
tests/fixtures/bepinex_bridge.metadata_only_extension_scope.synthetic.json
```

The 4L decision may allow 4M planning without a ready reviewed local metadata report only because
the allowed 4M behavior is inert, disabled by default, and limited to counters and booleans. That
does not change the capture boundary: text capture, current-line capture, UI text reading, Unity
scanning, hooks, OCR, extraction, provider calls, and companion contract changes remain disallowed.

## Consequences

Pros:

- Preserves the safety boundary while allowing architecture discussion to continue.
- Prevents a ready metadata report review from being misread as approval for capture.
- Gives future milestones a deterministic gate fixture to update intentionally.

Cons:

- The bridge remains limited to the existing disabled probe skeleton.
- A later metadata-only extension still needs a separate scoped milestone.
- Runtime usefulness remains unproven until local redacted evidence is reviewed.
