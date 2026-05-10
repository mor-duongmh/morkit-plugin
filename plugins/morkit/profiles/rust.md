# Rust Convention Profile (Tier 2)

> CLAUDE.md (Tier 1) overrides every rule here.

## Naming
- Modules/files: `snake_case`.
- Types/traits/enums: `PascalCase`.
- Functions/vars: `snake_case`.
- Consts/statics: `SCREAMING_SNAKE_CASE`.

## Idioms
- Return `Result<T, E>`; use `?` for propagation.
- Prefer `&str` parameters over `String` when ownership not needed.
- Use `thiserror` for library errors, `anyhow` for application errors.
- Use `Cow<'_, str>` to avoid allocation when possible.

## Anti-patterns (findings)
- `unwrap()` / `expect("...")` in non-test code → High (unless invariant proved in comment).
- `panic!` outside startup/CLI → High.
- `unsafe` block without `// SAFETY:` comment → High.
- `clone()` on large struct in hot path → Medium.
- `Arc<Mutex<...>>` copy-pasted without justification → Medium.
- `as` numeric cast that may truncate without check → Medium.

## Resource / concurrency
- Blocking call inside `async fn` → High.
- `tokio::spawn` without lifecycle management → Medium.
- Drop order assumptions across threads → Medium.
