# Commerce Order API (SCAPI / OCAPI Headless Storefront) — Work Template

Use this template when working on any task involving B2C Commerce headless order submission, retrieval, or notification via SCAPI or OCAPI.

---

## Scope

**Skill:** `apex/commerce-order-api`

**Request summary:** (fill in what the user asked for)

**API path in use:**
- [ ] SCAPI ShopAPI Orders (new integration — recommended)
- [ ] OCAPI Shop API /orders (legacy — maintenance only)
- [ ] Both (migration in progress)

---

## Context Gathered

Answer these before proceeding:

| Question | Answer |
|---|---|
| B2C Commerce org short code | |
| B2C Commerce organization ID | |
| SLAS client ID (public or private?) | |
| SLAS scopes configured | |
| Shopper type: guest, registered, or both | |
| OMS integration in place? | Yes / No |
| Order amendment required post-submission? | Yes / No — if Yes, requires OMS |
| Notification mechanism | B2C Hook / OMS Platform Event / Polling / None |

---

## SLAS Configuration Checklist

Before writing any SCAPI order code, verify SLAS is correctly configured:

- [ ] SLAS client exists in Account Manager with correct scopes:
  - `sfcc.shopper-baskets-orders` — for order submission and retrieval
  - `sfcc.shopper-myaccount.order` — for registered shopper order history
  - `sfcc.shopper-orders` — for guest order lookup by orderNo + email (if needed)
- [ ] Redirect URIs registered for public SLAS client (PKCE flows)
- [ ] Private SLAS client credentials stored in Salesforce Named Credentials (not Apex source)
- [ ] SLAS token TTL noted: access_token expires_in _______ seconds

---

## Basket Pre-Validation

Before calling `POST /orders`, verify the shopper basket is complete. Mark each item confirmed:

- [ ] At least one product line item in the basket
- [ ] Shipping address set on the basket
- [ ] Shipping method selected
- [ ] Payment instrument added (tokenized; no raw card data)
- [ ] Basket ID captured and stored (needed for retry deduplication)

---

## Order Submission Pattern

**Pattern selected:** (choose one)
- [ ] Guest shopper submission (SLAS guest token + POST /orders)
- [ ] Registered shopper submission (SLAS registered token + POST /orders)
- [ ] Server-side Apex callout (SLAS Trusted Agent + Named Credential)

**Deduplication implemented:**
- [ ] Client stores `basketId` before submission
- [ ] On network timeout: checks `GET /orders/{orderNo}` or correlates by `basketId` before retry
- [ ] UI shows "Checking order status..." state during verification window

---

## Response Handling

Record the key fields extracted from the `POST /orders` response:

| Field | Value / Handling |
|---|---|
| `orderNo` | Stored in: ______ |
| `status` | Expected: `created` |
| `paymentStatus` | |
| `confirmationStatus` | |
| Error on 400 | Basket incomplete — see pre-validation above |
| Error on 401 | SLAS token expired or invalid — refresh token |
| Error on 403 | SLAS scope missing — verify Account Manager client config |
| Error on 404 (basket) | Basket already consumed — order may have succeeded; check before retry |

---

## Order Retrieval Pattern

**Shopper type:**

Guest order lookup (by orderNo + email — no session required):
```
GET /checkout/shopper-orders/v1/organizations/{organizationId}/orders/{orderNo}?guest_email={email}
Authorization: Bearer {guestOrPublicToken}
```

Registered order history (paginated):
```
GET /checkout/shopper-orders/v1/organizations/{organizationId}/orders?offset=0&limit=10
Authorization: Bearer {registeredToken}
```

- [ ] Pagination handled: total ______, page size ______
- [ ] Token type confirmed: registered token for history, not guest token

---

## Notification Wiring

**Selected mechanism:**

B2C Commerce Hook:
- [ ] Hook registered: `dw.order.afterOrderCreated` in hooks.json
- [ ] Hook script wrapped in try/catch — HTTP callout failure does NOT abort order creation
- [ ] Webhook target URL confirmed reachable from Commerce Cloud IP ranges

OMS Platform Events (requires OMS integration):
- [ ] `OrderSummaryCreatedEvent` subscriber deployed
- [ ] `ProcessExceptionEvent` subscriber deployed (for payment job failures)
- [ ] Refer to `admin/commerce-order-management` skill for event subscription details

---

## Security Review

- [ ] SLAS access tokens are NOT stored in browser `localStorage` or `sessionStorage`
- [ ] SLAS access tokens use httpOnly cookies or BFF server-side storage
- [ ] Private SLAS client secrets are in Named Credentials — not in Apex literals
- [ ] If OCAPI is in use: allowed-origins in Business Manager is NOT a wildcard
- [ ] SCAPI responses are not logged to Apex debug logs in full (may contain payment token data)

---

## Post-Submission Amendment Plan

- [ ] If order amendment is required: OMS is integrated (see `admin/commerce-order-management`)
- [ ] If OMS is NOT integrated: Document that amendment requires a custom B2C cartridge approach
- [ ] Confirmed with stakeholders: SCAPI ShopAPI has NO PATCH /orders endpoint

---

## Notes

Record any deviations from the standard pattern, environment-specific configuration, or known edge cases discovered during this task:

(free text)
