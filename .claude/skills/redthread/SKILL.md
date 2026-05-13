```markdown
# redthread Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `redthread` Python codebase. You'll learn about file naming, import/export styles, commit practices, and how to write and run tests. This guide ensures consistency and best practices when contributing to or maintaining the repository.

## Coding Conventions

### File Naming
- Use **camelCase** for filenames.
  - Example: `myModule.py`, `dataProcessor.py`

### Import Style
- Use **relative imports** within the project.
  - Example:
    ```python
    from .utils import helperFunction
    ```

### Export Style
- Use **named exports** (explicitly listing symbols in `__all__`).
  - Example:
    ```python
    __all__ = ['MyClass', 'my_function']
    ```

### Commit Patterns
- Use the `feat` prefix for new features.
- Commit messages are concise (average 55 characters).
  - Example: `feat: add support for user authentication`

## Workflows

### Add a New Feature
**Trigger:** When implementing a new feature or module  
**Command:** `/add-feature`

1. Create a new file using camelCase naming (e.g., `newFeature.py`).
2. Implement your feature using relative imports for dependencies.
3. Export main functions/classes using named exports (`__all__`).
4. Write corresponding tests in a file matching `*.test.*` pattern.
5. Commit your changes with a message starting with `feat:`.
6. Push your branch and open a pull request.

### Refactor Existing Code
**Trigger:** When improving or restructuring existing code  
**Command:** `/refactor`

1. Identify the module to refactor.
2. Update code, maintaining camelCase filenames and relative imports.
3. Adjust exports as needed in `__all__`.
4. Update or add tests to reflect changes.
5. Commit with a clear message (e.g., `feat: refactor dataProcessor for clarity`).
6. Push changes and open a pull request.

## Testing Patterns

- Test files follow the `*.test.*` naming convention (e.g., `utils.test.py`).
- The testing framework is not specified; follow existing test file patterns.
- Place tests alongside the modules they test or in a dedicated test directory.
- Example test file:
  ```python
  # utils.test.py
  from .utils import helperFunction

  def test_helperFunction():
      assert helperFunction(2) == 4
  ```

## Commands
| Command        | Purpose                                  |
|----------------|------------------------------------------|
| /add-feature   | Start the workflow for adding a feature  |
| /refactor      | Begin refactoring an existing module     |
```