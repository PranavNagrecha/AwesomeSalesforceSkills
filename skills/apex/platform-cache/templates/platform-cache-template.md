# Platform Cache Decision Worksheet

## Cached Value

| Item | Value |
|---|---|
| Data being cached | |
| Source of truth | |
| Shared or user-scoped? | |
| Safe if evicted? | Yes / No |
| Invalidation approach | |

## Scope Decision

| Option | Use? | Why |
|---|---|---|
| Org cache | | |
| Session cache | | |
| Transaction-local memory only | | |
| Do not cache | | |

## Guardrails

- [ ] Cache miss path is defined
- [ ] Key names are namespaced
- [ ] Sensitive data is excluded
- [ ] Invalidation/versioning is documented
