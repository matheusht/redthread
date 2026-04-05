.PHONY: lint typecheck test test-golden ci dev install

# ── Help ─────────────────────────────────────────────────────────────────────

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

# ── Code Quality ─────────────────────────────────────────────────────────────

lint:  ## Ruff lint check (no auto-fix)
	.venv/bin/ruff check src/ tests/

lint-fix:  ## Ruff lint with auto-fix
	.venv/bin/ruff check --fix src/ tests/

typecheck:  ## Mypy strict type check
	.venv/bin/mypy src/redthread/

# ── Tests ─────────────────────────────────────────────────────────────────────

test:  ## Unit tests (no API calls)
	PYTHONPATH=src REDTHREAD_DRY_RUN=true \
	.venv/bin/pytest tests/ \
		--ignore=tests/test_golden_dataset.py \
		-v --tb=short

test-golden:  ## Golden Dataset regression (requires OPENAI_API_KEY)
	PYTHONPATH=src \
	.venv/bin/pytest tests/test_golden_dataset.py \
		-v --tb=short

# ── CI ────────────────────────────────────────────────────────────────────────

ci: lint typecheck test  ## Full local CI: lint + typecheck + unit tests

ci-full: lint typecheck test test-golden  ## Full CI including golden regression

# ── Project Setup ─────────────────────────────────────────────────────────────

dev:  ## Install with dev dependencies (editable mode)
	pip install -e ".[dev]"

install:  ## Install in editable mode (no dev extras)
	pip install -e .

# ── Dashboard & Monitoring ────────────────────────────────────────────────────

dashboard:  ## View campaign history dashboard
	.venv/bin/redthread dashboard

monitor:  ## Start the Security Guard daemon
	.venv/bin/redthread monitor start

status:  ## Show current ASI health status
	.venv/bin/redthread monitor status

# ── Local Models & Inference ──────────────────────────────────────────────────

llama-cpp-setup:  ## Clone and build llama.cpp from source (macOS Metal optimized)
	@if [ ! -d "vendor/llama.cpp" ]; then \
		mkdir -p vendor && git clone https://github.com/ggml-org/llama.cpp vendor/llama.cpp; \
	fi
	cd vendor/llama.cpp && make -j

model-setup:  ## Pull Gemma 4 E4B model via Ollama
	ollama pull gemma4:e4b
