# Examples — B2B vs B2C Commerce Architecture

## Example 1: Manufacturing Client Choosing B2B Commerce on Core for Dealer Portal

**Scenario:** A mid-market industrial equipment manufacturer maintains dealer accounts in Salesforce CRM (Accounts with contract pricing stored as Pricebook Entries). The project team is evaluating whether to build the dealer self-service ordering portal on B2B Commerce on Core or SFCC.

**Problem:** Without structured platform analysis, the team initially proposed SFCC because they had previous B2C consumer storefront experience. This would have required a custom middleware layer to expose CRM contract pricing to the storefront at checkout, a second integration to write orders back to Salesforce Order Management, and a third integration to check dealer credit limits in real time. The SFCC option would have added three external integration surfaces where the business requirement was simply "dealers log in and order against their contract price."

**Solution:**

The architect mapped each runtime requirement to its data source:

| Runtime requirement | Data location | B2B Commerce on Core | SFCC |
|---|---|---|---|
| Contract pricing per dealer account | Salesforce Pricebook Entry | Native (same org) | Requires outbound API call at checkout |
| Dealer credit limit check | Custom Account field | Native SOQL in Flow | Requires middleware callout |
| Order history in Service Cloud | OrderSummary object | Created natively | Requires async sync job |
| Account-gated product catalog | CommerceEntitlementPolicy | Native B2B feature | Not a native SFCC concept |

B2B Commerce on Core was selected. BuyerGroup records were aligned to the existing dealer tier structure. Contract pricing used existing Pricebook Entries — no migration. CommerceEntitlementPolicy records gated tier-specific products. Checkout was a standard Flow with no custom Apex for the pricing or entitlement steps.

**Why it works:** The manufacturer's data already lived in Salesforce CRM. B2B Commerce on Core's same-org architecture made that data natively available without integration overhead. The three integration surfaces the SFCC option required were eliminated entirely.

---

## Example 2: Fashion Retailer Choosing SFCC for Consumer Storefront

**Scenario:** A direct-to-consumer fashion brand expects 2,000+ concurrent anonymous shoppers during seasonal campaigns and requires a headless PWA front end, advanced promotions engine, and third-party personalization platform integration. The Salesforce org holds CRM and loyalty data but the brand has no B2B buyer accounts.

**Problem:** A consulting team initially proposed B2B Commerce on Core (with D2C license) because the brand already had a Salesforce org. Load testing against the platform limits revealed that the Salesforce API concurrent request cap and LWR rendering infrastructure could not sustain 2,000+ concurrent anonymous sessions during peak campaigns without significant over-provisioning costs. Additionally, the promotion engine complexity required far more than standard platform pricing rules, and the front-end team had React/Node.js expertise, not LWC expertise.

**Solution:**

SFCC was selected. The architecture was:

1. SFCC Primary Instance Group sized for peak traffic with CDN (Akamai) in front.
2. SCAPI used as the commerce API layer for the headless PWA front end.
3. Promotion Engine configured in Business Manager; custom cartridge override for loyalty discount application.
4. Salesforce CRM integration via Salesforce Connector for B2C Commerce: order records synced asynchronously to Salesforce for service rep visibility; loyalty points updated via platform event.
5. Personalization platform connected to SFCC via SCAPI and the on-site tracking script.

The Salesforce org was retained for CRM, service, and loyalty — SFCC handled all storefront traffic.

**Why it works:** SFCC's dedicated infrastructure and CDN-backed architecture were built for high-volume anonymous consumer traffic. The headless SCAPI pattern matched the front-end team's React expertise. The integration surface (async order sync, loyalty events) was well-defined and manageable, unlike the real-time CRM dependency the manufacturer in Example 1 required.

---

## Anti-Pattern: Proposing Commerce Extensions for SFCC Checkout Tax Customization

**What practitioners do:** An architect familiar with B2B Commerce on Core reads the Winter '24 Commerce Extensions documentation and proposes implementing a custom tax calculation service as a Commerce Extension (Apex class implementing `sfdc_checkout.CartExtension`) for a project that is actually on Salesforce B2C Commerce (SFCC).

**What goes wrong:** Commerce Extensions are a feature of B2B Commerce and D2C Commerce on Core only. SFCC has no concept of `sfdc_checkout.CartExtension`, no Apex runtime, and no Flow checkout. The SFCC tax integration is implemented as an SFRA cartridge override of the `app.server.request.started` hook or through the `dw.order.TaxMgr` Business Manager tax configuration. The proposed Apex-based Commerce Extension cannot be built, deployed, or executed in any SFCC environment.

**Correct approach:** Confirm the platform before specifying the extensibility mechanism. For SFCC, tax customization uses SFRA cartridge hooks or third-party tax cartridges (e.g., Avalara's SFCC cartridge). For B2B/D2C Commerce on Core, use Commerce Extensions. These are not interchangeable.
