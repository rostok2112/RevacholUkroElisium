import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_SUFFIXES = {".wav", ".ogg", ".mp3", ".assets", ".bundle"}
FORBIDDEN_NAMES = {"database.json"}
SKIP_DIR_NAMES = {".git", "node_modules", ".venv", "venv", "__pycache__"}
PRIVATE_ROOTS = [
    Path(".local-game"),
    Path("data/local"),
    Path("data/extracted"),
    Path("data/generated"),
    Path("extracted"),
    Path("game-data"),
    Path("private-data"),
    Path("workspace"),
    Path(".cache"),
    Path("vector-store"),
    Path("translation-memory/private"),
    Path("audio-index/private"),
    Path("screenshots/private"),
    Path("llm-cache"),
]


def is_under(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True

errors = []
for path in ROOT.rglob("*"):
    rel = path.relative_to(ROOT)
    if any(part in SKIP_DIR_NAMES for part in rel.parts):
        continue
    if any(is_under(rel, private_root) for private_root in PRIVATE_ROOTS):
        continue
    if path.is_file():
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"Forbidden media/game asset file outside private roots: {rel}")
        if path.name in FORBIDDEN_NAMES:
            errors.append(f"Forbidden extracted database file outside private roots: {rel}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print("Repository safety check passed.")
