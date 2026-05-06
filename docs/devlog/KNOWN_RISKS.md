# Known Risks

- The repo uses a lightweight local JSON Schema subset validator for Milestone 0 instead of the full `jsonschema` package.
- No real game extraction exists yet; all public fixtures are synthetic.
- Paid APIs and web retrieval are runtime policy/config only right now; tests and CI must stay mocked and offline.
- Runtime caches may contain copyrighted lines or model outputs later, so they must stay under ignored private roots.
- The Milestone 1A mock annotation output is deterministic and synthetic; it is not a quality translation engine.
- The Milestone 1B review renderer is static HTML for local review only; no production overlay UI exists yet.
- The Milestone 1C eval harness scores structural coverage only. It does not measure real semantic accuracy, Ukrainian literary quality, or player comprehension yet.
- Multiple Milestone 1C cases currently share the same deterministic mock annotation output, so score variation mostly comes from input glossary/context shape and tampering tests.
- The Milestone 1D companion server is a stdlib localhost skeleton only. It is not production security hardened.
- The Milestone 1D server stores latest context/annotation/overlay/eval state in memory only; state disappears on restart.
- The Milestone 1D default bind is `127.0.0.1`, but the CLI allows an explicit different host. Do not expose it beyond localhost without a later security review.
- The Milestone 1D HTTP API has no auth, TLS, persistence, rate limiting, CORS policy, or multi-client session model yet.
- Unsafe review output paths are rejected rather than normalized. Future tools should keep this explicit behavior unless there is a documented reason to change it.
- The annotation-card schema was not changed for Milestone 1A. Optional helper fields validate because the schema does not forbid additional properties.
