# C# Convention Profile (Tier 2)

> CLAUDE.md (Tier 1) overrides every rule here.

## Naming
- Types/methods/properties: `PascalCase`.
- Local vars/parameters: `camelCase`.
- Private fields: `_camelCase`.
- Interfaces: `IPascalCase`.
- Constants: `PascalCase` (Microsoft style) unless project uses SCREAMING_SNAKE.

## Idioms
- Use `async`/`await`; suffix async methods with `Async`.
- Use `using`/`using var` for `IDisposable`.
- Records for immutable data; classes for behavior.
- Prefer `IEnumerable<T>` parameters; concrete returns OK.

## Anti-patterns (findings)
- `async void` (except event handlers) → High.
- Blocking on async (`.Result`, `.Wait()`) → High.
- `catch (Exception) {}` empty → High.
- LINQ in hot path with multiple enumerations → Medium.
- Dynamic SQL via `string.Format`/interpolation → Critical.
- `HttpClient` instantiated per call instead of injected → Medium.

## Resource / concurrency
- `IDisposable` not in `using` → High.
- `lock` on `this` or `typeof(...)` → High.
