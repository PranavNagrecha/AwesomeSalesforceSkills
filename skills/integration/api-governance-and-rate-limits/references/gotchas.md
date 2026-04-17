# Gotchas — API Governance and Rate Limits

## Gotcha 1: Auto-refresh LWC

**What happens:** Open dashboard burns 1000 calls/hour per user.

**When it occurs:** Refresh every 60s.

**How to avoid:** Lengthen or use Pub/Sub for push updates.


---

## Gotcha 2: Retry storms on 429

**What happens:** Doubles consumption.

**When it occurs:** No backoff.

**How to avoid:** Exponential backoff + jitter.


---

## Gotcha 3: Anonymous allocation

**What happens:** Can't tell who is burning it.

**When it occurs:** Shared integration user.

**How to avoid:** One connected app per consumer; track via ApiTotalUsage.

