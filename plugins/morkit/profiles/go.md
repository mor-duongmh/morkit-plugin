# Go Convention Profile (Tier 2)

> CLAUDE.md (Tier 1) overrides every rule here.

## Naming
- Packages: lowercase, no underscores, short.
- Exported: `PascalCase`. Unexported: `camelCase`.
- Acronyms: keep case (e.g., `URL`, `HTTPClient`, `userID`).
- Errors: variables `ErrFoo`, types `FooError`.

## Idioms
- Return `error` last; check `if err != nil` immediately.
- Wrap with `fmt.Errorf("...: %w", err)`.
- Use `context.Context` as first param of long-running funcs.
- Prefer interfaces accepted, structs returned (consumer-driven).
- Use `defer` for cleanup right after acquiring resource.

## Anti-patterns (findings)
- `_ = err` (silently dropping error) → High.
- `panic` outside `init`/CLI bootstrap → High.
- Goroutine started without lifecycle/cancellation plan → High.
- Channel never closed leading to goroutine leak → High.
- Package-level mutable variables (without sync) → Medium.
- `fmt.Sprintf` into SQL → Critical (Security overlap).
- `exec.Command("sh","-c", input)` → Critical.
- `interface{}` (or `any`) in new APIs without justification → Medium.

## Resource / concurrency
- Open file/conn without `defer Close()` → High.
- `sync.Mutex` copied (passed by value) → High.
- Unbounded goroutine fan-out (no semaphore/worker pool) → Medium.
- `time.Now()` in business logic without injection (testability) → Low.

## Tests
- Use table-driven tests with `t.Run(name, ...)`.
- Use `t.Helper()` in helpers.
- No `time.Sleep` in tests; use `eventually` patterns.
