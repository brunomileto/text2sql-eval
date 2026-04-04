.PHONY: check lint audit security test

check: lint security test

lint:
	@echo "=== LINT ==="
	uv run ruff check .
	uv run ruff format --check .

audit:
	@echo "=== DEPENDENCY AUDIT ==="
	uv run pip-audit

security:
	@echo "=== SECURITY SCAN ==="
	uv run bandit -r src/ -q

test:
	@echo "=== TESTS ==="
	uv run pytest --tb=short -q
