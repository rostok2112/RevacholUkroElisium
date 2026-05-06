from pathlib import Path
import sys

FORBIDDEN_SUFFIXES = {".wav", ".ogg", ".mp3", ".assets", ".bundle"}
FORBIDDEN_NAMES = {"database.json"}

errors = []
for path in Path(".").rglob("*"):
    if ".git" in path.parts:
        continue
    if path.is_file():
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"Forbidden media/game asset file: {path}")
        if path.name in FORBIDDEN_NAMES:
            errors.append(f"Forbidden extracted database file: {path}")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print("Repository safety check passed.")
