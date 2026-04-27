```markdown
# redthread Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `redthread` Python codebase. You'll learn how to structure files, write imports and exports, follow commit message conventions, and understand the project's testing approach. This guide is ideal for contributors aiming for consistency and clarity in their work.

## Coding Conventions

### File Naming
- Use **snake_case** for all Python files.
  - Example: `my_module.py`, `data_processor.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import helper_function
    ```

### Export Style
- Use **named exports**; explicitly define what is exported from modules.
  - Example:
    ```python
    def important_function():
        pass

    __all__ = ['important_function']
    ```

### Commit Message Style
- Follow **conventional commit** patterns.
- Prefixes: `feat`, `chore`, `docs`
- Average length: ~46 characters
  - Example:
    ```
    feat: add support for new user roles
    chore: update dependencies
    docs: improve README usage section
    ```

## Workflows

### Adding a New Feature
**Trigger:** When implementing a new functionality  
**Command:** `/add-feature`

1. Create a new Python file using snake_case if needed.
2. Use relative imports to access internal modules.
3. Implement the feature with named exports.
4. Write or update corresponding test files (`*.test.*`).
5. Commit your changes using the `feat:` prefix.
    - Example: `feat: implement user authentication`

### Updating Documentation
**Trigger:** When improving or adding documentation  
**Command:** `/update-docs`

1. Edit or create documentation files as needed.
2. Use clear, concise language and code examples.
3. Commit changes with the `docs:` prefix.
    - Example: `docs: add API usage example to README`

### Maintenance or Dependency Updates
**Trigger:** When performing maintenance tasks  
**Command:** `/maintenance`

1. Update dependencies or perform refactoring.
2. Ensure all tests pass after changes.
3. Commit changes with the `chore:` prefix.
    - Example: `chore: bump requests to v2.28.0`

## Testing Patterns

- Test files follow the pattern `*.test.*` (e.g., `module.test.py`).
- Testing framework is **unknown**; check existing test files for structure.
- Place test files alongside or within the relevant module directory.
- Example test file name: `utils.test.py`

## Commands
| Command        | Purpose                                      |
|----------------|----------------------------------------------|
| /add-feature   | Start workflow for adding a new feature      |
| /update-docs   | Start workflow for updating documentation    |
| /maintenance   | Start workflow for maintenance or upgrades   |
```
