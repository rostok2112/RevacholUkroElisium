from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts.schema_validator import load_json
    from scripts.synthetic_review_renderer import render_review_html
    from scripts.synthetic_slice import ROOT, run_synthetic_slice
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from schema_validator import load_json
    from synthetic_review_renderer import render_review_html
    from synthetic_slice import ROOT, run_synthetic_slice


DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the synthetic Milestone 1A/1B slice.")
    parser.add_argument(
        "--event",
        type=Path,
        default=ROOT / "tests/fixtures/fake_game_event.synthetic.json",
        help="Synthetic fake game event JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/; unsafe paths are rejected."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Do not print the full JSON payload.")
    parser.add_argument(
        "--render-review",
        action="store_true",
        help="Render a static HTML review artifact instead of JSON.",
    )
    args = parser.parse_args()

    event = load_json(args.event)
    result = run_synthetic_slice(event)
    rendered = (
        render_review_html(result)
        if args.render_review
        else json.dumps(result, ensure_ascii=False, indent=2)
    )

    if args.output:
        try:
            output_path = _resolve_output(args.output)
        except ValueError as exc:
            parser.error(str(exc))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {output_path.relative_to(ROOT)}")
    elif not args.quiet:
        print(rendered)

    if args.quiet and not args.output:
        label = "Synthetic review" if args.render_review else "Synthetic slice"
        print(f"{label} passed.")
    return 0


def _resolve_output(output: Path) -> Path:
    raw = output.expanduser()
    resolved = raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    output_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise ValueError(
            "Unsafe output path. Use a path under workspace/synthetic-slice/ "
            "for generated synthetic artifacts."
        )
    return resolved


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
