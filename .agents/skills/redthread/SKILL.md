```markdown
# redthread Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns used in the `redthread` Python repository. You'll learn the project's coding conventions, file organization, import/export styles, and how to write and organize tests. This guide is ideal for contributors aiming for consistency and maintainability in the codebase.

## Coding Conventions

### File Naming
- Use **snake_case** for all file names.
  - Example: `my_module.py`, `data_processor.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import helper_function
    from ..models import DataModel
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ['MyClass', 'my_function']
    ```

### Commit Patterns
- Commit messages are freeform, with no strict prefixing.
- Average commit message length is about 32 characters.
  - Example:  
    ```
    Fix bug in data processing logic
    ```

## Workflows

### Adding a New Module
**Trigger:** When you need to add new functionality to the codebase  
**Command:** `/add-module`

1. Create a new Python file using snake_case naming.
2. Implement your functionality.
3. Use relative imports to access other modules.
4. Define `__all__` for named exports if necessary.
5. Write corresponding tests in a `*.test.*` file.

#### Example:
```python
# In my_feature.py
def new_feature():
    pass

__all__ = ['new_feature']
```

### Writing and Running Tests
**Trigger:** When you add new code or want to verify existing code  
**Command:** `/run-tests`

1. Create a test file matching the pattern `*.test.*` (e.g., `my_module.test.py`).
2. Write test functions for your code.
3. Use the project's preferred (unknown) testing framework.
4. Run the tests using the appropriate command for the framework.

#### Example:
```python
# In my_module.test.py
def test_new_feature():
    assert new_feature() is not None
```

## Testing Patterns

- Test files follow the pattern `*.test.*` (e.g., `module.test.py`).
- The specific testing framework is not detected; check existing tests or ask maintainers.
- Place test files alongside or near the modules they test.

## Commands
| Command       | Purpose                                 |
|---------------|-----------------------------------------|
| /add-module   | Scaffold and add a new module           |
| /run-tests    | Run all tests in the repository         |
```
