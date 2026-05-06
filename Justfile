check:
    python scripts/check_all.py

schemas:
    python scripts/validate_schemas.py

config:
    python scripts/validate_config.py --example config/revachol.example.toml

tree:
    python -c "from pathlib import Path; [print(p.as_posix()) for p in sorted(Path('.').rglob('*')) if p.is_file() and '.git' not in p.parts]"
