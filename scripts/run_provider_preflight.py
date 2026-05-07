from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts.provider_runtime_safety import (
        ProviderRuntimeSafetyError,
        build_provider_execution_plan,
    )
    from scripts.synthetic_slice import ROOT
    from scripts.validate_config import load_config
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from provider_runtime_safety import ProviderRuntimeSafetyError, build_provider_execution_plan
    from synthetic_slice import ROOT
    from validate_config import load_config


DEFAULT_CONFIG = ROOT / "config/revachol.example.toml"
DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/provider-preflight"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a redacted dry-run provider execution plan. This preflight never calls "
            "providers, network services, paid APIs, DeepL, or local model runtimes."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Config TOML path. Defaults to config/revachol.example.toml.",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        help="Provider registry id to preflight. Only mock can pass in this milestone.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/provider-preflight/; unsafe paths are rejected."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short pass/fail line.")
    args = parser.parse_args()

    try:
        output_path = resolve_output_path(args.output) if args.output else None
        config = load_config(args.config)
        plan = build_provider_execution_plan(config, provider_id=args.provider)
    except (OSError, ProviderRuntimeSafetyError, ValueError) as exc:
        parser.error(str(exc))

    rendered = json.dumps(plan, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    if args.quiet:
        status = "passed" if plan["ok"] else "blocked"
        print(f"Provider preflight {status}.")
    elif output_path:
        print(f"Wrote {output_path.relative_to(ROOT)}")
    else:
        print(rendered)

    return 0 if plan["ok"] else 1


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    output_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise ValueError(
            "Unsafe output path. Use a path under "
            "workspace/synthetic-slice/provider-preflight/ for generated preflight artifacts."
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
