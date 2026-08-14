# Well-Architected Notes — Composable Commerce Architecture

## Relevant Pillars

- **Efficient (primary)** — the org's API allocation is a fixed pool that shopper growth does not enlarge: Customer
  Community and Customer Community Login licences contribute **0** calls per licence to the 24-hour allocation. Every
  uncached BFF-to-org call therefore draws on a budget sized for internal users. On this platform, caching is not a
  performance optimisation for a composable storefront; it is the capacity model.
- **Resilient** — the 20-second concurrency boundary makes a slow storefront query an org-wide fault. Twenty-five
  concurrent long-running requests exhaust the pool for every caller, so the storefront can take down the ERP
  integration. Composable architecture moves failure domains around; it does not remove them.
- **Secure** — the shipped storefront enforces record access on every request. A BFF authenticating with a service
  identity collapses that enforcement into application code, and every authorisation decision the platform used to make
  becomes one the team must make correctly, on every endpoint, forever.
- **Adaptable** — the reason to go composable is frontend ownership. That is a real benefit and it is paid for in
  permanent operational surface: a frontend codebase, a BFF, CDN configuration, an observability stack, and a security
  boundary. The trade is only worth making when the frontend requirement is genuinely unmet by the shipped experience.

## Architectural Tradeoffs

**Composable vs the shipped storefront.** The shipped storefront comes with the platform's access enforcement, its
caching behaviour, and no BFF to run. Composable buys UX control and performance ownership and hands back four
long-lived responsibilities. The honest test is whether a named business requirement is unmet today — not whether the
team would prefer a modern frontend framework, which is a different and much weaker reason.

**Cache aggressiveness vs correctness.** Aggressive edge caching is what keeps the org call budget intact and is
exactly what makes price, inventory, and entitlement data stale. Resolve it per data class rather than per route:
catalogue content tolerates minutes, price tolerates seconds in most businesses and nothing in some, inventory and
entitlements usually tolerate nothing. Write the tolerance down per field; it is a commercial decision, not a technical
default.

**Composite requests vs individual calls.** Composite reduces round trips, which directly relieves the allocation
pressure. It also shares one timeout across every subrequest — "this timeout applies to the entire composite request,
not to each subrequest" — so a slow member fails the fast ones alongside it. Bundle by expected latency, never by
convenience, and keep anything unbounded out entirely.

**Service-account BFF vs per-shopper authentication.** A single service identity is simpler, poolable, and puts the
whole authorisation burden in the BFF. Per-shopper authentication keeps the platform enforcing access and multiplies
token management and session complexity. Whichever is chosen, the identity used in queries must be derived from a
verified token server-side — a client-supplied header is not an identity, it is a parameter.

## Anti-Patterns

1. **Sizing the API budget from shopper count.** Community licences add zero to the allocation, so a storefront's
   traffic is funded by the base 100,000 plus internal licences plus purchased add-ons. Assuming otherwise produces a
   capacity plan that is wrong in the same direction as the growth the business is hoping for.
2. **Load-testing in Full Sandbox and calling it validated.** Full Sandbox is allocated 5,000,000 API calls per 24
   hours. A test that passes there tells you the code works; it tells you nothing about the production ceiling.
3. **Letting a BFF call run long.** A read that crosses 20 seconds moves from an uncounted request to one of 25
   contended slots shared org-wide. Client timeouts below the boundary and a hard retry cap are what keep a slow
   dependency from becoming an incident for every other integration in the org.
4. **Identity from a request header.** `x-shopper-id` taken from the client, with no ownership predicate on the query.
   The org sees the BFF's service identity, so the platform's record access is not in play, and the endpoint returns
   any order to anyone who can guess an id.

## Official Sources Used

- Salesforce Developer Limits and Allocations Quick Reference (last updated 7 August 2026) — *Total API Request
  Allocations*: the "100,000 + (number of licenses x calls per license type) + purchased API Call Add-Ons" formula, the
  per-licence-type contributions (Customer Community 0, Customer Community Login 0, Customer Community Plus 200,
  Partner Community 200, Salesforce 1,000 in Enterprise and 5,000 in Unlimited/Performance), and the 5,000,000 Full
  Sandbox allocation.
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm (verified 2026-08-14)
- Salesforce Developer Limits and Allocations Quick Reference — *Concurrent API Request Limits* and *API Timeout
  Limits*: 25 concurrent long-running requests in production orgs and sandboxes (5 in Developer Edition and Trial
  orgs), `REQUEST_LIMIT_EXCEEDED`, the absence of a limit below 20 seconds, the 10-minute timeout, and the
  composite-request timeout scope.
  https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/salesforce_app_limits_platform_api.htm (verified 2026-08-14)
- Apex Developer Guide, Version 67.0 (Summer '26) — *Using the with sharing, without sharing, and inherited sharing
  Keywords*: the FLS disclaimer behind the "BFF must enforce what the platform used to" argument.
  https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm (verified 2026-08-14)

### Not sourced here

B2C Commerce (SCAPI) quotas, the SLAS authentication model, and Commerce-side caching behaviour are documented in the
B2C Commerce developer documentation, which was not reachable for these notes. Every figure above is a **core org**
limit. Do not read them as SCAPI limits, and verify the Commerce-side quota framework separately before sizing a
storefront against it.
