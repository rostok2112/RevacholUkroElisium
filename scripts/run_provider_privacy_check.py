from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts.provider_pipeline import ProviderPipelineError, build_provider_request
    from scripts.provider_privacy import ProviderPrivacyError, build_provider_privacy_envelope
    from scripts.provider_runtime_safety import (
        ProviderRuntimeSafetyError,
        build_provider_execution_plan,
    )
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT, build_context_packet
    from scripts.validate_config import load_config
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from provider_pipeline import ProviderPipelineError, build_provider_request
    from provider_privacy import ProviderPrivacyError, build_provider_privacy_envelope
    from provider_runtime_safety import ProviderRuntimeSafetyError, build_provider_execution_plan
    from schema_validator import load_json
    from synthetic_slice import ROOT, build_context_packet
    from validate_config import load_config


DEFAULT_CONFIG = ROOT / "config/revachol.example.toml"
DEFAULT_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"
DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/provider-privacy"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a redacted provider request privacy envelope and cache-write dry-run. "
            "This command never calls providers, network services, paid APIs, DeepL, "
            "or local model runtimes."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Config TOML path. Defaults to config/revachol.example.toml.",
    )
    parser.add_argument(
        "--event",
        type=Path,
        default=DEFAULT_EVENT,
        help="Synthetic fake game event JSON. Used by default.",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        help="Provider registry id to check. Only mock can produce an envelope.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/provider-privacy/; unsafe paths are rejected."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short pass/fail line.")
    args = parser.parse_args()

    try:
        output_path = resolve_output_path(args.output) if args.output else None
        config = load_config(args.config)
        plan = build_provider_execution_plan(config, provider_id=args.provider)
        if plan["ok"]:
            event = load_json(args.event)
            if not isinstance(event, dict):
                raise ProviderPrivacyError("Synthetic event JSON must be an object.")
            context_packet = build_context_packet(event)
            request = build_provider_request(context_packet, provider_name=args.provider)
            summary = {
                "schema_version": "provider-privacy-check.v1",
                "ok": True,
                "execution_plan": plan,
                "privacy_envelope": build_provider_privacy_envelope(request, config, plan),
            }
        else:
            summary = {
                "schema_version": "provider-privacy-check.v1",
                "ok": False,
                "execution_plan": plan,
                "privacy_envelope": None,
            }
    except (
        OSError,
        ProviderPipelineError,
        ProviderPrivacyError,
        ProviderRuntimeSafetyError,
        ValueError,
    ) as exc:
        parser.error(str(exc))

    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")

    if args.quiet:
        status = "passed" if summary["ok"] else "blocked"
        print(f"Provider privacy check {status}.")
    elif output_path:
        print(f"Wrote {output_path.relative_to(ROOT)}")
    else:
        print(rendered)

    return 0 if summary["ok"] else 1


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    output_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise ValueError(
            "Unsafe output path. Use a path under "
            "workspace/synthetic-slice/provider-privacy/ for generated privacy artifacts."
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
