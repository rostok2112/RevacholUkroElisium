from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

try:
    from scripts.overlay_state_simulator import (
        OverlayStateSimulatorError,
        simulate_overlay_action,
    )
    from scripts.render_overlay_review import MODES, load_view_model_fixture
    from scripts.synthetic_slice import ROOT
except ImportError:  # pragma: no cover - used when run as a script path.
    from overlay_state_simulator import OverlayStateSimulatorError, simulate_overlay_action
    from render_overlay_review import MODES, load_view_model_fixture
    from synthetic_slice import ROOT


DEFAULT_OUTPUT_ROOT = ROOT / "workspace/synthetic-slice/overlay-prototype/transitions"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Preview a declared overlay action/state transition from committed synthetic "
            "view-model fixtures. This performs no UI, clipboard, keyboard, provider, or "
            "companion-server side effects."
        )
    )
    parser.add_argument(
        "--fixture",
        choices=MODES,
        default="compact",
        help="Committed overlay view-model fixture to load.",
    )
    parser.add_argument("--action", required=True, help="Declared overlay action id to preview.")
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional JSON output path. Must be under "
            "workspace/synthetic-slice/overlay-prototype/transitions/."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print a short status line.")
    args = parser.parse_args()

    try:
        output_path = resolve_output_path(args.output) if args.output else None
        view_model = load_view_model_fixture(args.fixture)
        preview = simulate_overlay_action(view_model, args.action)
        if output_path:
            _write_preview(output_path, preview)
    except (OverlayStateSimulatorError, OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.quiet:
        if preview["allowed"]:
            print("Overlay state transition preview passed.")
        else:
            print(
                f"Overlay state transition preview blocked: {preview['blocked_reason']}",
                file=sys.stderr,
            )
    else:
        print(json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if preview["allowed"] else 1


def resolve_output_path(output: Path) -> Path:
    raw = output.expanduser()
    resolved = (
        raw.resolve(strict=False) if raw.is_absolute() else (ROOT / raw).resolve(strict=False)
    )
    allowed_root = DEFAULT_OUTPUT_ROOT.resolve(strict=False)
    if not _is_relative_to(resolved, allowed_root):
        raise ValueError(
            "Unsafe output path. Use a path under "
            "workspace/synthetic-slice/overlay-prototype/transitions/ for generated "
            "transition previews."
        )
    return resolved


def _write_preview(output_path: Path, preview: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(preview, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
