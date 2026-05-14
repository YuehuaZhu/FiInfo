.PHONY: install daily daily-real test lint clean

install:
	uv venv && uv pip install -e ".[dev]"
	uv run playwright install chromium

test:
	uv run pytest -q

lint:
	uv run ruff check src tests

daily:
	uv run python -m fiinfo.cli daily --source fixture --force-mock-llm

daily-real:
	uv run python -m fiinfo.cli daily

clean:
	rm -rf data/ outbox/ .pytest_cache/ .ruff_cache/
