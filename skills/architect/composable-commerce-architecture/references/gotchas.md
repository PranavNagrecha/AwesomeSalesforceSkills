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

**Source:** Salesforce Developer Limits and Allocations Quick Reference (Summer '26 PDF, salesforce_app_limits_cheatsheet.pdf), Total API Request Allocations: the allocation formula and per-licence table (Customer Community 0, Customer Community Login 0, Customer Community Plus 200, Partner Community 200), re-checked 2026-10-03.

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

**Source:** Salesforce Developer Limits and Allocations Quick Reference (Summer '26 PDF, salesforce_app_limits_cheatsheet.pdf), Concurrent API Request Limits: 25 long-running requests (20 seconds or longer) for production and sandboxes, 5 for Developer Edition and trial orgs; re-checked 2026-10-03.

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

**Source:** Salesforce Developer Limits and Allocations Quick Reference (Summer '26 PDF, salesforce_app_limits_cheatsheet.pdf), API Timeout Limits: "For calls to Composite Resources in REST API, this timeout applies to the entire composite request, not to each subrequest."

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

**Source:** Apex Developer Guide v67.0, Using the with sharing, without sharing, and inherited sharing Keywords ("Sharing declarations don't enforce object-level access or field-level security") and Set an Access Mode for Database Operations.

---

## Gotcha 5: SLAS rate limits belong to the instance, and staging gets 500 RPM

**What happens:** The B2C side has its own limit model. Shopper Login (SLAS) enforces rate limits per SLAS tenant (instance), not per client and not per shopper: 24,000 requests per minute on a production instance and 500 requests per minute on each non-production instance. Every client on the instance shares that budget. When it is reached, SLAS returns HTTP 429 with a `Retry-After` header. A single refresh token can be exchanged at most 3 times within 60 seconds; more attempts return 429.

**When it occurs:** During a load test against a staging instance, which hits 500 RPM long before the storefront is stressed. In production, when a BFF refreshes the same token from several concurrent requests, or when a login-heavy campaign shares the instance with other SLAS clients.

**How to avoid:** Size login and token traffic per instance, not per app. Load-test SLAS against the production allowance only with Salesforce's agreement, and expect 429 in staging. Serialize refresh per shopper session in the BFF and honour `Retry-After` exactly. Ask the Customer Success Manager about adjustments before a known peak; the documentation says limits can be adjusted per scenario.

**Source:** B2C Commerce Developer Guide, SCAPI > Load Shedding and Rate Limiting (developer.salesforce.com/docs/commerce/commerce-api/guide/throttle-rates.html); SLAS Best Practices, Refresh Token Service Protection (slas-best-practices.html). Both read 2026-10-03.

---

## Gotcha 6: Browse APIs shed load with 503; checkout does not

**What happens:** When an instance reaches its load threshold after scaling to maximum capacity, SCAPI endpoints protected by load shedding return HTTP 503. Responses carry `sfdc_load` (capacity in use, 0 to 100) and `sfdc_load_status`, which reads `WARN` at 80% and `THROTTLE` at 90%. Load shedding is not applied to checkout endpoints such as Shopper Baskets and Shopper Orders.

**When it occurs:** On a flash-sale peak, when product listing and search calls start returning 503 while basket and order calls keep working. A BFF that treats 503 as a hard error blanks the listing page instead of serving cached content.

**How to avoid:** Read `sfdc_load_status` in the BFF and switch catalog routes to stale cache at `WARN`. Treat 503 on browse endpoints as "serve stale", never as "retry immediately". Keep checkout on the documented Shopper Baskets and Shopper Orders families so it inherits the protection.

**Source:** B2C Commerce Developer Guide, SCAPI > Load Shedding and Rate Limiting (throttle-rates.html), read 2026-10-03.

---

## Gotcha 7: A BFF must be a SLAS private client; a browser app must be a public client

**What happens:** A team registers one SLAS client and uses it from both the browser and the BFF. Either the client secret ships in browser JavaScript, or the BFF runs a public-client PKCE flow it does not need. The documentation draws the line explicitly: any app that can store a secret is a private client, and "all shopping apps with a backend-for-frontend (BFF) must be provisioned as private clients", while single-page apps such as PWA Kit and mobile apps without a gateway "must be provisioned as public clients".

**When it occurs:** When the composable design adds a BFF late, after a browser-only prototype, and keeps the prototype's client.

**How to avoid:** Register a private client for the BFF and turn on Strict Client Auth, which requires `/login` and `/authorize` to carry credentials in the `x-slas-client-auth` header. Register a separate public client for any code that runs in the browser. Never put a client secret in a browser bundle.

**Source:** B2C Commerce Developer Guide, Private SLAS Client Use Cases (slas-private-client.html), Public SLAS Client Use Cases (slas-public-client.html), SLAS Best Practices, Strict Client Auth (slas-best-practices.html). Read 2026-10-03.

---

## Gotcha 8: A phased rollout with a custom frontend leaves the supported path

**What happens:** The plan keeps checkout on SFRA and builds browse pages in a custom framework. Session bridging between the two is the hard part, and the documented, supported mechanism targets PWA Kit: "Custom headless web applications are possible but not formally supported." From B2C Commerce version 25.3, Hybrid Auth replaces Plugin SLAS and keeps the SFRA session (`dwsid`) and the SLAS token synchronized, and new Hybrid Auth implementations must start on PWA Kit v3.

**When it occurs:** When the frontend framework is chosen before the phasing plan, and the phasing plan assumes session bridging "just works" for any frontend.

**How to avoid:** Decide the phasing before the framework. If browse and checkout will be split across a custom frontend and SFRA, budget the session-bridging work as owned code, test basket merge on login, and record in the decision record that this path is outside formal support.

**Source:** B2C Commerce Developer Guide, Configure a Hybrid Storefront with Plugin SLAS (phased-headless-rollouts.html) and Configure a Hybrid Storefront with Hybrid Auth (hybrid-auth.html). Read 2026-10-03.

---

## Gotcha 9: A guest order left on the session leaks into the next shopper's account

**What happens:** On a shared device, a guest places an order and the next person registers on the same browser session. Without a session boundary, the guest's order can associate with the new registered profile.

**When it occurs:** When the BFF keeps the guest access and refresh tokens after order confirmation, which is the default behavior of most token caches.

**How to avoid:** Treat order confirmation as a session boundary. After a successful `POST /orders`, request a fresh guest token from SLAS with `grant_type=client_credentials` and replace the stored access and refresh tokens.

**Source:** B2C Commerce Developer Guide, SLAS Best Practices, guest session rotation (slas-best-practices.html), read 2026-10-03.

---

Full source list with URLs: `references/well-architected.md`, section "Official Sources Used".

