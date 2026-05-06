# Current Session Plan

Goal: implement Milestone 0 foundation and runtime safety rails.

- Add explicit git ignores for local extraction, generated outputs, private caches, vectors, screenshots, audio indexes, and translation memory.
- Add an idempotent workspace bootstrap script that creates ignored local folders and README placeholders only.
- Add example TOML config plus validation for private path safety, runtime paid-provider settings, and no inline secrets.
- Add lightweight stdlib schema validation for synthetic fixtures and a synthetic end-to-end context-to-annotation example.
- Add unified checks through `scripts/check_all.py`, npm, Justfile, Makefile, and CI.
- Create devlog handoff files so future Codex sessions can resume quickly.

Note: `docs/00-project-vision.md` is absent in this repo. `docs/00-start-here.md` is the current vision entrypoint unless a later session renames or aliases it.
