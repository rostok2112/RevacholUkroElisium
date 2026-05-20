# BepInEx Bridge Skeleton

Milestone 4A adds a safe C# BepInEx bridge skeleton under `packages/bepinex-plugin/`.

This is not production mod behavior. It does not detect real dialogue, scan Unity objects, extract
text, read local game databases, run OCR, call providers, or display an overlay. It only defines a
small localhost bridge shape for future work.

## What The Skeleton Does

- Loads with BepInEx plugin metadata.
- Binds config values:
  - `Enabled = true`
  - `CompanionServerUrl = "http://127.0.0.1:8765"`
  - `RequestTimeoutMs = 3000`
  - `SendSyntheticEventOnStart = false`
- Checks `GET /health` on the local companion server.
- Can send one invented synthetic fake event to `POST /synthetic/provider-annotate`.
- Logs only safe metadata such as event id, line id, status, and unavailable companion state.
- Keeps the game running if the companion server is unavailable.

## Running The Companion Server

For local manual testing, start the companion server from the repository root:

```powershell
python scripts/run_companion_server.py
```

The default bridge URL matches the companion default:

```text
http://127.0.0.1:8765
```

The bridge skips requests if a non-localhost URL is configured.

## Optional Build Verification

Milestone 4B adds an optional build helper:

```powershell
python scripts/build_bepinex_bridge.py --quiet
```

The helper is stdlib-only and skips cleanly when `dotnet` or user-local BepInEx IL2CPP references
are missing. It does not download tools, require game files, or run as a required `check_all`
compilation step.

The package includes a minimal project file for a later local build:

```text
packages/bepinex-plugin/Revachol.UkrainianCompanion.BepInExBridge.csproj
```

It expects user-local BepInEx references supplied at build time:

```text
BepInExCoreDll=<path to BepInEx.Core.dll>
BepInExIL2CPPDll=<path to BepInEx.Unity.IL2CPP.dll>
```

You can pass those references directly:

```powershell
python scripts/build_bepinex_bridge.py `
  --core-dll <path-to-BepInEx.Core.dll> `
  --il2cpp-dll <path-to-BepInEx.Unity.IL2CPP.dll> `
  --output workspace/synthetic-slice/bepinex-bridge/build-report.json
```

or provide them through local environment variables:

```text
BEPINEX_CORE_DLL
BEPINEX_IL2CPP_DLL
BepInExCoreDll
BepInExIL2CPPDll
```

Generated reports belong under `workspace/synthetic-slice/bepinex-bridge/`. Built DLLs remain under
ignored `bin/`/`obj/` outputs and must not be committed.

### Warning Policy

Local BepInEx IL2CPP builds may emit `MSB3277` assembly-version conflict warnings from BepInEx/.NET
reference graphs. For Milestone 4B:

- A successful build with `MSB3277` warnings is acceptable if the bridge safety checks pass.
- The helper reports total warning count and `MSB3277` warning count.
- Warnings must stay visible; do not hide or suppress them silently.
- A later milestone may pin or clean references if runtime testing shows those warnings matter.

## Manual Install Shape

When a local build exists, the resulting DLL would be copied into the user-owned BepInEx plugin
folder for their local game install:

```text
BepInEx/plugins/
```

Do not commit built DLLs, game binaries, extracted databases, screenshots, audio, or local install
paths.

## Synthetic Manual Verification Checklist

This checklist is manual and synthetic-only:

1. Start the local companion server:

   ```powershell
   python scripts/run_companion_server.py
   ```

2. Run the optional build helper with local BepInEx references.
3. Copy the built DLL into the user-owned `BepInEx/plugins/` folder.
4. Launch the game from the user-owned local install.
5. Confirm the plugin logs safe startup metadata.
6. Confirm the `/health` check logs companion availability, or a concise unavailable warning.
7. Optionally set `SendSyntheticEventOnStart = true` in the local BepInEx config.
8. Confirm the companion server receives the invented synthetic provider event.
9. Stop the companion server and confirm the game continues after the safe unavailable warning.

Do not use this checklist to capture real dialogue, scan Unity objects, run OCR, or extract game
data.

## Synthetic Event Policy

The built-in event is invented synthetic text only:

```text
The committee pinned a medal on the leaking pipe and called it infrastructure.
```

It is wrapped as:

```json
{
  "input_type": "fake_event",
  "event": {}
}
```

The exact committed safety fixture is:

```text
tests/fixtures/bepinex_bridge.provider_annotate_request.synthetic.json
```

## Safety Check

Run:

```powershell
python scripts/check_bepinex_bridge_safety.py --quiet
```

The check verifies safe defaults, synthetic fixture shape, localhost-only posture, no secret-looking
values, no external service URLs, no raw payload logging, and no hook/extraction/OCR markers in the
C# source. It also verifies local build outputs stay ignored and the optional build helper does not
download tools or become mandatory in `check_all`.

## Not Implemented

- Real current-line detection.
- Real game text extraction.
- Decompiled game-code integration.
- OCR.
- Provider execution.
- Production overlay shell.
- Keyboard hooks.
- Clipboard writes.
- Companion HTTP contract changes.
