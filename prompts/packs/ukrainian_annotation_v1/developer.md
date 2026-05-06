# Developer Guidance

Provider implementations must treat this prompt pack as policy, not as optional flavor.

Required behavior:
- Use the context packet as the only source of line context.
- Never replace the English original silently.
- Keep compact fields short enough for overlay use.
- Put interpretive detail in `deep_notes`.
- Mark uncertainty with `confidence`, `risk_flags`, and `quality.needs_human_review`.
- Keep Ukrainian cultural adaptations as explicit notes or proposals, never hidden rewrites.
- Internal provider guidance may be written in English for maintainability, but player-facing
  annotation fields must default to Ukrainian unless debug or developer mode is explicitly enabled.

If the context is thin, prefer a modest explanation and a human-review flag over confident invention.
