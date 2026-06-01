from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.m2_synthetic_import_validator import (
        ALLOWED_RELATIONS as _ALLOWED_RELATIONS,
        RECOMMENDED_NEXT_STEP,
        SAFETY_FLAG_FIELDS as _SAFETY_FLAG_FIELDS,
        SCHEMA_VERSION,
        SOURCE_KIND,
        collect_m2_synthetic_import_errors,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from m2_synthetic_import_validator import (
        ALLOWED_RELATIONS as _ALLOWED_RELATIONS,
        RECOMMENDED_NEXT_STEP,
        SAFETY_FLAG_FIELDS as _SAFETY_FLAG_FIELDS,
        SCHEMA_VERSION,
        SOURCE_KIND,
        collect_m2_synthetic_import_errors,
    )
    from schema_validator import load_json
    from synthetic_slice import ROOT


FIXTURE_PATH = ROOT / "tests/fixtures/m2_synthetic_import_db.synthetic.json"
DOC_PATH = ROOT / "docs/m2-synthetic-import-format-contract.md"
ADR_PATH = ROOT / "docs/adr/0012-m2-local-extraction-import-scope.md"
SESSION_SUMMARY_PATH = ROOT / "docs/devlog/SESSION_SUMMARY.md"
NEXT_ACTIONS_PATH = ROOT / "docs/devlog/NEXT_ACTIONS.md"
ALLOWED_RELATIONS = _ALLOWED_RELATIONS
SAFETY_FLAG_FIELDS = _SAFETY_FLAG_FIELDS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the M2 synthetic import format.")
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass/fail line.")
    args = parser.parse_args(argv)

    errors = collect_m2_synthetic_import_format_errors()
    if errors:
        if args.quiet:
            print("M2 synthetic import format check failed.")
        else:
            print("\n".join(errors))
        return 1

    if args.quiet:
        print("M2 synthetic import format check passed.")
    else:
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema_version": "m2-synthetic-import-format-check.v1",
                    "fixture_schema_version": SCHEMA_VERSION,
                    "source_kind": SOURCE_KIND,
                    "implementation_added": False,
                    "recommended_next_step": RECOMMENDED_NEXT_STEP,
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


def collect_m2_synthetic_import_format_errors(path: Path = FIXTURE_PATH) -> list[str]:
    try:
        payload = load_json(path)
    except Exception as exc:
        return [f"Could not load M2 synthetic import fixture: {exc}"]

    errors = collect_m2_synthetic_import_errors(payload)
    if path == FIXTURE_PATH:
        errors.extend(_doc_errors())
    return errors


def _doc_errors() -> list[str]:
    errors: list[str] = []
    required_refs = (
        "docs/m2-synthetic-import-format-contract.md",
        "specs/m2-synthetic-import-db.schema.json",
        "scripts/m2_synthetic_import_validator.py",
        "scripts/check_m2_synthetic_import_format.py",
        "tests/fixtures/m2_synthetic_import_db.synthetic.json",
    )
    for path in (DOC_PATH, ADR_PATH, SESSION_SUMMARY_PATH, NEXT_ACTIONS_PATH):
        if not path.exists():
            errors.append(f"Missing M2 synthetic import format doc: {_display_path(path)}.")
            continue
        text = path.read_text(encoding="utf-8").replace("\\", "/")
        for required in required_refs:
            if required not in text:
                errors.append(f"{_display_path(path)} must point to {required}.")
    return errors


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve(strict=False).relative_to(ROOT.resolve(strict=False))).replace(
            "\\", "/"
        )
    except ValueError:
        return path.name


if __name__ == "__main__":
    raise SystemExit(main())
