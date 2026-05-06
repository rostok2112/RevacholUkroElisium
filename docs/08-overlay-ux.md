# Overlay UX

## Desired feel

The overlay should feel like a native reading aid, not a developer debug panel.

## Modes

### Compact mode

Visible by default.

- Original line remains in game.
- Ukrainian translation appears close to the dialogue panel.
- One optional icon signals available annotation.
- No large boxes unless requested.

### Genius mode

Triggered by click/hotkey.

Shows:
- selected phrase,
- Ukrainian explanation,
- idiom/subtext,
- skill/speaker voice,
- optional Ukrainian cultural equivalent,
- "why this translation" note.

### Deep context mode

Side panel with:
- recent dialogue history,
- branch tree around current node,
- audio playback,
- variables/modifiers,
- translation alternatives,
- glossary hits.

### Debug mode

For development only:
- line ID,
- conversation ID,
- retrieval snippets,
- model prompts,
- raw engine outputs,
- eval scores.

## Hotkeys

Suggested defaults:

- `Ctrl+Space`: toggle compact overlay.
- `Ctrl+Shift+Space`: open Genius mode for current line.
- `Ctrl+Alt+D`: debug mode.
- `Ctrl+Alt+S`: spoiler mode toggle.
- `Ctrl+Alt+R`: regenerate current translation.
- `Ctrl+Alt+A`: play associated voice/audio line if available.

## Design guardrails

- Never hide player response options.
- Never cover dice/check UI.
- Avoid long paragraphs in compact mode.
- Keep deep notes one click away, not always visible.
