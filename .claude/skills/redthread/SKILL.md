```markdown
# redthread Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and workflows used in the `redthread` Python codebase. You'll learn the project's coding conventions, how to add new research modules or phases, manage research dependencies, and follow the repository's commit and testing standards. This guide is designed to help contributors maintain consistency and quality across the codebase.

## Coding Conventions

### File Naming
- Use **snake_case** for all Python files.
  - Example: `gepa_phase.py`, `test_gepa_adapter.py`

### Import Style
- Use **relative imports** within modules.
  - Example:
    ```python
    from .models import GEPAResult
    from . import gepa_adapter
    ```

### Export Style
- Use **named exports** (explicitly define what is exported from each module).
  - Example:
    ```python
    __all__ = ["GEPAResult", "run_gepa_phase"]
    ```

### Commit Messages
- Follow **conventional commit** style.
  - Prefixes: `feat`, `docs`
  - Example: `feat: add GEPA phase 0 module and tests`

## Workflows

### Add New Research Module
**Trigger:** When adding a new research phase, module, or major algorithmic component (e.g., GEPA phase, Pareto selection, adapter) to the research pipeline.  
**Command:** `/new-research-module`

1. **Create or modify Python modules** under `src/redthread/research/`.
   - Example: `src/redthread/research/gepa_phase.py`
2. **Update or add test files** under `tests/`.
   - Example: `tests/test_gepa_phase0.py`
3. **Update supporting files** as needed to integrate the new module.
   - Example: `src/redthread/research/models.py`, `workspace.py`
4. **Ensure code quality and correctness:**
   - Run `ruff` for linting.
   - Run `mypy` for type checking.
   - Run all relevant tests and ensure they pass.

**Example:**
```python
# src/redthread/research/gepa_phase.py
from .models import GEPAResult

def run_gepa_phase(data):
    # Implementation here
    pass

__all__ = ["run_gepa_phase"]
```

```python
# tests/test_gepa_phase0.py
from src.redthread.research.gepa_phase import run_gepa_phase

def test_gepa_phase_basic():
    result = run_gepa_phase(sample_data)
    assert result is not None
```

---

### Add or Update Research Dependency
**Trigger:** When introducing or updating a research-related dependency (e.g., gepa, litellm), especially for new research phases or scripts.  
**Command:** `/add-research-dependency`

1. **Edit `pyproject.toml`** to add or update the dependency under an `[optional]` group.
   - Example:
     ```toml
     [project.optional-dependencies]
     research-gepa = ["gepa>=1.2.0"]
     ```
2. **Update `uv.lock`** to reflect the new or updated dependency.
3. **Import the dependency lazily or optionally** in the relevant research module.
   - Example:
     ```python
     try:
         import gepa
     except ImportError:
         gepa = None
     ```
4. **Verify that core installs do not require the optional dependency.**
   - Ensure the main package can be installed without the research dependency unless explicitly requested.

---

## Testing Patterns

- **Test files** are named with the pattern `test_*.py` and located in the `tests/` directory.
  - Example: `tests/test_gepa_adapter.py`
- **Testing framework** is not explicitly specified, but tests follow standard Python test conventions.
- **Example test:**
  ```python
  def test_gepa_adapter_runs():
      from src.redthread.research.gepa_adapter import run_adapter
      assert run_adapter(sample_input) == expected_output
  ```

## Commands

| Command                | Purpose                                                        |
|------------------------|----------------------------------------------------------------|
| /new-research-module   | Scaffold and integrate a new research module or phase          |
| /add-research-dependency | Add or update an optional research dependency for research   |
```
