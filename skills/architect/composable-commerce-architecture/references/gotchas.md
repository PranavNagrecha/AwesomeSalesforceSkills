# Gotchas — Composable Commerce Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Community licences contribute **zero** to the org's API allocation

**What happens:** A composable storefront's BFF talks to the core org for anything Commerce APIs do not cover —
entitlements, service history, custom pricing logic, order status. That traffic draws on the org's 24-hour API
allocation, and the allocation is computed per licence type. The Developer Limits and Allocations Quick Reference gives
the formula for Enterprise, Unlimited, and Performance Edition orgs as "100,000 + (number of licenses x calls per
license type) + purchased API Call Add-Ons", and then lists the per-licence contributions. Two lines decide the
architecture:

- **Customer Community: 0**
- **Customer Community Login: 0**

Customer Community Plus contributes 200 (Plus Login, 10); Partner Community 200 (Partner Community Login, 10). Full
Salesforce licences contribute 1,000 in Enterprise Edition and 5,000 in Unlimited and Performance.

The consequence is counter-intuitive: adding a million shoppers on Customer Community licences adds nothing to the
API budget. The BFF's entire call volume is funded by the 100,000 base plus the org's internal licences plus purchased
add-ons — a number sized for an internal user population, now serving public storefront traffic.

**When it occurs:** At the first traffic peak, which for commerce means the campaign the whole quarter was planned
around.

**How to avoid:** Compute the daily budget from the formula before designing the BFF's call pattern, not after. Every
uncached BFF-to-org call is a draw on a fixed pool that shopper growth does not enlarge. Cache aggressively at the BFF,
batch reads, and treat API Call Add-Ons as a line item in the business case rather than an emergency purchase. Note
also that Full Sandbox is allocated 5,000,000 calls per 24 hours — a load test that passes in Full Sandbox proves
nothing about production capacity.

---

## Gotcha 2: Twenty seconds is an architectural boundary, not a performance target

**What happens:** "The following table lists the limits for various types of orgs for concurrent inbound requests
(calls) with a duration of 20 seconds or longer": **25** for Production orgs and Sandboxes, **5** for Developer Edition
and Trial orgs. "If the number of long running requests exceeds the limit, the API returns a `REQUEST_LIMIT_EXCEEDED`
exception code. Any new concurrent requests aren't processed until there are fewer requests than the allowed limit."

And the sentence that turns this into a design rule: "There isn't a limit on the number of concurrent requests shorter
than 20 seconds."

**When it occurs:** When a BFF issues a wide catalogue or entitlement query that crosses 20 seconds under load. It
takes 25 concurrent slow callers to exhaust the pool, and a retrying middleware layer reaches 25 quickly. The failure
then presents across every integration in the org — the storefront takes down the nightly ERP sync, and the incident
gets logged as "Salesforce is slow".

**How to avoid:** Design every BFF-to-org read to complete well inside 20 seconds — narrow the field list, page the
results, push aggregation to a pre-computed object — because below that threshold the request is not counted at all.
Set the BFF's client timeout below 20 seconds so a slow call is abandoned rather than promoted into a contended slot,
and cap retries: retrying into an exhausted pool is how a slow minute becomes a slow hour.

---

## Gotcha 3: A composite request shares one timeout budget

**What happens:** "The timeout limit for REST and SOAP API calls is 10 minutes, except for any query call." Exceeding
it returns "a `REQUEST_RUNNING_TOO_LONG` status code (for SOAP API) or a `QUERY_TIMEOUT` exception code (for REST
API)". The trap for a BFF is the next sentence: "For calls to Composite Resources in REST API, this timeout applies to
the entire composite request, not to each subrequest."

**When it occurs:** When the BFF adopts composite requests to reduce round trips — the correct instinct given the
allocation pressure in Gotcha 1 — and bundles a slow subrequest with fast ones. The whole composite fails, including
the subrequests that had already succeeded, and the BFF's error handling usually treats that as a total failure of an
operation that was mostly fine.

**How to avoid:** Group composite subrequests by expected latency rather than by page. Keep anything unbounded out of a
composite entirely, and design the BFF's response shape so a partially-successful aggregate is representable — a
storefront that can render a product page without the personalised block is more available than one that cannot.

---

## Gotcha 4: A composable frontend does not inherit the platform's access model

**What happens:** In the shipped storefront, record access is enforced by the platform on every request. A BFF
authenticating with its own credentials collapses that: the org sees one identity, and every authorisation decision
about which shopper may see which order moves into code the team wrote. In Apex terms this is the well-documented
split — "Sharing declarations don't enforce object-level access or field-level security" — arriving
one layer higher, where nothing enforces either by default.

**When it occurs:** In the first custom endpoint that takes an identifier from the client. `GET /api/orders/:id`
implemented as a lookup by id, with the shopper's identity taken from a request header the client controls, is the
canonical composable-commerce IDOR.

**How to avoid:** Derive the shopper identity from a verified token on the server, never from a client-supplied
parameter, and scope every query by that identity in the BFF — then keep the platform's enforcement as a second layer
rather than replacing it. Where the BFF calls Apex, state the access mode explicitly (`WITH USER_MODE`, `as user`,
`AccessLevel.USER_MODE`) so the platform still has an opinion even though the caller is a service account.

## Official Sources Used

- Salesforce Developer Limits and Allocations Quick Reference (last updated 7 August 2026) — *Total API Request
  Allocations*: the "100,000 + (number of licenses x calls per license type) + purchased API Call Add-Ons" formula, the
  per-licence-type table including Customer Community 0 / Customer Community Login 0 / Customer Community Plus 200 /
  Partner Community 200, the Salesforce licence contributions (1,000 Enterprise, 5,000 Unlimited and Performance), the
  Developer Edition total of 15,000, and the 5,000,000 Full Sandbox allocation.
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm (verified 2026-08-14)
- Salesforce Developer Limits and Allocations Quick Reference — *Concurrent API Request Limits* and *API Timeout
  Limits*: the 25 / 5 concurrency figures for requests of 20 seconds or longer, `REQUEST_LIMIT_EXCEEDED`, "There isn't
  a limit on the number of concurrent requests shorter than 20 seconds", the 10-minute timeout with
  `REQUEST_RUNNING_TOO_LONG` / `QUERY_TIMEOUT`, and the composite-request timeout scope.
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 (Summer '26) — *Using the with sharing, without sharing, and inherited sharing
  Keywords*: "Sharing declarations don't enforce object-level access or field-level security".
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 — *Set an Access Mode for Database Operations*: the user-mode idioms
  (`WITH USER_MODE`, `insert as user`, `AccessLevel.USER_MODE`) cited above.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_enforce_usermode.htm (verified 2026-08-14)

### Not sourced here

B2C Commerce (SCAPI) has its own quota framework, authentication model (SLAS), and caching behaviour, published in the
B2C Commerce developer documentation rather than the core platform docs. Nothing in these notes should be read as a
statement about SCAPI quotas — the figures above are core-org API allocations. Verify SCAPI-side limits against the
Commerce API documentation for your instance before sizing a storefront against them.
