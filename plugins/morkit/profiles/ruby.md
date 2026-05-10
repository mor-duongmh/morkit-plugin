# Ruby Convention Profile (Tier 2)

> CLAUDE.md (Tier 1) overrides every rule here.

## Naming
- Classes/modules: `PascalCase`.
- Methods/vars: `snake_case`. Predicate methods end with `?`. Bang methods end with `!`.
- Constants: `SCREAMING_SNAKE_CASE`.

## Idioms
- Use blocks/iterators (`each`, `map`, `select`) over manual loops.
- Prefer `&:method_name` symbol-to-proc.
- Keep methods short; favor early returns.

## Anti-patterns (findings)
- `eval(input)` → Critical.
- `system("sh -c #{input}")` / backticks with input → Critical.
- `Marshal.load` on external data → Critical.
- `rescue` without exception class → High.
- Monkey-patching core classes in app code → Medium.
- Long methods > 30 lines → Medium.

## Rails-specific (if Rails detected)
- N+1 query suspicion (loop over records calling AR) → High.
- Mass assignment without strong params → Critical.
- `html_safe` on user input → Critical.
