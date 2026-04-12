# Gotchas — Commerce Order API (SCAPI / OCAPI Headless Storefront)

Non-obvious Salesforce B2C Commerce platform behaviors that cause real production problems in this domain.

## Gotcha 1: POST /orders Destroys the Basket Atomically — There Is No Rollback

**What happens:** The SCAPI `POST /checkout/shopper-orders/v1/.../orders` endpoint creates the order and deletes the shopper basket in a single atomic operation. If the HTTP response is lost in transit (network timeout, mobile app backgrounded), the client does not know whether the order was created. The basket is gone either way.

**When it occurs:** Any unreliable network path between the storefront and the SCAPI gateway — mobile apps on cellular, users closing the browser tab mid-submission, flaky network proxies, or aggressive client-side timeouts shorter than SCAPI's processing window (which can be 5–15 seconds for complex orders with promotions).

**How to avoid:** Never auto-retry `POST /orders` without first checking whether the order exists. Implement a backend-for-frontend (BFF) that correlates basket ID to order number: after a timeout, query `GET /orders` (registered shoppers) or look up by the stored orderNo+email pair (guest shoppers) to confirm success before showing an error. Show the shopper a "Checking your order status..." screen during this window. Client-side, store the `basketId` before submitting — if the POST returns 404 (basket not found), that is evidence the first call likely succeeded.

---

## Gotcha 2: SLAS Token Scope Errors Return 403, Not a Scope-Specific Error

**What happens:** If a SLAS public client is missing a required scope (e.g., `sfcc.shopper-baskets-orders`), the Commerce API returns an HTTP 403 Forbidden. The response body contains a type URI referencing `invalid-scope` or `insufficient-scope`, but the token itself appears valid — it was issued by SLAS without error. This causes developers to debug the API call itself (headers, endpoint URL, basket state) rather than the SLAS client configuration.

**When it occurs:** After initially configuring a SLAS client in Account Manager for authentication but forgetting to add the `sfcc.shopper-baskets-orders` scope for order operations. Also occurs when a SLAS client is cloned for a new environment and the scope list is not fully copied.

**How to avoid:** After any SLAS client configuration change, decode the issued access token (it is a JWT) and inspect the `scp` claim to verify scopes are present before testing API calls. The SLAS token will be issued regardless of whether the requested scopes are granted — the token's `scp` claim is authoritative. Required scopes for the full order flow: `sfcc.shopper-baskets-orders` (submit + retrieve), `sfcc.shopper-myaccount.order` (registered history), `sfcc.shopper-orders` (guest lookup by orderNo + email).

---

## Gotcha 3: Direct DML on OrderItemSummary in MANAGED Mode Corrupts Financial Aggregates (OMS Layer Boundary)

**What happens:** Teams that integrate B2C Commerce SCAPI with Salesforce OMS sometimes attempt to correct order quantities or prices by running direct Apex DML against `OrderItemSummary` records after the order is ingested into OMS. In MANAGED `OrderLifeCycleType`, this either throws a `DmlException` or succeeds silently — but in the silent success case, the OrderSummary's aggregate financial fields (`TotalAdjustedProductAmount`, `TotalCharged`, `GrandTotalAmount`) do not recalculate. The stored totals become inconsistent with the line items and cannot be corrected without Salesforce Support involvement.

**When it occurs:** When developers conflate the B2C Commerce SCAPI order model (which is the storefront-facing submission layer) with the OMS layer (which is the fulfillment and financial management layer). After a SCAPI order is ingested into OMS as an `OrderSummary`, all mutations must go through OMS Connect API actions (`submit-cancel`, `submit-return`, `adjust-item-submit`), not direct DML.

**How to avoid:** Treat the SCAPI Orders API and the OMS Connect API as two separate, non-overlapping layers. SCAPI handles storefront-to-order-creation. OMS handles everything after. Never write Apex that modifies `OrderItemSummary`, `FulfillmentOrderLineItem`, or `ChangeOrder` records directly in code that also touches SCAPI responses. If OMS is involved, all post-submission order changes go through `admin/commerce-order-management` Connect API actions.

---

## Gotcha 4: OCAPI and SCAPI Response Keys Use Different Casing — snake_case vs camelCase

**What happens:** OCAPI Shop API responses use `snake_case` key names (`customer_info`, `billing_address`, `order_total`, `shipping_items`). SCAPI responses use `camelCase` (`customerInfo`, `billingAddress`, `orderTotal`, `shippingItems`). JavaScript and Apex code that destructures these responses with hardcoded key names will silently get `undefined` or `null` when the API version switches, because `order.billing_address` evaluates to `undefined` when the actual key is `billingAddress`.

**When it occurs:** During OCAPI-to-SCAPI migrations where the response-parsing code is not updated alongside the endpoint change. Also occurs when a team runs OCAPI in one environment and SCAPI in another without an adapter layer.

**How to avoid:** Build an order response adapter/normalizer in the storefront's data layer that maps either API's response to a canonical internal model. Never directly use OCAPI or SCAPI raw keys in UI components or Apex deserialization classes — always pass through a mapping layer. When migrating from OCAPI to SCAPI, run both in parallel with response comparison tests before cutting over.

---

## Gotcha 5: SCAPI Has No Order Amendment Endpoint — Teams Discover This After Go-Live

**What happens:** The SCAPI ShopAPI Orders resource supports `POST /orders` (create) and `GET /orders` / `GET /orders/{orderNo}` (retrieve). There is no `PATCH /orders/{orderNo}` or equivalent amendment endpoint in SCAPI ShopAPI. Teams that build a headless storefront assuming they can amend orders (change address, add/remove items) via the same SCAPI layer discover this limitation when a customer calls support wanting to change a delivery address. The only amendment paths are: OMS Connect API actions (if OMS is integrated), or a custom B2C Commerce cartridge using the `dw.order.Order` business object directly in the storefront cartridge layer.

**When it occurs:** When solution architects spec the storefront order API without reading the full ShopAPI Orders reference or conflate SCAPI with OCAPI (OCAPI does expose PATCH for certain amendment operations). Discovery usually happens during UAT or early production.

**How to avoid:** Explicitly document in the design phase that SCAPI has no amendment endpoint. If order amendment is a business requirement, plan OMS integration from the start — `admin/commerce-order-management` covers the Connect API actions. If OMS is out of scope, document that amendment requires a custom cartridge approach using the Commerce Cloud business object layer, which is server-side JavaScript in the cartridge, not SCAPI.

---

## Gotcha 6: SLAS Guest Tokens Cannot Access Registered Shopper Order History — The Error Is 403, Not 401

**What happens:** A storefront that reuses the guest SLAS token (stored in a cookie or local state after checkout) to render the My Account order history page receives a 403 Forbidden from `GET /orders`. The response type is `insufficient-scope`. Developers often interpret 403 as a misconfigured SLAS client and invest time in Account Manager debugging, when the real issue is simply that the wrong token type is being used.

**When it occurs:** When the storefront token management does not correctly differentiate between guest (anonymous) and registered (authenticated) SLAS tokens. Common in implementations where checkout and My Account are built by different teams or at different times.

**How to avoid:** Gate all `GET /orders` (history) calls behind a check that the current token is a registered token (the JWT's `sub` claim is a real customer ID, not an anonymous guest GUID). The frontend should track token type in its auth state. If the shopper is not logged in, prompt login before showing order history — do not call `GET /orders` with a guest token at all.
