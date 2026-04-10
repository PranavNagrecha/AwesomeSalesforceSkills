---
name: historical-order-migration
description: "Use when loading historical CPQ orders, contracts, subscriptions, and assets into Salesforce CPQ so that future renewals and amendments work correctly — covering the CPQ Legacy Data Upload mechanism, strict object load sequencing, required field values, and pre/post-load configuration. NOT for opportunity migration (use opportunity-pipeline-migration). NOT for standard Salesforce Orders without CPQ. NOT for asset-based renewal model orgs. NOT for quoting net-new business."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "how do I load historical orders into Salesforce CPQ so renewal quotes work correctly"
  - "CPQ subscriptions loaded but renewal quote line items are blank or wrong"
  - "legacy contracts not generating correct renewal opportunities after data migration"
  - "how to migrate historical CPQ data without breaking future renewals and amendments"
  - "what is the correct order to load CPQ quotes, contracts, subscriptions, and assets for historical migration"
  - "CPQ Legacy Data Upload — what fields are required on SBQQ__Subscription__c for renewals"
  - "asset root id causing silent corruption on first renewal after data load"
tags:
  - cpq
  - legacy-data-upload
  - historical-orders
  - subscriptions
  - contracts
  - renewals
  - sbqq
  - data-migration
  - bulk-api
inputs:
  - "Source system export: historical order/contract data with product lines, start/end dates, quantities, unit prices, discount information"
  - "CPQ org configuration: renewal model (contract-based vs asset-based), renewal pricing method, subscription retention setting"
  - "Product2 and SBQQ__Product__c catalog: must exist in target org before any quote lines are loaded"
  - "Account records: must exist before Quotes and Contracts are created"
  - "Opportunity records: required as parent of SBQQ__Quote__c if present in source"
  - "User records: OwnerId resolution for Quote and Contract records"
  - "Pricebook2: active Price Book to assign to CPQ quotes"
outputs:
  - "Load sequence specification: disable rules → Quotes → QuoteLines → Contracts → Subscriptions → Assets"
  - "Field mapping CSV templates for each CPQ object in the load sequence"
  - "Pre-load configuration checklist (batch size, rules bypass, renewal model verification)"
  - "Post-load validation queries for subscription term dates, asset quantities, and renewal readiness"
  - "Completed historical-order-migration-template.md"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# Historical Order Migration

This skill activates when a practitioner needs to load historical order, contract, subscription, and asset data into an org running Salesforce CPQ (SBQQ) so that future renewal and amendment processes work correctly. It covers the CPQ Legacy Data Upload mechanism — the only supported path for this use case — and the strict object sequencing, field requirements, and configuration gates that govern it.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm contract-based renewal model**: CPQ Legacy Data Upload is only supported when the CPQ org uses the contract-based renewal model (`SBQQ__RenewalModel__c` = `Contract Based` on the CPQ package settings custom setting). Asset-based renewal model orgs cannot use this mechanism. Confirm the setting before any load begins.
- **Disable CPQ price and product rules**: CPQ triggers price rules and product rules on every Quote and Quote Line save. These rules fire during data load and cause incorrect pricing calculations, field overwrites, or load failures. The rules must be disabled before any Legacy Data Upload records are inserted and re-enabled only after the full load is validated.
- **Batch size must be 1**: CPQ Legacy Data Upload requires a batch size of 1 for all inserted objects. Loading with batch size > 1 bypasses required CPQ calculation triggers and produces records that look correct in the data but fail silently at renewal time. This applies to all tools: Data Loader, Bulk API, any ETL platform.
- **Asset Root Id and Revised Asset field interaction**: `SBQQ__Asset__c.SBQQ__RootId__c` must be null if `SBQQ__Asset__c.SBQQ__RevisedAsset__c` is populated. Populating both fields simultaneously produces records that look correct but corrupt the renewal/amendment chain silently. The corruption surfaces only at the first renewal attempt, not at insert time.
- **Required CPQ fields for renewal readiness**: `SBQQ__Subscription__c` records must have correct values for `SBQQ__StartDate__c`, `SBQQ__EndDate__c`, `SBQQ__Quantity__c`, `SBQQ__NetPrice__c`, `SBQQ__RegularPrice__c`, `SBQQ__Product__c`, and `SBQQ__Contract__c`. Missing or incorrect values on any of these fields cause renewal quote generation to produce blank or miscalculated lines.

---

## Core Concepts

### CPQ Legacy Data Upload — What It Is and Why It Is Required

CPQ Legacy Data Upload is Salesforce's designated mechanism for inserting historical order and contract data in a way that supports future renewals and amendments. It is not a standard data migration approach — it is a controlled insert process that triggers specific CPQ calculation hooks on each record.

Without Legacy Data Upload, records inserted via standard Bulk API or Data Loader bypass the CPQ package's renewal-preparation logic. The resulting subscriptions and assets may appear correct in the data but do not have the internal field values that CPQ requires to generate accurate renewal quotes. This failure mode is silent: no error is thrown at load time; the problem surfaces only when the first renewal opportunity is created.

Legacy Data Upload is only available for orgs on the **contract-based renewal model**. Orgs using asset-based renewals have a different renewal mechanism that does not rely on SBQQ__Subscription__c records in the same way.

### Object Load Sequence

CPQ enforces referential integrity and triggers package logic in a strict sequence. The required load order for historical CPQ data is:

1. **Account** — must exist before any other record; typically already present
2. **Opportunity** — required as the parent of SBQQ__Quote__c if the source data includes opportunity records
3. **Product2 / SBQQ__Product__c** — must exist before Quote Lines can reference them
4. **SBQQ__Quote__c** (CPQ Quote) — must be inserted with `SBQQ__Status__c` = `Approved` and `SBQQ__Primary__c` = `true`; the approved primary quote is what CPQ uses to create the Contract
5. **SBQQ__QuoteLine__c** (CPQ Quote Line) — must be inserted after the parent Quote exists
6. **Contract** — the standard Salesforce Contract object; must reference the Account; SBQQ will link it to the Quote via `SBQQ__Quote__c` on the Contract
7. **SBQQ__Subscription__c** — references both the Contract and the Product; contains the subscription term, pricing, and quantity data that drives renewal generation
8. **SBQQ__Asset__c** — references the Account and optionally the Subscription; required for amendment workflows

Any deviation from this sequence produces orphaned child records that either fail at insert or produce broken renewal chains.

### SBQQ__Quote__c Required Fields for Legacy Upload

The CPQ Quote inserted during Legacy Data Upload is not a working salesperson quote — it is a historical record that establishes the approved configuration. Required fields:

- `SBQQ__Status__c` = `Approved`
- `SBQQ__Primary__c` = `true`
- `SBQQ__Account__c` = the parent Account Id
- `SBQQ__Opportunity2__c` = the parent Opportunity Id (if applicable)
- `SBQQ__StartDate__c` and `SBQQ__EndDate__c` matching the contract term
- `SBQQ__SubscriptionTerm__c` = numeric term in months

A Quote that is not `Approved` and `Primary` will not be correctly linked to its Contract by CPQ's renewal logic.

### SBQQ__Subscription__c — The Renewal Engine

`SBQQ__Subscription__c` records are the core of the CPQ renewal model. When a renewal opportunity is created, CPQ reads the active subscriptions on the expiring contract and generates renewal quote lines from them. The accuracy of the renewal quote is entirely dependent on the accuracy of the subscription records.

Key fields that drive renewal quote line generation:

- `SBQQ__StartDate__c` / `SBQQ__EndDate__c` — defines the subscription term; renewal start date is derived from the subscription end date
- `SBQQ__Quantity__c` — quantity carried into the renewal
- `SBQQ__RegularPrice__c` / `SBQQ__NetPrice__c` / `SBQQ__CustomerPrice__c` — pricing fields used to calculate renewal price depending on the org's renewal pricing method
- `SBQQ__RenewalQuantity__c` — if populated, overrides `Quantity` for renewal purposes
- `SBQQ__Contract__c` — parent contract reference; this is how CPQ discovers which subscriptions belong to the renewing contract
- `SBQQ__Product__c` — the CPQ product; must match an active Product2/SBQQ__Product__c record

---

## Common Patterns

### Pattern: Full Legacy Data Upload for Contract-Based Renewal Org

**When to use:** The org uses contract-based renewals and historical orders from a legacy system need to be loaded so that CPQ generates correct renewal quotes at the end of the original subscription term.

**How it works:**

1. Disable CPQ price rules and product rules via CPQ package settings (or use `SBQQ__DisableAmendmentCoterminusCheck__c` and related settings depending on org version).
2. Set Data Loader / Bulk API batch size to 1 for all CPQ objects in this load.
3. Insert SBQQ__Quote__c records: `Status = Approved`, `Primary = true`, correct Account/Opportunity references, subscription term dates.
4. Insert SBQQ__QuoteLine__c records referencing the parent Quote and the correct Product2/SBQQ__Product__c.
5. Insert Contract records referencing Account; populate `SBQQ__Quote__c` on the Contract to link it to the approved CPQ quote.
6. Insert SBQQ__Subscription__c records referencing the Contract and Product; populate all pricing and term fields accurately.
7. Insert SBQQ__Asset__c records if amendments will be used; ensure `SBQQ__RootId__c` is null when `SBQQ__RevisedAsset__c` is populated.
8. Re-enable CPQ price and product rules.
9. Run post-load validation: query subscriptions by contract, verify term dates and pricing fields, test renewal quote generation in sandbox.

**Why not load with standard Bulk API at default batch size:** CPQ's package triggers that prepare subscription records for renewal fire only when batch size is 1. Higher batch sizes cause the triggers to fire in bulk mode and skip renewal-preparation logic, producing records that appear correct in queries but generate blank or incorrectly priced renewal quote lines.

### Pattern: Subscription-Only Load for Orgs with Existing Contracts

**When to use:** The target org already has Account, Opportunity, and Contract records loaded via a prior migration wave. Only CPQ Subscriptions and Assets need to be added to enable renewal generation.

**How it works:**

1. Confirm all parent Contracts exist and are in `Activated` status.
2. Disable CPQ price and product rules.
3. Set batch size to 1.
4. Insert SBQQ__Subscription__c with `SBQQ__Contract__c` referencing existing Contract external IDs.
5. Validate subscription count per contract matches source system subscription line count.
6. Insert SBQQ__Asset__c if amendment support is needed.
7. Re-enable rules.
8. Spot-test renewal quote generation on one or more contracts before proceeding to production load.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org uses contract-based renewal model | CPQ Legacy Data Upload with batch size 1 and rules disabled | Only supported mechanism for renewal-ready historical load |
| Org uses asset-based renewal model | Legacy Data Upload is not applicable; consult CPQ Asset-Based Renewal docs | Legacy Data Upload only supports contract-based model |
| Source data has both historical orders and active subscriptions | Load all historical first, activate contracts, then load subscriptions | Contract must be Activated before subscriptions are treated as active by renewal engine |
| Asset has been revised/amended in source system | Populate SBQQ__RevisedAsset__c; leave SBQQ__RootId__c null | Populating both fields silently corrupts the amendment chain |
| Renewal quotes generating blank lines after load | Check SBQQ__Subscription__c pricing fields and term dates | Renewal line generation reads directly from subscription field values |
| Load failing on CPQ Quote Lines | Confirm parent Quote is inserted first and has correct Status and Primary values | Quote Line insert requires a valid parent Quote with Approved/Primary flags |
| Price rules firing during load and corrupting prices | Disable price rules before load, re-enable after validation | CPQ price rules execute on every Quote and Quote Line save, overwriting manually set prices |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Verify prerequisites**: Confirm the org is on contract-based renewal model (`SBQQ__RenewalModel__c`). Confirm all parent records (Accounts, Opportunities, Products) exist in the target org. Document the load sequence and assign external ID fields to every CPQ object that needs cross-reference resolution.
2. **Disable CPQ automation**: Disable price rules and product rules via CPQ package settings before inserting any records. Record the current settings so they can be restored exactly after the load completes.
3. **Load Quotes then Quote Lines at batch size 1**: Insert SBQQ__Quote__c with `Status = Approved` and `Primary = true`. Then insert SBQQ__QuoteLine__c. Verify record counts after each step before proceeding.
4. **Load Contracts and link to Quotes**: Insert or upsert Contract records. Populate `SBQQ__Quote__c` on each Contract to link it to the approved CPQ quote. Set Contract `Status` to `Activated` if the subscription term has started.
5. **Load Subscriptions at batch size 1**: Insert SBQQ__Subscription__c with all required pricing and term fields populated. Verify every subscription has a non-null `SBQQ__Contract__c`, `SBQQ__Product__c`, `SBQQ__StartDate__c`, `SBQQ__EndDate__c`, and `SBQQ__Quantity__c`.
6. **Load Assets (if amendments required)**: Insert SBQQ__Asset__c. For revised assets, populate `SBQQ__RevisedAsset__c` and leave `SBQQ__RootId__c` null. For root (original) assets, confirm `SBQQ__RootId__c` references the asset's own Id (set by CPQ post-insert) or is null.
7. **Re-enable CPQ automation and validate**: Re-enable price and product rules. Run post-load validation queries (see Review Checklist). Test renewal quote generation on a sample of contracts in a sandbox before declaring the migration complete.

---

## Review Checklist

Run through these before marking historical CPQ order migration complete:

- [ ] Org confirmed on contract-based renewal model before any load began
- [ ] CPQ price rules and product rules disabled before first insert
- [ ] Batch size set to 1 for all CPQ object loads (Quote, Quote Line, Subscription, Asset)
- [ ] All SBQQ__Quote__c records have `Status = Approved` and `Primary = true`
- [ ] All SBQQ__Subscription__c records have non-null `SBQQ__Contract__c`, `SBQQ__Product__c`, `SBQQ__StartDate__c`, `SBQQ__EndDate__c`, `SBQQ__Quantity__c`
- [ ] SBQQ__Asset__c records with `SBQQ__RevisedAsset__c` populated have `SBQQ__RootId__c` = null
- [ ] Contract records are in `Activated` status where the subscription term has begun
- [ ] CPQ price rules and product rules re-enabled after load completed
- [ ] Post-load validation query: subscription count per contract matches source
- [ ] Test renewal quote generation triggered on at least one contract in sandbox

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Batch size > 1 silently breaks renewals** — Loading CPQ Subscriptions or Assets with batch size greater than 1 causes CPQ's package triggers to run in bulk mode, skipping the renewal-preparation logic. The records insert without error and look correct in SOQL queries. The silent corruption surfaces only when the first renewal opportunity is created — typically months after the migration.

2. **SBQQ__Asset__c Root Id and Revised Asset mutual exclusivity** — `SBQQ__RootId__c` must be null if `SBQQ__RevisedAsset__c` is populated. Populating both fields does not cause an insert error; CPQ accepts the record. The corruption appears at the first amendment or renewal: CPQ follows both the root chain and the revised chain and creates duplicate or malformed amendment quote lines.

3. **CPQ Legacy Data Upload requires contract-based renewal model** — The Legacy Data Upload process is only defined and tested for the contract-based renewal model. Asset-based renewal orgs have a different internal mechanism for renewal generation. Using Legacy Data Upload procedures in an asset-based renewal org produces subscriptions that do not participate in renewal generation.

4. **Price and product rules fire during load if not disabled** — CPQ price rules execute on every Quote and Quote Line insert/update, even during data loads. A price rule that recalculates net price based on discount schedules will overwrite the historically correct price being loaded from the source system. Rules must be disabled before load, not just during Quote insert — they can fire again on Subscription and Asset saves via triggered flows.

5. **SBQQ__Quote__c Status and Primary flags are required, not cosmetic** — A CPQ Quote that is not `Approved` and `Primary` does not participate in the Contract-to-Quote linkage that CPQ uses during renewal generation. Inserting a historical Quote with `Status = Draft` produces a record that looks like a valid quote but is invisible to CPQ's renewal engine. The Contract will not produce correct renewal quotes because no approved primary quote is linked to it.

6. **Contract must be Activated before subscriptions are used in renewal** — SBQQ__Subscription__c records on a Contract that is in `Draft` status are not treated as active subscriptions by CPQ's renewal engine. If historical contracts are left in Draft after the migration, renewal opportunity generation will not fire for them at the end of the subscription term.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `historical-order-migration-template.md` | Fill-in-the-blank work template capturing org renewal model, load sequence, external ID mapping, CPQ settings bypass plan, and post-migration validation queries |
| `check_historical_order_migration.py` | stdlib Python checker that validates CPQ migration CSV files for required field coverage, batch size configuration, and common Asset Root Id / Revised Asset conflicts |

---

## Related Skills

- `opportunity-pipeline-migration` — use when migrating standard Opportunity records and OpportunityLineItems; does not cover CPQ-specific objects
- `data-migration-planning` — use for multi-object migration architecture, tool selection, external ID strategy, and rollback planning
- `cpq-data-model` — use to understand the CPQ object schema, field dependencies, and package behavior before designing the migration
- `bulk-api-and-large-data-loads` — use for Bulk API 2.0 job configuration, monitoring, and error handling mechanics

---

## Official Sources Used

- CPQ Legacy Data Upload — https://help.salesforce.com/s/articleView?id=sf.cpq_legacy_data_upload.htm&type=5
- Legacy Data Upload with Renewals and Amendments (KA-000384279) — https://help.salesforce.com/s/articleView?id=000384279&type=1
- SBQQ__Subscription__c Object Fields for Legacy Upload — https://help.salesforce.com/s/articleView?id=sf.cpq_subscription_fields.htm&type=5
- Salesforce CPQ Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_guide.htm
- Bulk API 2.0 Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_intro.htm
