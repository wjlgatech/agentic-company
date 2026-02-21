---
name: python-coding-standards
description: Python coding standards and best practices. Use when implementing Python code covering async/await patterns, type hints, error handling, and idiomatic Python conventions.
license: Apache-2.0
metadata:
  author: agenticom
  version: "1.0"
---

# Python Coding Standards

## When to Use
Use when writing any Python code, especially async Python (asyncio, FastAPI, SQLAlchemy async).

## Do Not Use When
Writing non-Python code.

## Step-by-Step

1. **Type hints on all public functions**:
   ```python
   async def get_user(user_id: str) -> User | None:
   ```
   - Use `X | None` not `Optional[X]` (Python 3.10+)
   - Use `list[str]` not `List[str]` (Python 3.9+)

2. **Async patterns**:
   - Prefer `async def` for I/O bound functions
   - Never use `time.sleep()` in async code — use `await asyncio.sleep()`
   - Avoid blocking calls inside async functions (use `asyncio.run_in_executor` for CPU-bound)
   - Use `asyncio.gather()` for concurrent independent tasks

3. **Error handling**:
   - Catch specific exceptions, not bare `except:`
   - Include context in error messages: `raise ValueError(f"Invalid user_id={user_id!r}")`
   - Use `finally` for resource cleanup, or prefer context managers

4. **Dataclasses over dicts for structured data**:
   ```python
   @dataclass
   class UserConfig:
       name: str
       role: str
       max_retries: int = 3
   ```

5. **Pathlib over os.path**:
   ```python
   path = Path(__file__).parent / "config.yaml"  # not os.path.join(...)
   ```

6. **f-strings over .format() or %**:
   ```python
   msg = f"User {user.name!r} created at {ts:%Y-%m-%d}"
   ```

7. **No mutable default arguments**:
   - Bad:  `def f(items=[]):`
   - Good: `def f(items: list | None = None): items = items or []`

## Style
- Black formatter, line length 88
- Ruff linter (rules E, F, W, I, N, UP, B, C4)
- No TODO comments in submitted code — complete the implementation
