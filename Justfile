set shell := ["bash", "-cu"]

check:
    python scripts/check_repo.py

schemas:
    python scripts/validate_schemas.py

tree:
    find . -maxdepth 3 -type f | sort
