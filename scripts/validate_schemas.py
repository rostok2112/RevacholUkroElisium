from pathlib import Path
import json

for path in Path("specs").glob("*.json"):
    with path.open("r", encoding="utf-8") as f:
        json.load(f)
    print(f"OK {path}")
