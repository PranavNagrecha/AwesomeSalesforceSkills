# Well-Architected Notes — Commerce Order API (SCAPI / OCAPI Headless Storefront)

## Relevant Pillars

### Security

Order submission involves shopper authentication tokens, payment instrument data (tokenized), and personally identifiable information (name, address, email). Key security considerations:

- **SLAS token handling**: Access tokens must never be stored in browser localStorage (XSS risk). Use httpOnly cookies or a backend-for-frontend (BFF) that holds tokens server-side. Public SLAS clients are acceptable for browser PKCE flows, but private clients (with client secrets) must remain server-side only — never in frontend JavaScript bundles.
- **Named Credentials for Apex**: All Apex callouts to SCAPI or SLAS must use Salesforce Named Credentials to store endpoint URLs and credentials. Hardcoding client secrets in Apex source, Custom Metadata accessible to all profiles, or Custom Settings (not protected) violates the principle of least privilege and creates credential-sprawl risk.
- **OCAPI origin whitelist**: If OCAPI is still in use, the allowed-origins configuration in Business Manager must be explicitly restricted to known storefront domains. A wildcard (`*`) origin in OCAPI settings allows any domain to call the Shop API with the configured client ID.
- **Payment data scope**: SCAPI does not expose raw card numbers; payment instruments in the Commerce Cloud basket and order response contain only tokenized references. Do not attempt to log or persist full SCAPI order response bodies to Apex debug logs — they may contain payment token data that should be treated as sensitive.

### Reliability

- **Non-idempotent order submission**: SCAPI `POST /orders` is not idempotent. Network failures during submission create an ambiguous state. Reliable implementations must include a recovery path that checks whether the order was created before allowing retry (see examples.md for the deduplication pattern).
- **SLAS token refresh**: Access tokens expire (default 30 min). Reliable storefronts implement proactive token refresh before expiry rather than reactive refresh on 401. A 401 during checkout is a bad user experience; catching it proactively requires storing the token's `expires_in` value and refreshing at 80% of TTL.
- **Error surface for payment operations**: After a SCAPI order is ingested into OMS, async payment jobs (`ensure-funds-async`, `ensure-refunds-async`) use `ProcessExceptionEvent` as their error surface. If no subscriber exists, payment failures are invisible. This is a reliability risk for any SCAPI-to-OMS integration.

### Performance

- **Basket validation before order submission**: Calling `POST /orders` with an incomplete basket results in a 400 error after the Commerce Cloud platform processes the full basket state. Validate basket completeness client-side (shipping address, shipping method, payment instrument present) before submitting to avoid wasted round trips.
- **SCAPI response payload size**: The order creation response includes the full order object with all line items, shipments, pricing, and applied promotions. For carts with many line items (10+), response bodies can be 30–100KB. Avoid deserializing the full response in synchronous Apex callouts within governor limit constraints; parse only the fields required (`orderNo`, `status`) if the full order detail is not needed at submission time.
- **Platform Cache for Apex tokens**: SLAS tokens obtained for server-side Apex callouts should be stored in Platform Cache (Org partition) rather than re-fetched on every transaction. The token TTL (1800s) supports caching that avoids adding a SLAS token callout to every page load that needs order data.

### Operational Excellence

- **Monitoring SCAPI calls**: B2C Commerce Cloud provides request logging in Business Manager (Administration > Customization > Log Center). SCAPI request logs are separate from OCAPI logs. Ensure log retention is configured for production debugging. For Apex callouts, use Salesforce Event Log Files (API request events) to track callout volume and latency.
- **Migration from OCAPI to SCAPI**: OCAPI is in maintenance mode. Operational plans should include a SCAPI migration timeline. Running both OCAPI and SCAPI in parallel during migration requires an adapter layer in the storefront data layer to normalize response formats (see gotchas.md for key casing differences). Maintain feature parity testing between the two API paths before cutting over.
- **Cartridge hook reliability**: B2C Commerce hooks (`dw.order.afterOrderCreated`) run synchronously in the storefront request context. If the hook script throws an unhandled exception, it can roll back the order creation in some pipeline configurations. Wrap hook HTTP callouts in `try/catch` and log failures to the Commerce Cloud log; do not allow external webhook failures to abort order creation.

---

## Architectural Tradeoffs

**SCAPI with SLAS vs OCAPI with legacy auth**: SCAPI + SLAS provides centralized identity management, consistent token lifecycle, and alignment with Salesforce's strategic direction. OCAPI + legacy auth provides simpler initial setup (no Account Manager configuration) but creates per-site credential management overhead and no path to Salesforce identity federation. For new projects, SCAPI + SLAS is the correct choice despite higher initial configuration cost.

**Headless-only vs OMS-integrated**: A pure SCAPI headless storefront without OMS has simpler architecture but no post-submission order amendment capability. Adding OMS integration enables cancel/return/adjust via Connect API actions and platform event-driven status notifications, but requires OMS license provisioning and the additional `admin/commerce-order-management` layer. Architect teams must decide at project start — retrofitting OMS after go-live is expensive.

**Client-side token handling vs BFF pattern**: A backend-for-frontend that holds SLAS tokens server-side and proxies SCAPI calls is more secure (no token in browser storage) but adds infrastructure complexity. A pure client-side PKCE flow with httpOnly cookies for token storage is a reasonable middle ground for most implementations.

---

## Anti-Patterns

1. **Storing SLAS access tokens in browser localStorage** — localStorage is accessible to any JavaScript running on the page, including injected scripts from third-party marketing tags or compromised dependencies. A stolen SLAS token allows order history access and potentially order submission. Use httpOnly, Secure, SameSite=Strict cookies instead, or use a BFF to keep tokens server-side entirely.

2. **Conflating the SCAPI storefront layer with the OMS Connect API layer** — SCAPI handles order creation from the storefront. OMS handles fulfillment, cancellations, returns, and payment operations after order ingestion. Attempting to perform OMS-level operations (cancel an item, issue a refund) via SCAPI, or attempting to place a storefront order via the OMS Connect API, fails. Keep the layers strictly separated: SCAPI for submission and retrieval, OMS Connect API for post-submission lifecycle management.

3. **Using OCAPI wildcard allowed-origins in production** — Configuring `"allowed_origins": ["*"]` in OCAPI Site Development settings allows any web page to call the Shop API with your site's client ID. This enables cross-site request attacks targeting guest shopper sessions and is a PCI DSS audit finding. Always restrict OCAPI origins to explicit production and staging domain lists.

---

## Official Sources Used

- Salesforce Commerce API (SCAPI) ShopAPI Orders Reference — https://developer.salesforce.com/docs/commerce/salesforce-commerce/guide/ShopperOrders.html
- SLAS (Shopper Login and API Access Service) Developer Guide — https://developer.salesforce.com/docs/commerce/salesforce-commerce/guide/slas.html
- OCAPI Shop API Orders Resource — https://developer.salesforce.com/docs/commerce/b2c-commerce/references/ocapi-shop-api?meta=Orders
- B2C Commerce Hooks Reference — https://developer.salesforce.com/docs/commerce/b2c-commerce/references/b2c-commerce-hooks-reference?meta=Summary
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
