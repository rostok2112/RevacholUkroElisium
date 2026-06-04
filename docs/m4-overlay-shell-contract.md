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

The compact translation shell helper is:

```text
scripts/run_m4_overlay_shell.py
```

It renders local/private compact HTML from validated compact view models and keeps original/source
text, debug internals, provider payloads, screenshots, private paths, global keyboard hooks,
clipboard writes, native always-on-top behavior, provider execution, and companion HTTP changes out
of the shell summary and player-facing compact HTML. The next bounded step after the compact shell
is:

```text
m4_genius_card_shell
```

The Genius card rendering is implemented in the same helper. It consumes the existing deep overlay
view model and renders an expandable local browser card with `<details>/<summary>`. It does not
emit source/original text, line ids, provider payloads, private paths, screenshots, or debug
internals in player-facing shell HTML. The next bounded M4 step is:

```text
m4_overlay_hotkeys
```
