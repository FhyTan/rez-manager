---
description: 'Python coding conventions and guidelines'
applyTo: '**/*.py'
---

# Python Coding Conventions

## Python Instructions

## Core Principles

- Prioritize readability, clarity, and maintainability over clever or overly compact code.
- Write concise, idiomatic Python that is easy to change and easy to review.
- Keep functions and classes focused on a single responsibility.
- Prefer explicit behavior and clear data flow over hidden side effects.

## Type Hints and Modern Python

- Use descriptive names and provide type hints for public functions, methods, and important internal helpers.
- Prefer Python 3.10+ type syntax such as `int | str`, `list[str]`, and `dict[str, int]` instead of older `Union` and `List` forms unless compatibility requires otherwise.
- Prefer Python 3.10+ language features when they improve clarity, including `match` / `case` for structured branching.
- Use `from __future__ import annotations` when it improves forward references or keeps annotations simple.

## Paths and Filesystem

- Prefer `pathlib.Path` for representing and composing filesystem paths.
- Avoid using raw `str` values for paths when a `Path` object is appropriate.
- Prefer `Path` methods such as `/`, `joinpath()`, `read_text()`, `write_text()`, `open()`, and `resolve()` instead of `os.path` helpers when working with paths.
- Be explicit about text encodings, typically `encoding="utf-8"`, when reading or writing text files.

## Documentation and Comments

- Provide PEP 257 style docstrings for public modules, classes, and functions.
- Do not add docstrings or comments that only restate obvious code.
- Add comments only when they explain intent, constraints, non-obvious behavior, or important tradeoffs.
- For complex algorithms or business rules, briefly explain the approach and why it is structured that way.

## Exceptions and Error Handling

- Always catch specific exceptions such as `ValueError`, `FileNotFoundError`, or `OSError` rather than using a bare `except:`.
- Avoid `except Exception:` unless there is a clear boundary where broad handling is intentional; document the reason when doing so.
- Raise informative exceptions and preserve original context when appropriate.
- Handle edge cases explicitly, including empty input, invalid values, and missing files or directories.

## Code Structure

- Break down complex logic into smaller functions with descriptive names.
- Prefer early returns and guard clauses to reduce nesting.
- Avoid mutable default arguments.
- Keep I/O, business logic, and UI glue separated where possible.
- Prefer standard library tools such as `dataclasses`, `enum`, `collections`, and `itertools` when they make code simpler and clearer.

## Style and Formatting

- Follow the Ruff style guide and project formatting rules.
- Place function and class docstrings immediately after the `def` or `class` statement.
- Use blank lines to separate functions, classes, and logical blocks.
- Keep imports organized and remove unused imports.

## Testing Guidance

- Add or update tests for critical paths and behavior changes.
- Cover common edge cases such as empty inputs, invalid data types, and failure paths.
- Prefer focused unit tests with clear names that describe the behavior under test.
- Test observable behavior rather than implementation details when possible.

## Example
```python
def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.
    """
```

```python
from __future__ import annotations

from pathlib import Path

def load_version(path: Path) -> str:
    """
    Load and validate a version string from a text file.

    Parameters:
        path: Path to the version file.

    Returns:
        The normalized version string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
    """
    
    try:
        version = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise

    if not version:
        raise ValueError("Version file is empty")

    return version
```
