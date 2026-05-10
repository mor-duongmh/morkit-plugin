# Java Convention Profile (Tier 2)

> CLAUDE.md (Tier 1) overrides every rule here.

## Naming
- Packages: lowercase, dot-separated.
- Classes/Interfaces: `PascalCase`.
- Methods/fields: `camelCase`.
- Constants: `SCREAMING_SNAKE_CASE`.

## Idioms
- Use `Optional<T>` for "may-be-absent" return types; never for fields/parameters.
- Prefer immutability: `final` fields, defensive copies.
- Use try-with-resources for `AutoCloseable`.
- Prefer streams for collection transforms — but avoid side-effects inside.

## Anti-patterns (findings)
- `catch (Exception e) {}` → High.
- `Runtime.exec(String)` with user input → Critical.
- `XMLDecoder` / `ObjectInputStream` on user input → Critical.
- Public mutable fields → Medium.
- `Date` / `Calendar` in new code (use `java.time`) → Low.
- `null` returned where `Optional` would fit → Medium.
- Static singletons holding mutable state → Medium.

## Resource / concurrency
- Stream/connection without try-with-resources → High.
- `synchronized` on `String` literal / boxed primitive → High.
- `ExecutorService` not shut down → Medium.
