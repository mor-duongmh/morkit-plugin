---
updated: <YYYY-MM-DD>
status: draft
---

# Code Search Guide

> Quick `rg` recipes per task. For file locations and concern→file mapping see [../../00-overview/SOURCE-MAP.md](../../00-overview/SOURCE-MAP.md). These recipes supplement SOURCE-MAP keywords — they do not replace it.

---

<!-- hint: one ## section per task type; each section has exactly one runnable rg command -->
<!-- hint: replace <paths> with actual repo paths during project setup -->

## Find Entry Points For `<Feature A>`

```bash
rg -n "<keyword|class|route-prefix>" <path/to/controllers> <path/to/src>
```

## Find `<Feature A>` Data Flow

```bash
rg -n "<QueryClass|ServiceMethod|repoMethod>" <path/to/services> <path/to/repositories>
```

## Find `<Feature B>` Configuration / Constants

```bash
rg -n "<ConstantClass|CONFIG_KEY|enum-value>" <path/to/config> <path/to/constants>
```

## Find Auth / Permission Checks

```bash
rg -n "<AuthMiddleware|PermissionGuard|isAllowed|canAccess>" <path/to/src>
```

## Find Schema / Migration For `<Table>`

```bash
rg -n "<table_name|CREATE TABLE|AddColumn>" <path/to/migrations> <path/to/schema>
```

## Find All Routes

```bash
rg -n "<route-decorator|app\.get|router\.(get|post|put|delete)>" <path/to/routes>
```

## Find Tests For `<Class or Feature>`

```bash
rg -n "<ClassName|feature-keyword>" <path/to/tests>
```
