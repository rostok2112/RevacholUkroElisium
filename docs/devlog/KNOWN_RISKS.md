# Known Risks

- The repo uses a lightweight local JSON Schema subset validator for Milestone 0 instead of the full `jsonschema` package.
- No real game extraction exists yet; all public fixtures are synthetic.
- Paid APIs and web retrieval are runtime policy/config only right now; tests and CI must stay mocked and offline.
- Runtime caches may contain copyrighted lines or model outputs later, so they must stay under ignored private roots.
- The Milestone 1A mock annotation output is deterministic and synthetic; it is not a quality translation engine.
- The Milestone 1B review renderer is static HTML for local review only; no production overlay UI exists yet.
- Unsafe review output paths are rejected rather than normalized. Future tools should keep this explicit behavior unless there is a documented reason to change it.
- The annotation-card schema was not changed for Milestone 1A. Optional helper fields validate because the schema does not forbid additional properties.
