# BepInEx Bridge Log Contract

Milestone 4C defines a manual runtime log contract for the synthetic/manual BepInEx bridge.

This is not a runtime log from a local game install. Do not commit real BepInEx logs, game logs,
screenshots, game text, local install paths, or smoke reports.

## Allowed Log Metadata

Bridge logs may include:

- plugin name and synthetic/manual bridge mode;
- enabled or disabled config state;
- localhost safety skip;
- companion health available or unavailable state;
- endpoint status code;
- synthetic event id;
- synthetic line id;
- concise unavailable-companion warning;
- exception type and message for unavailable companion startup, without stack trace.

## Required Runtime Signals

The committed machine-readable contract is:

```text
tests/fixtures/bepinex_bridge.log_contract.synthetic.json
```

The C# bridge source must contain safe snippets for:

- plugin loaded in synthetic/manual mode;
- disabled bridge config;
- non-localhost companion URL skip;
- companion health passed;
- companion health failed;
- companion unavailable but game continues;
- synthetic send skipped;
- synthetic provider event sent;
- synthetic provider event rejected;
- `event_id`, `line_id`, and `status` metadata.

## Forbidden Log Content

Bridge logs must not include:

- full request payloads;
- full response payloads;
- raw source text;
- secrets, tokens, or API-key-shaped values;
- private absolute paths;
- real game dialogue or proprietary content;
- game hook, Unity object scan, OCR, extraction, or decompiled-code details;
- stack traces by default.

## Current Exception Policy

The startup unavailable-companion warning may include the exception type name and message. It must not
include a stack trace, request payload, response body, or local private path.
