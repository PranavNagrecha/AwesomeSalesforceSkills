# Examples — Composable Commerce Architecture

## Example 1: An API budget worked out before the BFF is written

**Context:** An Enterprise Edition org, 120 full Salesforce licences, a headless storefront whose shoppers hold
Customer Community licences. The team is sizing the BFF's call pattern against the core org.

**Problem:** The budget is assumed to grow with the shopper base. It does not. The org's daily allocation is
"100,000 + (number of licenses x calls per license type) + purchased API Call Add-Ons", and Customer Community
contributes **0** calls per licence — as does Customer Community Login. Shopper growth adds load and adds no
allocation. Teams discover this during a campaign, when the only remaining lever is an emergency add-on purchase.

**Solution:** Compute the ceiling explicitly, then derive the per-request budget the BFF must hit.

```text
Daily API allocation — Enterprise Edition worked example
────────────────────────────────────────────────────────
  base                                        100,000
  120 × Salesforce licence @ 1,000            120,000
  850,000 × Customer Community @ 0                  0   ← shoppers add nothing
  purchased API Call Add-Ons                        0
                                              ────────
  ceiling                                     220,000 calls / 24h

Peak-day storefront sessions (planned)         60,000
Uncached BFF→org calls per session                  4   ← naive design
                                              ────────
Peak-day demand                               240,000   ← over ceiling before
                                                          any internal or
                                                          integration traffic

Budget available to the storefront:
  220,000 − 40,000 (integrations, internal apps, reserve)  = 180,000
  180,000 / 60,000 sessions = 3.0 calls per session ceiling
Design target: ≤ 1 uncached org call per session; everything else cached
              at the BFF or served from the Commerce APIs.
```

**Why it works:** The calculation converts a vague "cache aggressively" instruction into a number the BFF's design can
be tested against — one uncached org call per session, not four. It also surfaces the two decisions that belong in the
business case rather than in an incident: how much allocation is reserved for non-storefront traffic, and whether add-on
capacity is purchased in advance. One caution on validating this: Full Sandbox is allocated 5,000,000 calls per 24
hours, so a load test that passes there says nothing about the production ceiling.

---

## Example 2: A route policy that keeps every org call under the 20-second boundary

**Context:** The BFF serves product listing, product detail, cart, and an authenticated order-history page. Order
history is the only route that must read the core org on every request.

**Problem:** Order history starts as a single wide query — orders, line items, shipment status, entitlements — and
crosses 20 seconds under load. At that point it stops being a slow page and becomes a shared-resource problem: requests
of 20 seconds or longer contend for **25** concurrent slots in a production org, and exceeding that returns
`REQUEST_LIMIT_EXCEEDED` to *every* caller, including the nightly ERP integration. Below 20 seconds, "There isn't a
limit on the number of concurrent requests".

**Solution:** Make the boundary an explicit per-route policy, enforced by client timeouts rather than by hope.

```yaml
# bff/config/route-policy.yaml — reviewed with the same rigour as the data model
defaults:
  org_client_timeout_ms: 8000        # ABORT well before the 20s pool boundary
  org_retry:
    attempts: 1                      # retrying into an exhausted pool extends the outage
    backoff_ms: 250
  on_org_unavailable: degrade        # render without the org-sourced block

routes:
  - path: /p/:sku                    # product detail
    org_calls: none                  # Commerce APIs + CDN only
    cache: { edge_ttl_s: 300, swr_s: 3600 }

  - path: /c/:category               # product listing
    org_calls: none
    cache: { edge_ttl_s: 600, swr_s: 3600 }

  - path: /cart
    org_calls: none                  # cart state is not core-org state
    cache: { edge_ttl_s: 0 }

  - path: /account/orders            # the one route that reads the org
    org_calls:
      - name: order-summary
        shape: paged                 # 20 rows, summary fields only
        expected_p99_ms: 900
        budget_note: >-
          Must stay under 20s at p100, not p99. A request that crosses 20s
          occupies one of 25 concurrent slots shared with every other
          integration in the org.
      - name: order-detail
        when: on-demand              # fired by expanding one order, never on page load
        shape: single-record
    composite: false
    composite_note: >-
      Not bundled. "For calls to Composite Resources in REST API, this timeout
      applies to the entire composite request, not to each subrequest" — pairing
      a slow subrequest with fast ones fails all of them together.
    cache: { edge_ttl_s: 0, private: true }
```

**Why it works:** Each route states whether it touches the org at all, and the two that do are shaped to stay far from
the boundary — paged summary reads on page load, detail fetched only when a shopper asks for it. The 8-second client
timeout is the enforcement mechanism: a call that would have become a contended slot is abandoned instead, and
`on_org_unavailable: degrade` means the page still renders. Capping retries at one is deliberate; retry storms are how
a slow minute becomes an org-wide incident.

---

## Anti-Pattern: Trusting the client for identity in a BFF endpoint

**What practitioners do:** The BFF authenticates to the org with its own service credentials and passes the shopper's
identity through from the frontend.

```js
// bff/routes/orders.js — the canonical composable-commerce IDOR
app.get('/api/orders/:orderId', async (req, res) => {
  const shopperId = req.headers['x-shopper-id'];        // client-supplied. anything.
  const order = await sf.query(
    `SELECT Id, OrderNumber, TotalAmount, Account.Name
     FROM Order WHERE Id = '${req.params.orderId}'`     // no ownership predicate
  );
  res.json(order);                                       // every field, every order
});
```

**What goes wrong:** Two failures at once. The header is attacker-controlled, so identity is asserted rather than
proven. And the query has no ownership predicate, so any valid order id returns a full order — the platform's record
access is not in play, because the org sees the BFF's service identity, not the shopper's. The shipped storefront
enforced this for you; a composable one does not, and nothing in the stack fails until someone iterates ids.

**Correct approach:** Derive identity server-side from a verified token, scope every query by it, and keep the
platform's own enforcement as a second layer.

```js
app.get('/api/orders/:orderId', requireVerifiedShopperToken, async (req, res) => {
  const shopperId = req.shopper.id;                      // from the VERIFIED token, not a header

  // Parameters are bound by the client library, never interpolated into the SOQL string.
  const order = await sf.query(
    `SELECT Id, OrderNumber, TotalAmount, Status
     FROM Order
     WHERE Id = :orderId AND Shopper_External_Id__c = :shopperId`,
    { orderId: req.params.orderId, shopperId }
  );

  if (!order) return res.status(404).end();              // 404, not 403 — do not confirm existence
  res.json(project(order));                              // explicit field projection
});
```

Three things changed and all three matter: identity comes from a verified token, the ownership predicate is in the
query rather than in a comment, and the field list handed to the client is an explicit projection.

The fourth layer is the integration user itself. An API query runs as the authenticated user, so that user's object
and field permissions are the last line of defence — which means the BFF's integration user should be permissioned to
the minimum the storefront needs, not cloned from an admin. (`WITH USER_MODE` and `as user` are Apex-side idioms and
belong in an Apex REST endpoint, not in a SOQL string sent over the Query API; if the storefront needs behaviour the
Query API cannot express safely, an Apex REST service that states its access mode is the right place to put it.)

---

## Example 3: Reference architecture decision record for a B2C composable storefront

**Context:** A retailer on B2C Commerce wants a Next.js storefront for browse pages, keeps SFRA checkout for one season, and reads order history from a Service Cloud org for logged-in shoppers.

**The decision record** lives at `docs/adr/0051-composable-browse-sfra-checkout.md` in the storefront repository. B2C Commerce cartridges and the Next.js app deploy through B2C code versions and the hosting platform, not through the Metadata API, so no `package.xml` applies to the storefront. The one core-org artifact (the order-history integration user's permission set) follows the org's normal release manifest.

```markdown
# ADR-0051: Next.js browse, SFRA checkout for FY27 H1, BFF as SLAS private client

## Status
Accepted (2026-10-03), Digital Architecture Board

## Context
- B2C Commerce production instance; one staging instance.
- SLAS limits are per instance: 24,000 RPM production, 500 RPM staging.
  Peak forecast: 9,000 logins + refreshes per minute on campaign day.
- Browse SCAPI families are protected by load shedding (HTTP 503,
  sfdc_load_status WARN at 80%, THROTTLE at 90%). Shopper Baskets and
  Shopper Orders are not shed.
- Order history reads a Service Cloud Enterprise Edition org with 150
  Salesforce licences. Shoppers hold Customer Community licences, which
  add 0 calls to the org's 24-hour allocation:
  100,000 + 150 x 1,000 = 250,000 calls per 24 hours, shared with ERP.
- Session bridging between a custom frontend and SFRA is "possible but
  not formally supported" (Plugin SLAS guide); Hybrid Auth (25.3+)
  targets PWA Kit v3.

## Decision
1. Browse pages: Next.js on the hosting CDN; product and listing routes
   edge-cached; on WARN serve stale.
2. BFF: Node service registered as a SLAS private client with Strict
   Client Auth. No client secret reaches the browser.
3. Checkout: SFRA for FY27 H1. We own the session-bridging code and test
   basket merge on login in every release.
4. Order history: one paged org call per page view, 8-second client
   timeout, summary fields only. Detail on demand.
5. Gaps (loyalty balance): SCAPI Custom API with page caching, not BFF
   code, so the CDN can cache it.

## Consequences
### Positive
- Browse pages scale on the CDN; checkout keeps SFRA's maturity.
### Negative
- Session bridging is unsupported territory we maintain ourselves.
- Order history budget: at 40,000 logged-in order views per day we use
  16% of the org allocation; a second org-backed page needs a new ADR.
- Staging cannot exercise SLAS at production volume.

## Alternatives Considered
### PWA Kit v3 with Hybrid Auth for browse
Viable and formally supported; rejected because the design system is
already built in Next.js. Revisit if bridging defects exceed two per
quarter.
### Full composable including checkout now
Rejected: PCI scope and payment re-certification in the same season.

## Review Trigger
Re-evaluate when SFRA checkout is retired or bridging defects exceed
two per quarter. Owner: Commerce Architect.

## Date
2026-10-03
```

**The SLAS smoke test the BFF team runs before every release** (`bff/scripts/slas-guest-token.sh`). It requests a guest token as a private client and honours `Retry-After` on 429, the behavior the rate-limit section requires of client code.

```bash
#!/usr/bin/env bash
# bff/scripts/slas-guest-token.sh: guest token via a SLAS private client.
# Env: SHORT_CODE, ORG_ID, CLIENT_ID, CLIENT_SECRET, CHANNEL_ID
set -euo pipefail
url="https://${SHORT_CODE}.api.commercecloud.salesforce.com/shopper/auth/v1/organizations/${ORG_ID}/oauth2/token"
auth=$(printf '%s:%s' "$CLIENT_ID" "$CLIENT_SECRET" | base64 | tr -d '\n')
for attempt in 1 2 3; do
  hdrs=$(mktemp); body=$(mktemp)
  code=$(curl -sS -o "$body" -D "$hdrs" -w '%{http_code}' -X POST "$url" \
    -H "Authorization: Basic ${auth}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "grant_type=client_credentials" \
    --data-urlencode "channel_id=${CHANNEL_ID}")
  if [ "$code" = "200" ]; then echo "OK: guest token issued"; exit 0; fi
  if [ "$code" = "429" ]; then
    wait=$(awk 'tolower($1)=="retry-after:" {print $2}' "$hdrs" | tr -d '\r')
    echo "429: waiting ${wait:-60}s as instructed by Retry-After"; sleep "${wait:-60}"; continue
  fi
  echo "ERROR: HTTP ${code}"; cat "$body"; exit 1
done
echo "ERROR: still rate limited after 3 attempts"; exit 1
```

Grounding: the token endpoint, the `Basic` header of base64 `clientID:clientSecret`, `grant_type=client_credentials`, and the recommended `channel_id` come from the Private SLAS Client Use Cases page; the base URI form comes from Load Shedding and Rate Limiting. UNVERIFIED (2026-10-03): the `/shopper/auth/v1/organizations/{organizationId}/oauth2/token` path is inferred from the documented `/oauth2/login` path on the SLAS Best Practices page and the "/token endpoint of the SLAS API" wording; confirm against the SLAS API reference before use.

**Why it works:** every number in the record is one the platform enforces, each negative is checkable, and the unsupported part of the design is written down with an owner and an exit condition.

