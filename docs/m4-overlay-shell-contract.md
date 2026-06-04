# M4 Overlay Shell Contract

This contract defines the first real overlay shell boundary for original `M4 - Real overlay`.

It is a local browser shell contract. It does not add native always-on-top packaging, Electron,
Tauri, global keyboard hooks, clipboard writes, provider execution, companion HTTP contract changes,
OCR, Unity scanning, hooks/Harmony, game-file reads, BepInEx log reads, screenshots, or committed
generated shell artifacts.

## Inputs

The shell may consume only validated overlay state generated from existing contracts:

- `overlay-state-source.v1`;
- `local-overlay-prototype.v1` compact and deep view models;
- committed synthetic fixtures for self-tests.

The shell must reuse `scripts/overlay_state_source.py`, `scripts/local_overlay_prototype.py`,
`scripts/overlay_viewmodel_validator.py`, and `scripts/overlay_actions.py`. It must not invent a
parallel view-model or state-source schema.

## Output Boundary

A future shell helper may write generated HTML only under:

```text
workspace/local-private/overlay/
```

Generated shell files are local/private artifacts and must not be committed.

## Player-Facing Behavior

The shell may render:

- compact Ukrainian translation from the compact view model;
- an expandable Genius card from the existing deep view model;
- page-local hotkeys that affect only the loaded browser page.

The shell must not render raw provider payloads, private paths, logs, screenshots, debug internals,
raw prompt text, or generated cache payloads in player-facing compact or Genius views.

## Guardrail

The shell contract fixture and checker are:

```text
docs/m4-overlay-shell-contract.md
tests/fixtures/m4_overlay_shell_contract.synthetic.json
scripts/check_m4_overlay_shell_contract.py
```

Validate with:

```powershell
python scripts/check_m4_overlay_shell_contract.py --quiet
```

The next bounded M4 step is:

```text
m4_compact_translation_shell
```
