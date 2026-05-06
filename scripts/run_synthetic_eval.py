from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts.synthetic_eval import get_synthetic_eval_cases, run_eval_case, run_synthetic_eval
    from scripts.synthetic_slice import ROOT
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from synthetic_eval import get_synthetic_eval_cases, run_eval_case, run_synthetic_eval
    from synthetic_slice import ROOT


DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic structural evals for synthetic slice coverage."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/; unsafe paths are rejected."
        ),
    )
    parser.add_argument(
        "--write-reviews",
        action="store_true",
        help="Write per-case review HTML under workspace/synthetic-slice/eval/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Do not print JSON summary to stdout.")
    args = parser.parse_args()

    summary = run_synthetic_eval()
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)

    if args.output:
        try:
            output_path = resolve_output_path(args.output)
        except ValueError as exc:
            parser.error(str(exc))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {output_path.relative_to(ROOT)}")
    elif not args.quiet:
        print(rendered)

    if args.write_reviews:
        review_dir = DEFAULT_OUTPUT_ROOT / "eval"
        review_dir.mkdir(parents=True, exist_ok=True)
        for case in get_synthetic_eval_cases():
            result = run_eval_case(case)
            review_path = review_dir / f"{_safe_slug(case.case_id)}.html"
            review_path.write_text(result.review_html + "\n", encoding="utf-8")
            print(f"Wrote {review_path.relative_to(ROOT)}")

    if args.quiet and not args.output and not args.write_reviews:
        print("Synthetic eval passed.")
    return 0 if summary["passed"] else 1


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    output_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise ValueError(
            "Unsafe output path. Use a path under workspace/synthetic-slice/ "
            "for generated synthetic eval artifacts."
        )
    return resolved


def _safe_slug(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_" else "_" for char in value)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
