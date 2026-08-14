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
