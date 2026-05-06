from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts.provider_pipeline import ProviderPipelineError, run_provider_pipeline
    from scripts.schema_validator import load_json
    from scripts.synthetic_slice import ROOT, build_context_packet
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from provider_pipeline import ProviderPipelineError, run_provider_pipeline
    from schema_validator import load_json
    from synthetic_slice import ROOT, build_context_packet


DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice"
DEFAULT_EVENT = ROOT / "tests/fixtures/fake_game_event.synthetic.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the synthetic provider pipeline. Milestone 2A implements only the "
            "offline deterministic mock provider; real providers are future opt-in."
        )
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--event",
        type=Path,
        default=DEFAULT_EVENT,
        help="Synthetic fake game event JSON. Used by default.",
    )
    source_group.add_argument(
        "--context-packet",
        type=Path,
        help="Synthetic context packet JSON. Must validate against the context schema.",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        choices=["mock"],
        help="Provider to run. Only 'mock' is implemented in Milestone 2A.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional output path. Written artifacts are allowed only under "
            "workspace/synthetic-slice/; unsafe paths are rejected."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Do not print annotation JSON.")
    args = parser.parse_args()

    try:
        context_packet = _load_context_packet(args)
        annotation_card = run_provider_pipeline(context_packet, args.provider)
        rendered = json.dumps(annotation_card, ensure_ascii=False, indent=2)

        if args.output:
            output_path = resolve_output_path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered + "\n", encoding="utf-8")
            print(f"Wrote {output_path.relative_to(ROOT)}")
        elif not args.quiet:
            print(rendered)

        if args.quiet and not args.output:
            print("Provider pipeline mock passed.")
    except (ProviderPipelineError, ValueError) as exc:
        parser.error(str(exc))
    return 0


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    output_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, output_root):
        raise ValueError(
            "Unsafe output path. Use a path under workspace/synthetic-slice/ "
            "for generated synthetic provider artifacts."
        )
    return resolved


def _load_context_packet(args: argparse.Namespace) -> dict[str, object]:
    if args.context_packet:
        loaded = load_json(args.context_packet)
        if not isinstance(loaded, dict):
            raise ProviderPipelineError("Context packet JSON must be an object.")
        return loaded

    event = load_json(args.event)
    if not isinstance(event, dict):
        raise ProviderPipelineError("Synthetic event JSON must be an object.")
    return build_context_packet(event)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
