# Python

Modern Python earns its keep when the types are honest, the environment is reproducible, and failures are loud. The rules below assume Python 3.12+. Where a rule depends on the version, the version is called out. This is backend guidance and stays framework-agnostic.

## Type hints and static checking

- Annotate every public function signature: parameters and return type. The annotation is the contract.
- Write `-> None` explicitly for functions that return nothing. Silence is not a return type.
- Use `T | None` for nullable values (3.10+). Reach for `Optional[T]` only in code that still targets older runtimes.
- Avoid `Any`. It disables checking for the value and everything it flows into. Use it only when the type is genuinely open.
- Run a static checker (mypy or pyright) in CI. Hints are analysis only; nothing enforces them at runtime.
- Import heavy or cyclic types under a `TYPE_CHECKING` guard so they cost nothing at runtime.

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mymodule import HeavyClass
```

## Environment and dependencies

- Create a virtual environment for every project. Never install into the system interpreter.
- Declare the project and its direct dependencies in `pyproject.toml`. It is the single source of build and tool config.
- Pin transitive dependencies in a lockfile so installs are reproducible across machines and CI.
- Separate runtime dependencies from dev and test extras. Production should not ship your test runner.

## Project layout

- Use a `src/` layout for libraries. It stops the interpreter from importing straight out of the working tree and hiding packaging bugs.
- Keep `__init__.py` empty or minimal. No side effects, no heavy logic on import.

```
my-project/
├── pyproject.toml
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
└── tests/
    ├── conftest.py
    └── test_core.py
```

## Style, formatting, and linting

- Follow PEP 8: 4-space indent, no tabs, `lowercase_with_underscores` for functions and variables, `CapWords` for classes, `UPPER_CASE` for module constants.
- Name exceptions with an `Error` suffix: `PaymentDeclinedError`.
- Let a formatter own layout. Run ruff (formatter and linter) or black, and enforce it in CI so style never reaches review.
- Use ruff or isort to group and order imports: standard library, third-party, local, each block separated by a blank line. Never `from module import *`.
- Compare to `None`, `True`, and `False` with `is`, never `==`. Check emptiness with `if not seq:`, not `len(seq) == 0`.

## Data structures

- Use a `@dataclass` for plain internal data: it gives you `__init__`, `__repr__`, and equality for free. Add `frozen=True` for immutable records and `slots=True` to cut memory.
- Use pydantic when data crosses a trust boundary and needs validation or parsing (request bodies, config, external payloads). It coerces and rejects at the edge.
- Do not hand-roll classes that only carry fields. That is what dataclasses are for.

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Money:
    amount: int
    currency: str
```

## Error handling

- Raise exceptions to signal failure. Never return `None` or an error code as a sentinel.
- Catch the most specific exception you can. Avoid `except Exception:` as a catch-all, and never write a bare `except:`, which also swallows `KeyboardInterrupt` and `SystemExit`.
- Derive custom exceptions from `Exception`, not `BaseException`.
- Chain with `raise X from Y` to preserve the original cause.
- Keep `try` blocks small: wrap only the statement that can fail. Put the success path in an `else`.
- Never use `assert` for production validation. The `-O` flag strips assertions.

```python
class PaymentDeclinedError(Exception):
    """Raised when the payment gateway rejects the charge."""

try:
    charge = gateway.submit(order)
except GatewayTimeout as exc:
    raise PaymentDeclinedError("gateway timed out") from exc
else:
    record(charge)
```

## Context managers

- Use `with` for anything that needs deterministic cleanup: files, locks, connections, transactions. Cleanup runs on an early return or an exception, unlike a trailing close.
- Open multiple resources in one `with` rather than nesting.
- Write your own context manager with `contextlib.contextmanager` when you own a resource lifecycle.

```python
with open(path) as src, open(dest, "w") as out:
    out.write(transform(src.read()))
```

## Mutable default arguments

- Never use a mutable default (`[]`, `{}`, `set()`). Python evaluates the default once, so it is shared across every call and accumulates state.
- Default to `None` and build the value inside the function.

```python
def append_row(row: str, rows: list[str] | None = None) -> list[str]:
    rows = rows if rows is not None else []
    rows.append(row)
    return rows
```

## Comprehensions

- Use a comprehension for a straight map or filter. It reads as one expression and states intent.
- Fall back to an explicit loop when there is branching, a side effect, or more than one condition. A comprehension that needs a comment has outgrown the form.
- Do not nest comprehensions past one level of `for`. Readability collapses fast.

```python
active_ids = [u.id for u in users if u.is_active]
```

## Logging

- Use the `logging` module for diagnostics. Never `print()`.
- Get a named logger per module: `logger = logging.getLogger(__name__)`.
- Pick the level deliberately: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
- Pass arguments lazily so formatting only happens when the record is emitted: `logger.debug("processing %s records", count)`, not an f-string.
- Call `logger.exception(...)` inside an `except` block to attach the traceback.
- In library code, do not call `logging.basicConfig()`. Configuration belongs to the application.
- Never log secrets, tokens, or PII.

## Testing

- Use pytest. Name files `test_*.py` and functions `test_*`.
- Put shared fixtures in `conftest.py` so they are discovered without explicit imports.
- Drive variations with `@pytest.mark.parametrize` instead of loops inside a test.
- Keep each test independent: no shared mutable state between tests.
- For the coverage contract and the philosophy behind it, follow `core-development/references/testing-philosophy.md`.

## Do / Instead of

| Do | Instead of |
|---|---|
| Raise a specific exception | return `None` as an error sentinel |
| `T \| None` (3.10+) | `Optional[T]` in new code |
| `default=None`, build inside | mutable default argument |
| `with open(...)` | manual `open` / `close` |
| Named logger + lazy args | `print()` for diagnostics |
| `is None` / `is not None` | `== None` |
| `@dataclass` / pydantic | hand-written field-only class |
| Static checker in CI | trusting hints are enforced |
| Lockfile for transitive deps | unpinned `pip install` |
| Comprehension for map/filter | comprehension with branching and comments |
