from __future__ import annotations

import argparse
import json
import sys

try:
    from scripts.provider_registry import provider_summary
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from provider_registry import provider_summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect the local provider registry. This command never calls providers, "
            "external services, paid APIs, DeepL, or local model runtimes."
        )
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print provider registry summary JSON. This is also the default behavior.",
    )
    parser.add_argument("--quiet", action="store_true", help="Print only a short pass message.")
    args = parser.parse_args()

    summary = provider_summary()
    if args.quiet:
        print("Provider registry summary passed.")
    else:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
