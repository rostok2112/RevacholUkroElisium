from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT, run_synthetic_slice
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from schema_validator import load_json
    from synthetic_slice import ROOT, run_synthetic_slice


DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice"
APPROVED_OUTPUT_ROOTS = [
    ROOT / "workspace",
    ROOT / "data/generated",
    ROOT / "llm-cache",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the synthetic Milestone 1A vertical slice.")
    parser.add_argument(
        "--event",
        type=Path,
        default=ROOT / "tests/fixtures/fake_game_event.synthetic.json",
        help="Synthetic fake game event JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path under an ignored demo/private directory.",
    )
    parser.add_argument("--quiet", action="store_true", help="Do not print the full JSON payload.")
    args = parser.parse_args()

    event = load_json(args.event)
    result = run_synthetic_slice(event)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        output_path = _resolve_output(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {output_path.relative_to(ROOT)}")
    elif not args.quiet:
        print(rendered)

    if args.quiet and not args.output:
        print("Synthetic slice passed.")
    return 0


def _resolve_output(output: Path) -> Path:
    raw = output.expanduser()
    resolved = raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    approved_roots = [path.resolve(strict=False) for path in APPROVED_OUTPUT_ROOTS]
    if not any(_is_relative_to(resolved, root) for root in approved_roots):
        fallback = DEFAULT_OUTPUT_ROOT / output.name
        resolved = fallback.resolve(strict=False)
    return resolved


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
