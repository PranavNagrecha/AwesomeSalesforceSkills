---
name: products-and-pricebooks
description: "Use when configuring the Salesforce product catalog and pricing structure: creating Product2 records, setting up Standard and custom Pricebooks, managing PricebookEntry junction records, enabling multi-currency pricing, configuring Product Schedules (Revenue and Quantity), or troubleshooting incorrect prices on Opportunity line items and Quotes. Triggers: 'add product to pricebook', 'pricebook entry', 'standard pricebook', 'product catalog', 'multi-currency product pricing', 'product schedule', 'revenue schedule', 'quantity schedule', 'deactivate product'. NOT for CPQ (Salesforce Revenue Cloud / SBQQ) product configuration, CPQ pricing rules, or CPQ bundle setup. NOT for Quote template layout or PDF generation."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
triggers:
  - "how do I add a product to a pricebook in Salesforce"
  - "why are prices wrong on opportunity line items"
  - "can I delete the Standard Pricebook"
  - "how do I set up multi-currency pricing for products"
  - "how do product schedules work and how do I enable them"
  - "I deactivated a product but existing opportunities still show it"
  - "can I delete a custom pricebook that is referenced by open opportunities"
tags:
  - products
  - pricebooks
  - pricebook-entry
  - product-catalog
  - multi-currency
  - product-schedules
  - opportunity-products
  - sales-cloud
inputs:
  - "Salesforce org edition (Products and Pricebooks available in all editions except Essentials without add-on)"
  - "Whether multi-currency is enabled in the org"
  - "List of products, pricing tiers, and currencies needed"
  - "Whether Product Schedules (Revenue or Quantity) are required"
  - "Existing Pricebook structure and any open Opportunities or Quotes referencing current Pricebooks"
outputs:
  - "Product catalog configuration guidance (Product2, Pricebook2, PricebookEntry)"
  - "Standard Pricebook and custom Pricebook setup instructions"
  - "Multi-currency PricebookEntry setup plan"
  - "Product Schedule configuration guidance"
  - "Product deactivation safe-handling procedure"
  - "Data model explanation and constraint summary"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Products and Pricebooks

Use this skill when configuring or troubleshooting Salesforce's native product catalog and pricing structure. The core data model involves three objects — `Product2`, `Pricebook2`, and `PricebookEntry` — working together as a junction pattern. Misunderstanding the role of each object is the single most common source of incorrect pricing on Opportunity line items and Quote line items.

This skill does NOT cover CPQ (Salesforce Revenue Cloud / SBQQ) pricing rules, CPQ bundles, or CPQ price actions. Route those requests to the `architect/cpq-vs-standard-products-decision` skill.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Multi-currency status**: Check Setup > Company Information > Currencies. If multiple currencies are active, each product needs one PricebookEntry per currency per Pricebook. Forgetting this leaves products unselectable in multi-currency orgs.
- **Edition and license**: Products and Pricebooks are available in Group, Professional, Enterprise, Performance, Unlimited, and Developer editions. Confirm the org supports the features before designing around them.
- **Existing Pricebook references**: Check whether any open Opportunities or Quotes reference the Pricebooks you intend to modify or deactivate. A custom Pricebook cannot be deleted while any Opportunity or Quote references it in an active state.
- **Product Schedule requirements**: Revenue Schedules and Quantity Schedules must be explicitly enabled in Setup > Products > Product Schedules Settings before they appear on product records. Confirm this before designing a schedule-based revenue recognition workflow.

---

## Core Concepts

### The Product2 / Pricebook2 / PricebookEntry Data Model

The Salesforce product catalog is a three-object model:

- **Product2** — Defines what you are selling. Contains the product name, product code, description, family, `IsActive` flag, and any custom fields. A Product2 record has no price on its own.
- **Pricebook2** — Defines a pricing context (e.g., "Standard", "Partner Discount", "Enterprise"). Contains the pricebook name and `IsActive` flag. Each org has exactly one Standard Pricebook (created automatically) and can have unlimited custom Pricebooks.
- **PricebookEntry** — The junction object that pairs one Product2 with one Pricebook2 and assigns a `UnitPrice`. When a rep adds a product to an Opportunity or Quote, they are selecting a PricebookEntry — not the Product2 directly.

The dependency chain is:

1. Create the Product2 record and activate it (`IsActive = true`).
2. Create a PricebookEntry in the **Standard Pricebook** for that product. This is required even if you never use the Standard Pricebook for selling; the platform requires a Standard Pricebook entry to exist before any custom Pricebook entry can be created for the same product.
3. Create PricebookEntry records in each custom Pricebook you want to expose the product through.

Skipping step 2 and going straight to a custom Pricebook entry is a hard platform error — the API will reject it.

### Standard Pricebook Constraints

Every Salesforce org has exactly one Standard Pricebook. Its properties:

- It cannot be deleted — only deactivated (`IsActive = false`).
- It is the anchor Pricebook. All products must have a Standard Pricebook entry before they can appear in any custom Pricebook.
- When the Standard Pricebook is deactivated, new Opportunities and Quotes cannot select it, but existing line items using it are preserved.
- The Standard Pricebook is identified programmatically using `Test.getStandardPricebookId()` in Apex tests. Hardcoding its ID in test code is a common and problematic anti-pattern — the ID varies between orgs and sandboxes.

### Custom Pricebooks

Custom Pricebooks can be created without limit. Each custom Pricebook:

- Can have a different `UnitPrice` per product per currency than the Standard Pricebook.
- Cannot be deleted while any Opportunity or Quote references it and that Opportunity or Quote has an open status.
- Can be deactivated at any time — deactivation hides it from new Opportunity and Quote record creation but does not invalidate existing line items referencing it.
- Is selected at the Opportunity level via `Opportunity.Pricebook2Id`. All products added to that opportunity must come from the same Pricebook. Mixing entries from different Pricebooks on a single opportunity is not supported.

### Multi-Currency Pricing

When multi-currency is enabled, each PricebookEntry is scoped to a specific currency. For a product to be available in multiple currencies:

- One PricebookEntry must exist per currency per Pricebook per product.
- The `CurrencyIsoCode` field on PricebookEntry determines which currency that entry's `UnitPrice` is expressed in.
- Automatic currency conversion using static exchange rates does not create new PricebookEntries — it applies an exchange rate at reporting time. If a PricebookEntry in EUR does not exist, a rep with an EUR Opportunity cannot add that product.

Example: a product sold in USD and EUR requires four PricebookEntry records — one in Standard/USD, one in Standard/EUR, one in CustomPricebook/USD, and one in CustomPricebook/EUR.

### Product Schedules

Product Schedules split how revenue or quantity is recognized across time after an opportunity is closed. There are two types:

- **Revenue Schedules**: Model installment payment plans. The total price is divided across payment dates. Each Revenue Schedule record represents one installment.
- **Quantity Schedules**: Model phased delivery. The total quantity is divided across delivery dates. Each Quantity Schedule record represents one delivery batch.

Schedules must be enabled at two levels:
1. **Org level**: Setup > Products > Product Schedules Settings — check "Enable Revenue Schedules" and/or "Enable Quantity Schedules."
2. **Product level**: On each Product2 record, set the Schedule Type to Revenue, Quantity, or Both and define the default schedule (number of installments, frequency).

Product Schedules affect how Collaborative Forecasting rolls up revenue if the forecast type is set to use Product Schedules as the forecast object. Confirm the forecasting setup before enabling schedules in a production org.

### Product Deactivation

Setting `Product2.IsActive = false` hides a product from the selection picker when adding products to new Opportunities or Quotes. It does NOT:

- Remove the product from existing Opportunity line items.
- Delete PricebookEntry records for that product.
- Affect any existing Opportunity, Quote, or Order that already uses that product.

This is intentional — deactivation is safe for catalog cleanup and does not break historical data. Always prefer deactivation over deletion for products that have ever appeared on a closed or historical Opportunity.

---

## Common Patterns

### Pattern: Multi-Tiered Pricing with Standard and Custom Pricebooks

**When to use:** Different customer segments (e.g., direct customers vs. reseller partners) receive different list prices for the same products.

**How it works:**
1. Create all Product2 records and activate them.
2. Add Standard Pricebook entries for every product (required platform step).
3. Create a custom "Direct" Pricebook and a custom "Partner" Pricebook.
4. Add PricebookEntry records to each custom Pricebook with the appropriate `UnitPrice` per product.
5. On each Opportunity, set `Pricebook2Id` to the appropriate Pricebook for that customer segment. All products added to the opportunity must come from that same Pricebook.

### Pattern: Multi-Currency Product Catalog

**When to use:** The org sells in more than one currency and reps need to price deals in the customer's local currency.

**How it works:**
1. Confirm multi-currency is enabled and all required currencies are active in Setup > Manage Currencies.
2. For each product, create a PricebookEntry in the Standard Pricebook for each active currency.
3. For each custom Pricebook, create PricebookEntries for each product-currency combination as well.
4. Use Data Loader or a script to bulk-create PricebookEntry records if the catalog is large — doing this manually is error-prone at scale.
5. Test by creating an Opportunity in each currency and confirming all required products are selectable.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need different prices for different customer segments | Create custom Pricebooks per segment | One Pricebook per Opportunity; custom Pricebooks keep segment pricing isolated |
| Product no longer for sale | Deactivate Product2 (IsActive = false) | Deactivation hides from picker; deletion risks breaking historical data |
| Need to retire a custom Pricebook | Deactivate Pricebook2; cannot delete if referenced by open Opportunities | Deactivation prevents new selection; existing line items are preserved |
| Selling in multiple currencies | Create one PricebookEntry per product per currency per Pricebook | Multi-currency requires explicit entries — exchange rate conversion does not create entries |
| Revenue installments or phased delivery | Enable Product Schedules at org and product level | Schedules model time-phased revenue/quantity; must be enabled before use |
| Rep cannot see a product in an Opportunity | Check PricebookEntry exists for that product/Pricebook/currency combo | Missing junction record is the most common cause |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm org readiness** — Verify the org edition supports Products, check whether multi-currency is enabled, and confirm Product Schedules Settings match the business requirements (Revenue, Quantity, or both). Document these inputs before designing the catalog.
2. **Create and activate Product2 records** — Use Setup > Products or Data Loader for bulk creation. Set `IsActive = true`, populate product code and family fields. Do not skip the product family field if reports or filters will use it.
3. **Create Standard Pricebook entries for all products** — Every product must have a PricebookEntry in the Standard Pricebook before it can appear in any custom Pricebook. For multi-currency orgs, create one Standard Pricebook entry per active currency per product.
4. **Create custom Pricebooks and their PricebookEntries** — For each pricing tier or customer segment, create a Pricebook2 record and add PricebookEntry records linking each product with its segment-specific `UnitPrice`. For multi-currency orgs, repeat per currency.
5. **Configure Product Schedules if required** — Enable at the org level in Setup > Products > Product Schedules Settings, then configure each product's schedule type (Revenue, Quantity, or Both), default number of installments, and frequency. Verify with the forecasting team how schedules interact with Collaborative Forecasting rollups.
6. **Test end-to-end** — Create test Opportunities in each currency and segment. Confirm correct products appear, correct prices populate, and schedules generate as expected. Test with a non-admin user to confirm Profile and FLS settings allow product and pricebook selection.
7. **Run the checker script and review output** — Run `python3 skills/admin/products-and-pricebooks/scripts/check_products_and_pricebooks.py --manifest-dir path/to/metadata` and address all flagged issues before deploying.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All Product2 records have `IsActive = true` and a populated product code
- [ ] Every product has a PricebookEntry in the Standard Pricebook before any custom Pricebook entry was created
- [ ] For multi-currency orgs: one PricebookEntry per product per currency per Pricebook
- [ ] Custom Pricebooks created and named clearly to match their business purpose
- [ ] Pricebook2Id set correctly on test Opportunities; products from one Pricebook are not mixed with another
- [ ] Product Schedules enabled at org level if required; each product's schedule type is set
- [ ] Deactivated products confirmed absent from the product picker; existing line items confirmed intact
- [ ] No custom Pricebook deleted while referenced by open Opportunities or Quotes
- [ ] Standard Pricebook not deleted (platform prevents this but confirm no workaround was attempted)
- [ ] FLS and Profile settings allow sales reps to read Pricebook2 and create/read PricebookEntry

---

## Related Skills

- `architect/cpq-vs-standard-products-decision` — Use when the business is evaluating CPQ vs standard Products/Pricebooks, or when pricing complexity (bundles, rules, approvals) exceeds standard capabilities.
- `admin/quotes-and-quote-templates` — Use when quote line items are not showing correct prices from the Pricebook or when the quote PDF needs to reflect pricing data.
- `admin/opportunity-management` — Use when the relationship between products, Pricebooks, and opportunity stage/forecast rollup is the core design question.
- `admin/collaborative-forecasts` — Use when Product Schedules are being used as the forecast object and schedule-based revenue rollup needs to be configured.
