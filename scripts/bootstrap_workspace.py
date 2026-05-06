from __future__ import annotations

import argparse
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PRIVATE_FOLDERS = {
    "workspace": "General private runtime workspace for local state and experiments.",
    "data/local": "Local-only user data derived from a legally installed copy.",
    "data/extracted": "Private extraction output. Do not commit game text, tables, or assets.",
    "data/generated": "Generated private artifacts such as indexes or full translation drafts.",
    "llm-cache": "Private prompt, response, and provider cache data.",
    "vector-store": "Private embeddings and retrieval indexes.",
    "translation-memory/private": "User-reviewed private translation memory.",
    "audio-index/private": "Private audio metadata and local references.",
    "screenshots/private": "Private screenshots for debugging only.",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create ignored local workspace folders.")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config/revachol.example.toml",
        help="Config file to read additional private paths from.",
    )
    args = parser.parse_args()

    folders = dict(DEFAULT_PRIVATE_FOLDERS)
    folders.update(_paths_from_config(args.config))

    for relative_path, purpose in sorted(folders.items()):
        folder = _resolve_repo_relative(relative_path)
        folder.mkdir(parents=True, exist_ok=True)
        readme = folder / "README.local.md"
        if not readme.exists():
            readme.write_text(_readme_text(relative_path, purpose), encoding="utf-8")
        label = folder.relative_to(ROOT) if _is_relative_to(folder, ROOT) else folder
        print(f"OK {label}")

    print("Workspace bootstrap complete. No game data was extracted.")
    return 0


def _paths_from_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    with path.open("rb") as handle:
        config = tomllib.load(handle)

    folders: dict[str, str] = {}
    paths = config.get("paths", {})
    if isinstance(paths, dict):
        for key, value in paths.items():
            if key == "game_install_path" or not key.endswith("_path"):
                continue
            if isinstance(value, str) and value.strip():
                folders[value] = f"Configured private path from paths.{key}."

    network = config.get("network_enrichment", {})
    if isinstance(network, dict):
        cache_path = network.get("cache_path")
        if isinstance(cache_path, str) and cache_path.strip():
            folders[cache_path] = "Private opt-in web enrichment cache."

    return folders


def _readme_text(relative_path: str, purpose: str) -> str:
    return (
        "# Local Private Workspace\n\n"
        f"Path: `{relative_path}`\n\n"
        f"Purpose: {purpose}\n\n"
        "This folder is intentionally ignored by git. It may contain local game extraction output, "
        "private caches, prompts, model responses, screenshots, generated indexes, or user review "
        "data. Do not move its contents into public repo paths.\n"
    )


def _resolve_repo_relative(path: str | Path) -> Path:
    raw = Path(path).expanduser()
    if raw.is_absolute():
        return raw.resolve(strict=False)
    return (ROOT / raw).resolve(strict=False)


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
