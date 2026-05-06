.PHONY: check schemas config test

check:
	python scripts/check_all.py

schemas:
	python scripts/validate_schemas.py

config:
	python scripts/validate_config.py --example config/revachol.example.toml

test:
	python -m unittest discover -s tests -p "test_*.py"
