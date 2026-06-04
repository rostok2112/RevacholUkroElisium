# M3 BepInEx Bridge Scope Recovery

Original `M3 - BepInEx bridge` is now active after M2 closeout. The canonical roadmap in
`tasks/milestones.md` defines three M3 completion criteria:

```text
Emit current line event.
Match line IDs.
Debug console.
```

This scope recovery step documents the existing bridge baseline so later M3 work does not recreate
already completed support work.

## Existing Baseline

The former bridge/workflow work already provides:

```text
packages/bepinex-plugin/src/RevacholCompanionBridgePlugin.cs
packages/bepinex-plugin/src/CompanionHttpClient.cs
packages/bepinex-plugin/src/SyntheticEventFactory.cs
packages/bepinex-plugin/src/MetadataProbe.cs
scripts/build_bepinex_bridge.py
scripts/check_bepinex_bridge_safety.py
scripts/run_bepinex_metadata_probe_local_smoke.py
scripts/run_bridge_to_overlay_synthetic_smoke.py
scripts/run_local_bridge_workflow.py
```

That baseline includes BepInEx plugin loading, localhost companion health checks, an optional
synthetic event, optional local build verification, disabled-by-default metadata probe counters,
manual smoke/report/review helpers, and a local workflow wrapper.

## M3 Status

The existing baseline does not complete original M3:

- `Emit current line event` remains incomplete.
- `Match line IDs` remains incomplete.
- `Debug console` remains incomplete.

The bridge currently emits only invented synthetic events. It does not detect real dialogue,
capture current-line text, match runtime state to the M2 private line index, expose a debug command
surface, scan Unity objects, add hooks, run OCR, read game files, call providers, or change the
companion HTTP contract.

## Guardrail

The machine-readable scope fixture and checker are:

```text
docs/m3-bepinex-bridge-scope.md
tests/fixtures/m3_bepinex_bridge_scope.synthetic.json
scripts/check_m3_bepinex_bridge_scope.py
```

Validate with:

```powershell
python scripts/check_m3_bepinex_bridge_scope.py --quiet
```

The next allowed atomic M3 step is:

```text
m3_current_line_event_contract
```
