# BepInEx Plugin Design

## Responsibilities

- Hook or observe text display events.
- Resolve current line ID where possible.
- Emit current state to `127.0.0.1`.
- Avoid altering game text in the first milestone.
- Provide debug logs and version info.

## Anti-goals

- No API keys in plugin.
- No cloud calls from plugin.
- No bundled translation database.
- No destructive asset replacement in MVP.

## Future

- Optional in-game UI injection.
- Optional audio reference emission.
- Optional live reload for translator/debug mode.
