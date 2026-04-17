# Gotchas — OmniStudio Asynchronous Data Operations

## Gotcha 1: Sync >120s kill

**What happens:** Whole IP aborts.

**When it occurs:** Single slow callout.

**How to avoid:** Timeout on HTTP calls; queue if needed.


---

## Gotcha 2: Cache stale

**What happens:** Users see old data.

**When it occurs:** Cache-enabled with wrong TTL.

**How to avoid:** TTL appropriate; bust cache on mutation.


---

## Gotcha 3: No error branch

**What happens:** Silent failure to user.

**When it occurs:** Happy-path IP only.

**How to avoid:** Error path with UI message.

