# Python Convention Profile (Tier 2)

> CLAUDE.md (Tier 1) overrides every rule here.

## Naming (PEP 8)
- Modules: `snake_case`.
- Classes: `PascalCase`.
- Functions/variables: `snake_case`.
- Constants: `SCREAMING_SNAKE_CASE`.
- Private: leading single underscore.

## Idioms
- Prefer f-strings over `%` and `.format`.
- Use context managers (`with`) for files/locks/transactions.
- Type hints on public APIs (Python 3.10+).
- Use `dataclasses` or `pydantic` instead of dict-as-record.
- Iterators/generators for streaming; avoid building giant lists.

## Anti-patterns (findings)
- Mutable default argument (`def f(x=[])`) → High.
- `except:` or `except Exception: pass` → High.
- `eval` / `exec` on dynamic input → Critical (Security overlap).
- `pickle.load` on external data → Critical (Security overlap).
- `yaml.load` without `Loader=SafeLoader` → Critical.
- Bare `assert` for runtime validation (stripped under `-O`) → Medium.
- `subprocess.*` with `shell=True` and string interpolation → Critical.
- Globals mutated from inside functions without `global` declaration → Medium.

## Resource / concurrency
- Open file without `with` → Medium.
- `requests` without `timeout=` → Low.
- `asyncio` blocking call (`time.sleep`, sync I/O) inside coroutine → High.
- Threading shared mutable state without `Lock`/`Queue` → High.

## Tests
- Use `pytest` style; avoid `unittest.TestCase` in new code unless project uses it.
- Test functions named `test_<unit>_<scenario>`.
