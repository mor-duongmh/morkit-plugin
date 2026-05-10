# PHP Convention Profile (Tier 2)

> CLAUDE.md (Tier 1) overrides every rule here.

## Naming (PSR-12)
- Classes: `PascalCase`.
- Methods/properties: `camelCase`.
- Constants: `SCREAMING_SNAKE_CASE`.
- Files (classes): `PascalCase.php` matching class name (PSR-4).

## Idioms
- Use strict types: `declare(strict_types=1);` at top of file.
- Type-hint parameters and returns; use union types (`int|string`) when justified.
- Prefer constructor property promotion (PHP 8+).
- Use enums (PHP 8.1+) over class constants.

## Anti-patterns (findings)
- `unserialize` on user input → Critical.
- `eval(...)` → Critical.
- SQL via string concatenation → Critical.
- `extract($_GET)` / `extract($_POST)` → Critical.
- `@` error suppression → Medium.
- Mixed return types without `mixed` declaration → Medium.

## Resource
- File handles via `fopen` not closed → High.
- `curl_init` without `curl_close` → Medium.
