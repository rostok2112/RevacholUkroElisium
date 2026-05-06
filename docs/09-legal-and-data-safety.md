# Legal and Data Safety

## Public repo rule

Do not commit:

- extracted dialogue database,
- `.po`, `.transl`, or generated translation files containing original game text,
- voice lines,
- images,
- portraits,
- music,
- screenshots containing substantial copyrighted text,
- proprietary game binaries.

## Allowed in repo

- code,
- schemas,
- prompt templates,
- synthetic examples,
- tiny paraphrased examples,
- user-created glossaries that do not reproduce game text,
- documentation,
- tests with synthetic fixtures.

## Local user data

The user may extract data from their own local installation for private use. Store it under ignored paths such as:

- `.local-game/`
- `extracted/`
- `private-data/`

Current preferred private roots also include:

- `data/local/`
- `data/extracted/`
- `data/generated/`
- `workspace/`
- `llm-cache/`
- `vector-store/`
- `translation-memory/private/`
- `audio-index/private/`
- `screenshots/private/`

## Runtime API and web policy

Paid APIs are allowed during real product use when the user explicitly configures provider environment variables. Tests and CI must use deterministic mocks and must not call paid providers.

Web retrieval or scraping is allowed only as a future opt-in runtime enrichment feature for lawful sources with attribution and ignored local caches. Do not scrape or redistribute Disco Elysium dialogue/script mirrors, fan dialogue databases, audio, images, screenshots, or localization tables. Exact game context must come from the user's legally installed local copy.

## Distribution model

Recommended:
- distribute code and tooling only,
- require user to point the tool at their local game install,
- generate indexes locally,
- never ship ZA/UM content.

## Scribe and other fan tools

Treat public fan tools as design references. Do not scrape and redistribute their content unless license and rights are explicit and compatible.
