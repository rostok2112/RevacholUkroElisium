from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from scripts.check_bepinex_runtime_smoke_report import (
        REPORT_ROOT,
        canonical_json,
        default_report_template,
        ensure_safe_report_path,
    )
except ModuleNotFoundError:  # pragma: no cover - script execution from scripts/
    from check_bepinex_runtime_smoke_report import (
        REPORT_ROOT,
        canonical_json,
        default_report_template,
        ensure_safe_report_path,
    )


DEFAULT_OUTPUT = REPORT_ROOT / "report.template.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write a blank redacted BepInEx runtime smoke report template."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Template path under workspace/synthetic-slice/bepinex-bridge/runtime-smoke/.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short success line.")
    args = parser.parse_args(argv)

    try:
        output_path = ensure_safe_report_path(Path(args.output))
    except Exception as exc:
        parser.error(str(exc))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical_json(default_report_template()), encoding="utf-8")

    if args.quiet:
        print("BepInEx runtime smoke report template written.")
    else:
        print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
