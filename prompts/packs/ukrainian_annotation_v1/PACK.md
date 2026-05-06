# Ukrainian Annotation Prompt Pack v1

This pack defines synthetic-only guidance for Ukrainian translation and annotation providers.
It is a contract aid, not a model integration.

Core intent:
- Preserve the English original as canonical context.
- Give the player playable Ukrainian comprehension, not a destructive replacement.
- Put nuance in annotations when compact translation would become too heavy.
- Keep uncertainty visible through confidence, risk flags, and human-review signals.
- Use only invented synthetic examples in public tests and docs.

This pack is compatible with `scripts/provider_pipeline.py` and the deterministic mock provider.
Future real providers must remain opt-in and must respect local/private cache boundaries.
