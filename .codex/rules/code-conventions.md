---
alwaysApply: true
---

# Code Conventions Rule

Apply these conventions on every RedThread edit.

## Architecture

- Keep files under 200 lines whenever practical; split before adding complexity.
- Keep orchestration in `src/redthread/orchestration/`.
- Keep algorithmic logic in `src/redthread/core/`.
- Keep evaluation logic in `src/redthread/evaluation/`.
- Keep adapters in `src/redthread/pyrit_adapters/`.
- Keep shared models in `src/redthread/models.py` or local `models/` modules.

## Python

- Use Python 3.12+ style with `from __future__ import annotations`.
- Use full type annotations and keep `mypy --strict` compatibility.
- Prefer async functions for I/O-bound work.
- Use module-level loggers instead of `print()`.
- Add docstrings for public classes and functions.

## Boundaries

- Do not import PyRIT directly outside `src/redthread/pyrit_adapters/` unless an existing pattern already requires it.
- Do not mix orchestration and deep algorithm logic in the same file.
- Extract shared helpers instead of duplicating logic.
- Prefer composition and registries over long `if/elif` chains.

## Verification

- Prefer the smallest meaningful check first.
- Keep tests under `tests/`.
- Mock external LLM calls in automated tests.
