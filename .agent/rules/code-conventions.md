---
alwaysApply: true
---

# Code Conventions Rule

Conventions that **every edit** must follow, regardless of scope.

## Python (RedThread — `src/redthread/`)

- **Python 3.12+** — use `from __future__ import annotations` in every file
- **Pydantic v2** for all data models — use `BaseModel`, `Field`, `model_config`
- **Pydantic Settings** for config — `BaseSettings` with `env_prefix="REDTHREAD_"`
- **Async-first** — all I/O-bound operations must be `async def`
- **Type annotations** — full coverage, `mypy --strict` must pass
- **Logging** — `logger = logging.getLogger(__name__)` per module, no `print()`
- **Emoji prefixes** for log levels: 🔴 start, ✅ success, ❌ failure, ⚠️ partial, 🔬 eval, 💥 jailbreak

## Module Structure

- Never import PyRIT directly outside `pyrit_adapters/`
- Never import `openai` directly outside `pyrit_adapters/` or `evaluation/`
- Algorithm files (`core/*.py`) must be pure Python — no LLM SDK imports
- All models go in `models.py` — keep as single source of truth

## Formatting

- `ruff check src/` — must pass clean (line length 100, Python 3.12 target)
- `mypy --strict src/` — must pass (no `Any` escapes without explicit `# type: ignore`)
- Docstrings required on every class and public method
- No inline comments explaining what the code does — only WHY

## Testing

- All tests in `tests/` with `pytest-asyncio`
- Mock external LLM calls — never make real API calls in tests
- Test file naming: `test_<module_name>.py`

## Reference

Full stack: `docs/TECH_STACK.md`
