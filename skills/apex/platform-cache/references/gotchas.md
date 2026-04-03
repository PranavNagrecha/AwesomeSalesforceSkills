# Gotchas — Platform Cache

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Cache Misses Must Always Be Safe

**What happens:** The code assumes a value will be present and fails when the cache is empty or evicted.

**When it occurs:** Platform Cache is treated like a source of truth.

**How to avoid:** Always implement a fallback load path.

---

## Shared Org Cache Is The Wrong Place For User-Specific Secrets

**What happens:** User-specific or sensitive data gets placed in a shared cache scope.

**When it occurs:** Teams optimize for convenience without reviewing cache scope.

**How to avoid:** Reserve org cache for shared non-sensitive reference data and keep secrets elsewhere.

---

## Session Cache Depends On Session Context

**What happens:** A design assumes session-scoped state will behave like durable background state.

**When it occurs:** Teams blur interactive session patterns with async processing patterns.

**How to avoid:** Use session cache only when session context is actually part of the use case.

---

## Fixed Keys Can Trap Stale Data

**What happens:** A cached object remains logically outdated because nothing changes the key or invalidates the entry.

**When it occurs:** Cache invalidation is postponed indefinitely.

**How to avoid:** Use versioned keys or explicit invalidation tied to the source data lifecycle.
