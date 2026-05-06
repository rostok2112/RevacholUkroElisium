# Start Here

This project should be developed as a **quality-first companion**, not as a simple machine translation patch.

The intended player experience:

1. The game is still visually and narratively Disco Elysium.
2. English remains visible and trusted.
3. Ukrainian appears as a helper layer:
   - concise translation,
   - one-line explanation,
   - expandable annotation,
   - optional Ukrainian cultural resonance,
   - audio/tone notes when useful.
4. The player never needs to alt-tab, use phone OCR, or paste text manually during normal play.

## Recommended first coding order

1. Define contracts: `specs/context-packet.schema.json`, `specs/annotation-card.schema.json`.
2. Build local extraction/import pipeline from user-owned game files.
3. Build a fake-game harness with synthetic lines.
4. Build companion service WebSocket + overlay prototype.
5. Build one conversation vertical slice.
6. Add translation evals.
7. Only then optimize BepInEx integration and UX polish.
