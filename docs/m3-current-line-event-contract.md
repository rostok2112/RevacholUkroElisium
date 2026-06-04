# M3 Current-Line Event Contract

Original `M3 - BepInEx bridge` requires:

```text
Emit current line event.
Match line IDs.
Debug console.
```

This contract scopes only the first criterion. It defines the minimal event shape and safety
boundary for a later implementation. It does not implement the event.

## Controlling Baseline

M3 starts from the recovered bridge baseline in:

```text
docs/m3-bepinex-bridge-scope.md
tests/fixtures/m3_bepinex_bridge_scope.synthetic.json
scripts/check_m3_bepinex_bridge_scope.py
```

Existing bridge skeleton, build helper, runtime smoke workflow, metadata probe, synthetic bridge
smoke, and local workflow wrapper must be reused. They must not be recreated for this step.

## Event Shape

A later implementation may emit only a local metadata event with this redacted shape:

```text
schema_version: "m3-current-line-event.v1"
event_kind: "current_line"
bridge_source: "bepinex"
emitted_at_unix_ms: integer
line_id: string or null
conversation_id: string or null
source: "synthetic" or "runtime_metadata"
capture_enabled: boolean
raw_text_included: false
private_paths_included: false
provider_called: false
```

The future event may not contain raw dialogue text, UI text, filenames, private paths, screenshots,
logs, provider payloads, extracted DB contents, line-index contents, or context-graph contents.

## Capture Boundary

The future implementation must be disabled by default and local-only. It may emit only through the
approved local bridge path that already exists in the BepInEx bridge baseline.

The future implementation must not add OCR, broad Unity object scanning, hooks/Harmony patches,
game-file reads, BepInEx log reads, provider execution, companion HTTP contract changes, or
committed runtime artifacts. Any line ID value must come from an already-safe metadata source or
invented synthetic event path; matching against the M2 private line index remains a separate M3
step.

## Guardrail

The machine-readable contract fixture and checker are:

```text
docs/m3-current-line-event-contract.md
tests/fixtures/m3_current_line_event_contract.synthetic.json
scripts/check_m3_current_line_event_contract.py
```

Validate with:

```powershell
python scripts/check_m3_current_line_event_contract.py --quiet
```

The next allowed atomic M3 step is:

```text
m3_current_line_event_implementation
```

The implementation guardrail is now tracked in:

```text
packages/bepinex-plugin/src/CurrentLineEventFactory.cs
tests/fixtures/m3_current_line_event_implementation.synthetic.json
scripts/check_m3_current_line_event_implementation.py
```

After this implementation, only the original M3 current-line event criterion is marked done. The
next bounded step is:

```text
m3_line_id_matching
```
