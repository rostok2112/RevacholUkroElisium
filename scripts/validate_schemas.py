from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

from schema_validator import collect_errors, load_json


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class FixtureCase:
    schema_path: Path
    fixture_path: Path
    expected_valid: bool


FIXTURE_CASES = [
    FixtureCase(
        ROOT / "specs/context-packet.schema.json",
        ROOT / "tests/fixtures/context_packet.synthetic.json",
        True,
    ),
    FixtureCase(
        ROOT / "specs/context-packet.schema.json",
        ROOT / "tests/fixtures/context_packet.invalid.synthetic.json",
        False,
    ),
    FixtureCase(
        ROOT / "specs/annotation-card.schema.json",
        ROOT / "tests/fixtures/annotation_card.synthetic.json",
        True,
    ),
    FixtureCase(
        ROOT / "specs/annotation-card.schema.json",
        ROOT / "tests/fixtures/annotation_card.invalid.synthetic.json",
        False,
    ),
    FixtureCase(
        ROOT / "specs/glossary-entry.schema.json",
        ROOT / "tests/fixtures/glossary_entry.synthetic.json",
        True,
    ),
    FixtureCase(
        ROOT / "specs/glossary-entry.schema.json",
        ROOT / "tests/fixtures/glossary_entry.invalid.synthetic.json",
        False,
    ),
    FixtureCase(
        ROOT / "specs/fake-game-event.schema.json",
        ROOT / "tests/fixtures/fake_game_event.synthetic.json",
        True,
    ),
    FixtureCase(
        ROOT / "specs/fake-game-event.schema.json",
        ROOT / "tests/fixtures/fake_game_event.invalid.synthetic.json",
        False,
    ),
]


def main() -> int:
    errors: list[str] = []
    schemas: dict[Path, dict] = {}

    for path in sorted((ROOT / "specs").glob("*.schema.json")):
        try:
            schemas[path] = load_json(path)
        except Exception as exc:
            errors.append(f"Could not parse schema {path.relative_to(ROOT)}: {exc}")
            continue
        print(f"OK schema JSON {path.relative_to(ROOT)}")

    for case in FIXTURE_CASES:
        schema = schemas.get(case.schema_path)
        if schema is None:
            errors.append(f"Missing loaded schema for {case.schema_path.relative_to(ROOT)}")
            continue

        try:
            fixture = load_json(case.fixture_path)
        except Exception as exc:
            errors.append(f"Could not parse fixture {case.fixture_path.relative_to(ROOT)}: {exc}")
            continue

        fixture_errors = collect_errors(fixture, schema)
        label = case.fixture_path.relative_to(ROOT)
        if case.expected_valid and fixture_errors:
            errors.append(f"{label} should be valid: {'; '.join(fixture_errors)}")
        elif not case.expected_valid and not fixture_errors:
            errors.append(f"{label} should be rejected but passed")
        elif case.expected_valid:
            print(f"OK valid fixture {label}")
        else:
            print(f"OK rejected fixture {label}")

    errors.extend(_validate_e2e_fixture(schemas))

    if errors:
        print("\n".join(errors))
        return 1

    print("Schema validation passed.")
    return 0


def _validate_e2e_fixture(schemas: dict[Path, dict]) -> list[str]:
    fixture_path = ROOT / "tests/fixtures/synthetic_e2e_example.json"
    errors: list[str] = []
    try:
        fixture = load_json(fixture_path)
    except Exception as exc:
        return [f"Could not parse fixture {fixture_path.relative_to(ROOT)}: {exc}"]

    context_schema = schemas[ROOT / "specs/context-packet.schema.json"]
    annotation_schema = schemas[ROOT / "specs/annotation-card.schema.json"]
    context_errors = collect_errors(fixture.get("context_packet"), context_schema)
    annotation_errors = collect_errors(fixture.get("annotation_card"), annotation_schema)

    if context_errors:
        errors.append(f"{fixture_path.relative_to(ROOT)} context_packet invalid: {context_errors}")
    if annotation_errors:
        errors.append(
            f"{fixture_path.relative_to(ROOT)} annotation_card invalid: {annotation_errors}"
        )

    if not errors:
        print(f"OK e2e fixture {fixture_path.relative_to(ROOT)}")
    return errors


if __name__ == "__main__":
    sys.exit(main())
