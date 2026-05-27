# Local Bridge Workflow

`scripts/run_local_bridge_workflow.py` is a thin local coordinator for the existing synthetic
bridge workflow. It does not launch the game, read arbitrary game files, print raw logs, dump
provider payloads, change C# behavior, add companion endpoints, or implement capture.

The wrapper exists to reduce command sprawl. It delegates to the existing redacted helpers:

- `scripts/run_bepinex_metadata_probe_local_smoke.py`
- `scripts/run_bridge_to_overlay_synthetic_smoke.py`
- `scripts/run_overlay_refresh_readiness.py`

## Doctor

Run this before a local smoke:

```powershell
python scripts/run_local_bridge_workflow.py --phase doctor --auto-discover
```

The doctor phase reports redacted booleans only:

- git dirty/clean status;
- bridge build helper available;
- BepInEx references found;
- Steam game autodiscovery result;
- `BepInEx/plugins` presence;
- companion health availability;
- bridge DLL built/found;
- no raw logs, reports, workspace outputs, generated HTML, `bin/`, or `obj/` artifacts staged.

Private absolute paths are redacted by default. Use `--verbose` only for local troubleshooting.

## Metadata Smoke Prep

Prepare only the disabled metadata probe startup snapshot:

```powershell
python scripts/run_local_bridge_workflow.py `
  --phase prepare-metadata-smoke `
  --auto-discover
```

This may build/install the bridge through the existing helper and set:

```text
MetadataProbeEnabled = true
MetadataProbeLogOnStart = true
```

It does not enable synthetic send.

## Companion Smoke Prep

Prepare the companion-connected synthetic smoke:

```powershell
python scripts/run_companion_server.py
python scripts/run_local_bridge_workflow.py `
  --phase prepare-companion-smoke `
  --auto-discover
```

This verifies local companion health first. If health is available, it enables:

```text
MetadataProbeEnabled = true
MetadataProbeLogOnStart = true
SendSyntheticEventOnStart = true
```

`SendSyntheticEventOnStart` is the existing bridge config key and must be restored to false after
the local run.

## Bridge-To-Overlay Prep

For the full synthetic bridge-to-overlay path, prepare with:

```powershell
python scripts/run_companion_server.py
python scripts/run_local_bridge_workflow.py `
  --phase prepare-bridge-to-overlay-smoke `
  --auto-discover
```

Then manually launch and close the game yourself. The wrapper never launches the game.

After the game closes, run:

```powershell
python scripts/run_local_bridge_workflow.py `
  --phase post-bridge-to-overlay-smoke `
  --auto-discover `
  --write-report
```

The post phase uses only the existing redacted BepInEx log/report flow, companion latest
provider-state presence checks, overlay state-source/view-model validation, and in-memory HTML
accessibility checks. It must not print raw `LogOutput.log`, report contents, provider payloads,
private paths, screenshots, generated HTML, or game text.

Then clean up:

```powershell
python scripts/run_local_bridge_workflow.py `
  --phase cleanup `
  --auto-discover
```

Cleanup restores:

```text
MetadataProbeEnabled = false
MetadataProbeLogOnStart = false
SendSyntheticEventOnStart = false
```

Finally, if the companion server is still intentionally running, summarize overlay refresh readiness:

```powershell
python scripts/run_overlay_refresh_readiness.py --quiet
```

Use fixture-only validation with:

```powershell
python scripts/run_overlay_refresh_readiness.py --self-test --quiet
```

## Boundaries

The local workflow proves only synthetic/manual bridge and overlay readiness steps. It does not
prove or approve current-line capture, real text capture, UI text reading, Unity scanning,
hooks/Harmony, OCR, extraction, real provider execution, production overlay shell behavior,
companion HTTP contract changes, keyboard hooks, clipboard writes, downloads, or new dependencies.

Do not commit local runtime artifacts:

- `workspace/synthetic-slice/` outputs;
- `BepInEx/LogOutput.log` or other logs;
- report JSON from a real run;
- generated overlay HTML;
- `bin/` or `obj/` outputs;
- screenshots;
- game files;
- private local paths.
