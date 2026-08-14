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

---

## Gotcha 4: Scale Cache Makes Cached Data Mappers Executable Regardless of Permission

**What happens:** After metadata is Scale-cached, a Data Mapper can run for a user who fails Required Permission on a live (uncached) run. Cache refreshes on successful executions. `CheckCachedMetadataRecordSecurity` covers **IPs**, not Data Mappers. Remediation for DMs is often `TurnOffScaleCache=true` (perf cost).

**When it occurs:** Guest portals; "Required Permission on every component" as the only control. Nested parent IP + cached child DM.

**How to avoid:** Turn off Scale Cache for guest-reachable / PII Data Mappers. Enable cached-metadata security on IPs. Do not treat Required Permission as holding after the first warm cache. See `omnistudio-security` §6.

