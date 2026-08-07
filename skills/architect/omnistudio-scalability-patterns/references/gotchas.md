# Gotchas — OmniStudio Scalability Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Async Fire-and-Forget Removes UI Blocking But Does NOT Escape Governor Limits

**What happens:** An Integration Procedure configured with `useFuture: true` (fire-and-forget) continues to fail with governor limit errors — most commonly `Too many SOQL queries: 101` — even after the async mode is enabled. The errors now occur silently in the background, surfacing as blank IP results or missing data rather than a visible OmniScript error message.

**When it occurs:** Any time practitioners treat fire-and-forget as a general-purpose "run this in the background" fix for governor limit problems. Future Apex has the same SOQL (100), DML (150), and DML rows (10,000) limits as synchronous Apex. Only CPU (60,000ms) and heap (12MB) are higher. If the IP was hitting SOQL limits synchronously, it will continue hitting them asynchronously.

**How to avoid:** Distinguish the actual constraint before choosing an async mode:
- UI blocking only: use fire-and-forget
- Governor limits (SOQL, CPU, heap): use Queueable Chainable
Audit IP SOQL consumption in debug logs before applying async modes.

---

## Gotcha 2: The Concurrent-Long-Running-Apex Limit Is Org-Wide, Synchronous-Only, and Licence-Scaled

**What happens:** During peak portal hours, OmniScript submissions start failing with capacity errors that do not look like ordinary governor limit errors. Investigation shows the org exceeded its concurrent long-running Apex ceiling — every *synchronous* Apex entry point in the org shares that pool: portal Integration Procedures, internal Lightning/Visualforce actions, synchronous API requests from a middleware, and any managed-package Apex running at the same moment.

**When it occurs:** Three details are routinely got wrong, and each one wrecks the sizing arithmetic:

1. **The threshold is 5 seconds, not 20.** Salesforce counts "synchronous concurrent transactions for long-running transactions that last longer than 5 seconds for each org." An IP that averages 8 seconds is already consuming a slot on every invocation.
2. **The ceiling is not a flat 25.** It is "calculated as a ratio of 100 licenses to one concurrent long-running Apex transaction. Minimum limit is 10, Maximum limit is 50." A 500-licence org has 10 slots (the floor); a 3,000-licence org has 30; anything above 5,000 licences is capped at 50.
3. **Asynchronous Apex does not consume slots.** Batch, Queueable, `@future`, and Scheduled Apex are governed by separate async limits, not this one. Blaming a nightly batch job for portal capacity errors is the classic mis-attribution.

**How to avoid:**
- Compute the org's real ceiling from its licence count before sizing anything
- Design IPs to complete well under **5 seconds** in the common case; route genuinely long operations to Queueable Chainable, which removes them from this pool entirely
- Subscribe to the `ConcurLongRunApexErrEvent` platform event — `CurrentValue` and `LimitValue` report the actual breach and the actual ceiling, which is the only reliable way to learn your org's number
- Still schedule heavy batch jobs outside peak portal hours, but for the correct reason: batch work contends for database and CPU resources and for row locks, which pushes *synchronous* transactions past the 5-second bar. The batch job does not occupy a slot itself; it makes other transactions long-running.

---

## Gotcha 3: Direct Platform Access Does Not Cover Write Operations

**What happens:** An Integration Procedure that reads member data via Direct Platform Access (DPA) and then updates a Case record continues to consume Apex CPU toward the governor limit. Practitioners believe DPA has removed all CPU overhead, but CPU time still accumulates for the write steps.

**When it occurs:** Direct Platform Access in Spring '25+ bypasses Apex CPU governors specifically for read operations: SOQL queries, DataRaptor Extracts in read mode, and Salesforce Object operations in GET mode. Insert, update, delete, and upsert operations still run through the Apex runtime and accumulate CPU time as normal. A mixed read/write IP only partially benefits from DPA.

**How to avoid:**
- Separate read-heavy and write-heavy steps into distinct Integration Procedures where possible
- Enable DPA on the read-only IP; keep the write IP on standard execution mode
- Do not assume DPA eliminates all CPU overhead for an IP that contains any DML

---

## Gotcha 4: LWR + CDN Is a Prerequisite for Portal Scalability, Not an Optimization

**What happens:** A high-volume Experience Cloud portal deployed on an Aura runtime experiences severe page load degradation at 300+ concurrent users despite IP-level caching and Queueable Chainable being correctly configured. The bottleneck is server-side page rendering, not governor limits.

**When it occurs:** Aura-based Experience Cloud sites render page structure on the Salesforce application server for every request. At high concurrency, this creates sustained application server load that IP caching does not address — because the page shell itself, not just data, is re-rendered per session. LWR enables CDN delivery of static page structure, dramatically reducing per-request server load. Without LWR, CDN cannot cache Experience Cloud pages.

**How to avoid:**
- Confirm the Experience Cloud site is on LWR runtime before deploying a high-volume portal
- Enable CDN caching in the site's Administration settings
- Measure time-to-first-byte under load before and after CDN enablement to confirm the CDN is serving cached content
- Aura-to-LWR migration requires planning and testing; do not treat it as a quick fix mid-project

---

## Gotcha 5: IP-Level Caching Serves Identical Responses Regardless of User Context

**What happens:** IP-level caching is enabled for an Integration Procedure that appears to be reference data but actually includes user-specific elements (e.g., personalised pricing, account-specific product availability). Users start receiving other users' cached data — a serious data privacy incident.

**When it occurs:** OmniStudio IP-level caching caches the output keyed on input parameters. If the IP input does not include a user-specific key (like account ID or contact ID), all users with the same generic inputs receive the same cached response. For an IP that queries public product catalog data this is correct behavior; for an IP that queries account-specific pricing, it is a data leakage risk.

**How to avoid:**
- Only enable IP-level caching for IPs that return genuinely user-agnostic data (product catalogs, configuration tables, geography lookups)
- For user-specific data, use DataRaptor Extract caching with user context keys or do not cache
- Review the cache key inputs carefully: if the same response should not be returned to two different users, caching at the IP level is not appropriate
