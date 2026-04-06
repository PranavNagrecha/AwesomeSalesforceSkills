# Examples — Products and Pricebooks

## Example 1: Setting Up a Two-Pricebook Catalog for Direct and Partner Sales

### Context

A SaaS company sells software licenses directly to enterprise customers and through a reseller partner network. Direct customers pay list price; partners receive a 20% discount. The product catalog has 15 products across three product families.

### Problem

The admin tried to add a product to a custom "Partner" Pricebook but received an error: "You must create a PricebookEntry in the Standard Pricebook before creating entries in custom Pricebooks." Additionally, a rep in Europe reported that a product was not showing up when creating an Opportunity in EUR.

### Solution

**Step 1 — Establish the Standard Pricebook entries:**

For each product, add a PricebookEntry to the Standard Pricebook in every active currency:

```
Standard Pricebook:
  - Product: Annual License Pro (USD, UnitPrice: $10,000)
  - Product: Annual License Pro (EUR, UnitPrice: €9,200)
  - Product: Implementation Services (USD, UnitPrice: $5,000)
  - Product: Implementation Services (EUR, UnitPrice: €4,600)
  ... (repeat for all 15 products × 2 currencies = 30 entries)
```

**Step 2 — Create the Partner Pricebook and add entries:**

```
Partner Pricebook:
  - Product: Annual License Pro (USD, UnitPrice: $8,000)  ← 20% discount
  - Product: Annual License Pro (EUR, UnitPrice: €7,360)
  - Product: Implementation Services (USD, UnitPrice: $4,000)
  - Product: Implementation Services (EUR, UnitPrice: €3,680)
  ... (repeat for all 15 products × 2 currencies = 30 entries)
```

**Step 3 — Assign Pricebook to Opportunities:**

Use a Flow or validation rule to auto-set `Opportunity.Pricebook2Id` based on the Account's `Partner_Type__c` field so reps do not have to manually select the Pricebook.

**Step 4 — Test:**

Create one test Opportunity per currency per Pricebook type. Confirm all 15 products appear in the picker with the correct `UnitPrice` for that Pricebook and currency combination.

### Key Takeaway

The Standard Pricebook is a platform requirement, not an optional anchor. Every product needs a Standard Pricebook entry before it can appear in any custom Pricebook — regardless of whether the Standard Pricebook is ever used for selling. Multi-currency adds a multiplicative factor: 15 products × 2 currencies × 2 Pricebooks = 60 PricebookEntry records.

---

## Example 2: Enabling Revenue Schedules for a Subscription Product

### Context

A company sells annual software contracts that are billed quarterly. The finance team wants Salesforce to track four quarterly invoices against each Opportunity product so that revenue can be forecasted month by month using Collaborative Forecasting set to use Product Schedules as the forecast object.

### Problem

The rep added the product to the Opportunity but saw no schedule section on the OpportunityLineItem. The admin confirmed Product Schedules were not enabled at the org level.

### Solution

**Step 1 — Enable at the org level:**

Navigate to Setup > Products > Product Schedules Settings. Check "Enable Revenue Schedules." Save.

**Step 2 — Configure the product's default schedule:**

On the Product2 record for "Annual Software Contract":
- Schedule Type: Revenue
- Number of Installments: 4
- Installment Period: Quarterly
- Installment Type: Divide Amount Into Multiple Installments

**Step 3 — Verify on Opportunity:**

After adding the product to an Opportunity, click into the OpportunityLineItem and confirm the Revenue Schedule section appears with 4 quarterly installments dividing the total UnitPrice × Quantity.

**Step 4 — Confirm forecast interaction:**

In Collaborative Forecasting Setup, verify that the forecast type uses "Product Schedules" as the forecast source. If still set to "Opportunity," schedule data will not roll into the forecast — the forecast type object must match.

### Key Takeaway

Revenue Schedules require explicit enablement at both the org level (Setup) and the product level (Schedule Type field). Enabling at only one level will silently fail — the field does not appear on the product until org-level is on, and schedules do not generate on OpportunityLineItems until the product's Schedule Type is set.

---

## Example 3: Safe Product Deactivation During Catalog Cleanup

### Context

A company is sunsetting an older product line. The admin needs to remove three products from the catalog so reps cannot add them to new Opportunities, while preserving all historical closed-won Opportunity data that references those products.

### Problem

The admin was considering deleting the Product2 records entirely. A colleague warned that this could affect historical reporting, but the admin was not sure exactly what would break.

### Solution

**Do NOT delete — deactivate instead:**

1. On each of the three Product2 records, uncheck the "Active" checkbox (`IsActive = false`) and save.
2. Verify: open a new Opportunity, click "Add Products," and confirm the deactivated products do not appear in the picker.
3. Verify historical integrity: open a closed-won Opportunity that used one of those products. Confirm the OpportunityLineItem still shows the product name, quantity, and price correctly.
4. Verify PricebookEntry records are untouched: query `SELECT Id, IsActive FROM PricebookEntry WHERE Product2Id IN (...)`. The PricebookEntry records remain; they are not deleted when a product is deactivated.

**If deletion is truly required (rare):**

- Deletion is only safe if the product has NEVER been used on any Opportunity, Quote, Order, or Contract.
- Run a query: `SELECT COUNT() FROM OpportunityLineItem WHERE PricebookEntry.Product2Id = '<id>'` — if count > 0, do not delete.
- Similarly check `QuoteLineItem`, `OrderItem`, and any CPQ line objects if installed.

### Key Takeaway

Deactivation is always the safe choice. It removes the product from future selection without touching any historical records or associated PricebookEntry junction records. Deletion is a one-way door that risks breaking reporting, managed package references, and integration data.
