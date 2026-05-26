# Commit Message Standards

## Format
```
type(scope): description
```

## Types (priority order)
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no logic change)
- `refactor`: Restructure without behavior change
- `test`: Tests
- `chore`: Maintenance, deps, config
- `perf`: Performance
- `build`: Build system
- `ci`: CI/CD

## Rules
- **<72 characters**
- **Present tense, imperative** ("add" not "added")
- **No period at end**
- **Scope optional but recommended**
- **Focus on WHAT, not HOW**
- For agent config files (paths under `.claude/` or `plugins/`): prefer `feat`, `fix`, or `perf` over `docs` — these directories contain agent behavior, not documentation.

## NEVER Include AI Attribution
- ❌ "Generated with Claude"
- ❌ "Co-Authored-By: Claude"
- ❌ Any AI reference

## Good Examples
- `feat(auth): add login validation`
- `fix(api): resolve query timeout`
- `docs(readme): update install guide`
- `refactor(utils): simplify date logic`

## Bad Examples
- ❌ `Updated files` (not descriptive)
- ❌ `feat(auth): added login using bcrypt with salt` (too long, describes HOW)
- ❌ `Fix bug` (not specific)

## Special Cases (agent config files)
- `.claude/` or `plugins/` skill updates: `perf(skill): improve token efficiency`
- `.claude/` or `plugins/` new skills: `feat(skill): add database-optimizer`
- `docs(readme): ...` is still valid for top-level README/changelog
