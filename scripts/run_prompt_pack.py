from __future__ import annotations

import argparse
import json
import sys

try:
    from scripts.prompt_pack import DEFAULT_PACK_ID, PromptPackError, load_prompt_pack
except ModuleNotFoundError:  # pragma: no cover - used when run as a script path.
    from prompt_pack import DEFAULT_PACK_ID, PromptPackError, load_prompt_pack


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a local prompt pack. This command never calls providers or APIs."
    )
    parser.add_argument(
        "--pack",
        default=DEFAULT_PACK_ID,
        help="Prompt pack id to load. Default: ukrainian_annotation_v1.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a deterministic JSON summary of prompt pack metadata.",
    )
    args = parser.parse_args()

    try:
        pack = load_prompt_pack(args.pack)
    except PromptPackError as exc:
        parser.error(str(exc))

    summary = pack.summary()
    summary["loaded_policy_count"] = len(pack.policy_texts)
    summary["synthetic_examples_chars"] = len(pack.synthetic_examples)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
