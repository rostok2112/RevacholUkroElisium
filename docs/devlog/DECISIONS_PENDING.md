# Decisions Pending

- Whether to add a full JSON Schema dependency later or keep the local validator small.
- Whether the companion server starts as Python, TypeScript, or a split service.
- Which overlay stack to use for the first real UI prototype.
- How to structure lawful opt-in web enrichment and source attribution.
- Whether to rename or alias `docs/00-start-here.md` as `docs/00-project-vision.md`.
- Whether to keep the actual repository spelling `revachol-ukro-elisium` long-term or introduce a documented `elysium` alias later.
- Whether future annotation-card helper fields should remain permissive additional properties or become explicit optional schema properties.
- Whether future review artifacts should stay static HTML, add Markdown output, or wait for a real overlay prototype.
- Which synthetic eval dimensions should graduate from Milestone 1C checks into the long-term eval framework.
- Milestone 1D chose a stdlib `http.server` skeleton first; decide later whether to keep it, wrap it, or replace it with a production service framework.
- How soon to split deterministic mocks from future provider-backed translation/annotation adapters.
- Milestone 1E chose a tiny stdlib local client and API contract doc before provider work.
- Milestone 2A provider abstractions live under `scripts/` initially; decide later when to move toward a package layout.
- How to version provider prompt contracts before real paid API or local model adapters are enabled.
- Whether Milestone 2B should introduce a dedicated prompt/style pack manifest or keep prompt loading as simple file reads.
- Whether provider annotation should be exposed through companion server/client in Milestone 2B or wait until a richer mock/eval pass exists.
