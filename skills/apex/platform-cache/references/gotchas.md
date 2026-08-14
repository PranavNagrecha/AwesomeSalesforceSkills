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

## TTL Is Bounded At Both Ends, And The Ceiling Differs By Scope

**What happens:** A design asks for a lifetime the scope cannot deliver — "keep it for a day or two" is impossible in session cache — or picks a sub-five-minute TTL that the platform will not accept.

**When it occurs:** TTL is chosen from business intuition instead of the documented per-scope range. Platform Cache Limits states it as: org cache minimum developer-assigned TTL 300 seconds (5 minutes), maximum 172,800 seconds (48 hours), default 86,400 seconds (24 hours) when `ttlSecs` is omitted; session cache minimum 300 seconds (5 minutes), maximum 28,800 seconds (8 hours).

**How to avoid:** Choose the scope from the ceiling as well as the sharing model — anything that must stay warm beyond 8 hours cannot be session-scoped at all. Pass `ttlSecs` explicitly rather than inheriting the 24-hour org default.

---

## OmniStudio Metadata Caching Needs The VlocityMetadata Partition

**What happens:** Data Mapper metadata caching never engages, and the OmniStudio runtime keeps re-reading that metadata even though "Platform Cache is enabled."

**When it occurs:** The org runs Platform Cache rather than Scale Cache. Data Mapper metadata is cached automatically under Scale Cache unless Scale Cache is turned off; the OmniStudio caching doc is explicit that "If you use the Platform Cache, you must allocate space in the VlocityMetadata cache partition to enable this automatic caching."

**How to avoid:** Allocate capacity to the `VlocityMetadata` partition in Setup > Platform Cache before relying on OmniStudio metadata caching, and count that allocation when budgeting Platform Cache capacity across partitions.

---

## Fixed Keys Can Trap Stale Data

**What happens:** A cached object remains logically outdated because nothing changes the key or invalidates the entry.

**When it occurs:** Cache invalidation is postponed indefinitely.

**How to avoid:** Use versioned keys or explicit invalidation tied to the source data lifecycle.
