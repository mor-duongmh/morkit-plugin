# TypeScript / TSX Convention Profile (Tier 2)

> CLAUDE.md (Tier 1) overrides every rule here. If CLAUDE.md is silent on a topic, this profile applies.

## Naming
- Files: `kebab-case.ts` for utilities; `PascalCase.tsx` for React components.
- Variables/functions: `camelCase`.
- Types/interfaces/classes: `PascalCase`.
- Constants (module-level immutable): `SCREAMING_SNAKE_CASE`.
- Booleans: prefix with `is`, `has`, `should`, `can`.

## Idioms
- Prefer `const` over `let`; never `var`.
- Strict null checks: prefer `Foo | undefined` explicit; avoid `any`.
- Use `unknown` for unknown input; narrow before use.
- Prefer named exports; one default export at most per file.
- `async/await` over chained `.then` for new code.
- Replace `enum` with `as const` literal unions when applicable.
- React: hooks at top of component, no conditional hooks.

## Anti-patterns (findings)
- `any` introduced in new code → Medium.
- `// @ts-ignore` without comment justifying → Medium.
- `dangerouslySetInnerHTML` with non-sanitized input → Critical (Security overlap).
- Empty catch `{}` → High.
- Floating promises (no `await`, no `.catch`, no `void`) → High.
- Mutable exported `let` → Medium.
- React: `useEffect` without dependency array, or with all-deps disabled → Medium.

## Resource handling
- `fetch` without timeout/abort signal → Low.
- File handles or streams not closed in error path → High.
