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

## Gotcha 2: The 25-Concurrent-Long-Running-Apex Limit Is Org-Wide, Not Portal-Specific

**What happens:** During peak portal hours, OmniScript submissions start failing with capacity errors that do not appear to be governor limit errors. Investigation reveals that a nightly batch job scheduled to run at the same time as portal peak is consuming a large share of the org's concurrent Apex capacity.

**When it occurs:** The 25-concurrent-long-running-Apex limit (for requests lasting more than 20 seconds) applies to all Apex execution in the org simultaneously: Integration Procedures, triggers, batch jobs, Queueable chains, scheduled classes. High-concurrency portal deployments share this ceiling with all other Apex running at the same time. A batch data migration or scheduled rollup that runs during business hours will silently consume portal capacity.

**How to avoid:** 
- Schedule heavy batch jobs outside peak portal hours
- Monitor the concurrent request count in Setup > Apex Jobs
- Design IPs to complete well under 20 seconds in the common case (use Queueable Chainable only for genuinely long operations, not as a default)
- Consider the org-wide Apex capacity when sizing portal concurrency expectations

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
