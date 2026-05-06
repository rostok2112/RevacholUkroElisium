---
name: copyright-safe-modding
description: Keep the project legally safer by preventing game text, audio, images, and extracted proprietary data from entering the repo.
---

# Copyright-safe Modding Skill

Use before committing extraction, import, fixture, screenshot, audio, or fan-tool data.

## Hard rules

Do not commit:
- original game dialogue,
- extracted database,
- voice lines,
- images,
- music,
- translated full script containing original alignment,
- substantial screenshots with copyrighted text.

Allowed:
- schemas,
- code,
- prompts,
- synthetic examples,
- local-only extraction scripts,
- tiny non-infringing snippets only if legally reviewed.

## Useful files

- `docs/09-legal-and-data-safety.md`
- `.gitignore`
- `scripts/check_repo.py`
