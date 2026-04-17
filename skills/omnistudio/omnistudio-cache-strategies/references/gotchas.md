# Gotchas — OmniStudio Cache Strategies

## Gotcha 1: Sharing leak

**What happens:** User A sees User B's filtered list.

**When it occurs:** No per-user key.

**How to avoid:** Include user context in cache key or use user-partitioned cache.


---

## Gotcha 2: Stale after bug fix

**What happens:** Patched data still missing.

**When it occurs:** No bust on deploy.

**How to avoid:** Cache version key bumped on deploy.


---

## Gotcha 3: Over-long TTL

**What happens:** Business data stale.

**When it occurs:** Copy-paste config.

**How to avoid:** TTL per use case.

