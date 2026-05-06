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

## Distribution model

Recommended:
- distribute code and tooling only,
- require user to point the tool at their local game install,
- generate indexes locally,
- never ship ZA/UM content.

## Scribe and other fan tools

Treat public fan tools as design references. Do not scrape and redistribute their content unless license and rights are explicit and compatible.
