# Known Risks

- The repo uses a lightweight local JSON Schema subset validator for Milestone 0 instead of the full `jsonschema` package.
- No real game extraction exists yet; all public fixtures are synthetic.
- Paid APIs and web retrieval are runtime policy/config only right now; tests and CI must stay mocked and offline.
- Runtime caches may contain copyrighted lines or model outputs later, so they must stay under ignored private roots.
- This workspace currently has no `.git` metadata, so local checks cannot inspect tracked-vs-untracked status.
