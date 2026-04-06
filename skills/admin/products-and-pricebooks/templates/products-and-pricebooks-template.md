# Products and Pricebooks — Work Template

Use this template when configuring or auditing the Salesforce product catalog and Pricebook structure. Fill in every section before starting implementation work.

---

## 1. Org Context

| Field | Value |
|---|---|
| Org edition | <!-- e.g., Enterprise, Unlimited --> |
| Multi-currency enabled? | <!-- Yes / No --> |
| Active currencies | <!-- e.g., USD, EUR, GBP --> |
| CPQ (SBQQ) installed? | <!-- Yes / No — if Yes, stop and use cpq-vs-standard-products-decision skill --> |
| Product Schedules needed? | <!-- Revenue / Quantity / Both / None --> |
| Number of existing products | <!-- approximate count --> |
| Number of existing Pricebooks | <!-- Standard + any custom --> |

---

## 2. Product Catalog Requirements

List each product line and its attributes:

| Product Name | Product Code | Family | Schedule Type | Active? |
|---|---|---|---|---|
| <!-- e.g., Annual License Pro --> | <!-- e.g., LIC-001 --> | <!-- e.g., Software --> | <!-- Revenue / Quantity / Both / None --> | <!-- Yes / No --> |
| | | | | |
| | | | | |

---

## 3. Pricebook Structure

### Standard Pricebook

Will the Standard Pricebook be used for selling? <!-- Yes / No / Only as anchor (required) -->

### Custom Pricebooks Needed

| Pricebook Name | Purpose / Customer Segment | Active? |
|---|---|---|
| <!-- e.g., Partner Pricebook --> | <!-- e.g., Reseller partners — 20% discount --> | <!-- Yes / No --> |
| | | |

---

## 4. PricebookEntry Matrix

For each combination of Product × Pricebook × Currency, document the intended `UnitPrice`:

| Product | Pricebook | Currency | UnitPrice |
|---|---|---|---|
| <!-- e.g., Annual License Pro --> | Standard Pricebook | USD | <!-- e.g., 10000.00 --> |
| <!-- e.g., Annual License Pro --> | Standard Pricebook | EUR | <!-- e.g., 9200.00 --> |
| <!-- e.g., Annual License Pro --> | Partner Pricebook | USD | <!-- e.g., 8000.00 --> |
| <!-- e.g., Annual License Pro --> | Partner Pricebook | EUR | <!-- e.g., 7360.00 --> |
| | | | |

**Note:** Standard Pricebook entries MUST be created before any custom Pricebook entries for the same product.

---

## 5. Pricebook Assignment Automation

How will `Opportunity.Pricebook2Id` be set on new Opportunities?

- [ ] Manual selection by rep
- [ ] Record-Triggered Flow (describe trigger field: <!-- e.g., Account.Partner_Type__c --> )
- [ ] Default set via Page Layout / field default
- [ ] External integration sets it on creation

Automation owner: <!-- Name or team -->
Flow/automation name: <!-- if building or referencing one -->

---

## 6. Product Schedules Configuration (if applicable)

Skip this section if Product Schedules are not required.

| Setting | Value |
|---|---|
| Revenue Schedules enabled in Setup? | <!-- Yes / No --> |
| Quantity Schedules enabled in Setup? | <!-- Yes / No --> |
| Default installments per product | <!-- e.g., 12 for monthly billing --> |
| Installment period | <!-- Monthly / Quarterly / Annually / Custom --> |
| Installment type | <!-- Divide Amount / Repeat Amount --> |
| Collaborative Forecasting forecast object | <!-- Opportunity / Product Schedules / OpportunityLineItem --> |

---

## 7. Product Deactivation Plan (if applicable)

List products being retired and confirm they have been verified safe to deactivate:

| Product Name | Product2 ID | Open OLIs? | Action |
|---|---|---|---|
| <!-- product name --> | <!-- ID --> | <!-- Yes / No — if Yes, resolve before deactivating --> | <!-- Deactivate / Keep active --> |

---

## 8. Pre-Deployment Checklist

Run through before deploying to production:

- [ ] All Product2 records created with correct product code and family
- [ ] Standard Pricebook entries created for ALL products in ALL active currencies
- [ ] Custom Pricebook entries created for all required product/currency combinations
- [ ] Pricebook assignment automation tested with non-admin user in sandbox
- [ ] Product Schedules enabled at org level if required; each product's schedule type confirmed
- [ ] No Pricebook referenced by open Opportunities is being deleted
- [ ] Checker script run: `python3 skills/admin/products-and-pricebooks/scripts/check_products_and_pricebooks.py --manifest-dir <path>`
- [ ] Test Opportunities created in each currency — all required products appear in picker with correct prices
- [ ] Sales rep profile confirmed to have read access on Pricebook2 and PricebookEntry

---

## 9. Notes and Decisions Log

<!-- Document any decisions, deviations from standard patterns, or open questions here -->

| Date | Decision | Owner |
|---|---|---|
| <!-- YYYY-MM-DD --> | <!-- what was decided and why --> | <!-- who decided --> |
