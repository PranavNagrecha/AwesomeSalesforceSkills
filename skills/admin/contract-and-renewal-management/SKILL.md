---
name: contract-and-renewal-management
description: "Use when configuring or troubleshooting Salesforce CPQ contract creation, subscription management, amendment quotes, or renewal quotes. Trigger keywords: contract, amendment, renewal, subscription, co-termination, SBQQ__Subscription__c. NOT for designing the amendment/renewal architecture or swap pattern — use architect/subscription-management-architecture. NOT for amending or renewing contracts from Apex — use apex/cpq-api-and-automation. Also covers the standard Contract and Order objects underneath CPQ — Contract Status vs StatusCode, activation locking, EndDate auto-calculation, ContractSettings and OrderSettings, reduction orders, and renewal-reminder automation. Trigger keywords: Contract, ContractStatus, StatusCode, ActivatedDate, OwnerExpirationNotice, ContractTerm, EndDate, Order, OrderItem, reduction order, ContractSettings, OrderSettings, renewal reminder. NOT for Revenue Cloud or Subscription Management objects — use architect/revenue-cloud-architecture and architect/subscription-management-architecture."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Performance
triggers:
  - "how do I create a contract from a CPQ opportunity"
  - "amendment quote is not picking up updated list prices for existing subscription lines"
  - "renewal quote is not being generated automatically after contract activation"
  - "co-termination is extending lines beyond the expected end date"
  - "large-scale amendment is timing out or failing with more than 1000 subscription lines"
  - "CPQ contract amendment renewal subscription management co-termination"
  - "contract end date is blank after the data load"
  - "cannot update fields when activating a contract"
  - "renewal reminder did not fire for contracts expiring next month"
  - "reduce the quantity on an order that is already activated"
tags:
  - cpq
  - contracts
  - amendments
  - renewals
  - subscriptions
  - sbqq
  - orders
  - contract-lifecycle
inputs:
  - "CPQ package version installed in org"
  - "Opportunity with SBQQ__Quoted__c = true and at least one Quote Line with SBQQ__SubscriptionPricing__c set"
  - "CPQ Settings: Contract, Renewal, and Amendment preference values"
  - "Whether the org uses auto-renewal or agent-initiated renewal"
  - "Approximate number of subscription lines on contracts being amended"
  - "Contract Settings: whether Auto-calculate Contract End Date is on"
  - "Order Settings: whether Orders and Reduction Orders are enabled"
  - "The full Contract Status label list and the StatusCode category each label sits in"
outputs:
  - "Activated Contract with child SBQQ__Subscription__c records"
  - "Amendment Quote with preserved original subscription pricing on existing lines"
  - "Renewal Quote linked via SBQQ__RenewedContract__c with configurable term"
  - "Decision guidance on async vs synchronous amendment processing"
  - "Deployable ContractSettings / OrderSettings / ContractStatus / ValidationRule metadata"
  - "A renewal-reminder flow intent plus the SOQL behind it"
dependencies:
  - cpq-pricing-rules
  - cpq-product-catalog-setup
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Contract and Renewal Management

This skill covers the full Salesforce CPQ contract lifecycle: creating contracts from won opportunities, managing subscription records, generating amendment quotes to modify active contracts, and generating renewal quotes when contracts approach expiration. It activates when a practitioner needs to configure, debug, or extend CPQ contract or renewal behavior.

---

## Before Starting

Gather this context before working on anything in this domain:

- Verify that the Salesforce CPQ package is installed and that at least one Quote Line on the originating Opportunity has `SBQQ__SubscriptionPricing__c` populated (Fixed Price or Percent Of Total). Without this field, the contract creation process will not generate `SBQQ__Subscription__c` child records.
- Confirm whether the org relies on automatic renewal (CPQ Setting: Auto Renew) or manually initiated renewal. This determines whether a Renewal Opportunity and Renewal Quote are created automatically on contract activation.
- The most common wrong assumption is that editing a product's list price after a contract is activated will update the prices on an amendment quote for existing subscription lines. It will not — existing lines are locked to the original contracted price.
- Establish which layer the request is actually about. The **standard** `Contract` and `Order` objects (Status/StatusCode, activation locking, `ContractTerm`/`EndDate`, `ContractSettings`, `OrderSettings`, reduction orders) are documented platform behaviour and are covered here and in `references/metadata-examples.md`. **Salesforce CPQ** (`SBQQ__*`) is a managed package layered on top of them; its objects appear in none of the platform guides. Revenue Cloud and Subscription Management are a third layer again — route those to `architect/revenue-cloud-architecture` and `architect/subscription-management-architecture`.
- Relevant platform limits: synchronous amendment processing is reliable up to approximately 200 subscription lines. Above 1,000 lines, async processing via `SBQQ.ContractManipulationAPI` or the batch job framework is required. Between 200 and 1,000 lines, behavior depends on org governor limits and should be tested. **UNVERIFIED (2026-09-05): the 200 / 1,000 line thresholds are CPQ managed-package rules of thumb. They are not stated in any Salesforce platform guide (`SBQQ__` returns zero hits in the Object Reference, Metadata API Developer Guide, Apex Developer Guide and Apex Reference Guide), and the App Limits cheat sheet publishes no Contract or Order limits at all. Measure the real ceiling in your own org before quoting either number to a customer.**

---

## Questions to Ask Before Configuring

Ask these before touching Setup or writing a line of metadata. Each one maps to a gotcha that costs a redesign if it surfaces late.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Are we on standard Contracts and Orders, Salesforce CPQ, or Revenue Cloud?" | The three layers share the word "contract" and share almost no behaviour; CPQ objects are absent from every platform guide | The routing decision, and which of this skill's files apply versus `architect/subscription-management-architecture` |
| "List every Contract Status label the business uses, and which status category each one sits in." | A label added inside the `Activated` category breaks every filter written against `Status = 'Activated'` (Gotcha 7) | The `ContractStatus` value set to deploy, and the exact `ISPICKVAL` list the validation rule must enumerate |
| "Who activates contracts, and through what — the UI, Data Loader, a Flow, or an integration?" | `Status` is the only field accepted on the activating save, and activation cannot be reversed (Gotcha 6) | The two-DML activation sequence, and whether a sandbox dry run on real data is mandatory |
| "Is the contract end date something the business types, or something the term implies?" | `autoCalculateEndDate` decides whether `EndDate` is writable at all; a mapped `EndDate` is silently dropped when it is on (Gotcha 8) | The `ContractSettings` value, the migration field map, and the null-`EndDate` post-load gate |
| "What is the renewal notice window, in days, and who receives it?" | `OwnerExpirationNotice` accepts only 15, 30, 45, 60, 90, 120 — anything else needs a flow (Gotcha 12) | Either a legal picklist value or a schedule-triggered flow spec, and a decision not to run both |
| "Will customers ever reduce quantity mid-term, and on what — a contract or an order?" | Reduction orders need `enableReductionOrders` on before any order data exists, and deleted `OrderItem` rows never come back (Gotcha 11) | The `OrderSettings` flags to deploy on day one rather than retrofit |
| "Which contracts already exist, and do they all have both signature dates?" | A validation rule on activation fails every legacy activated contract on its next save, and those records cannot be walked back to Draft | A decision to deploy the rule active or inactive, and the remediation list |

What a proper configuration adds over just creating contracts: activation is a reviewed two-step that cannot happen without signatures, every renewal query keys on the status *category* so new labels never make contracts disappear from the pipeline, end dates come from the term rather than from whatever a spreadsheet held, and the reduction path exists before the first customer needs it rather than after.

---

## Core Concepts

### The Standard Contract and Order Lifecycle

CPQ sits on top of the standard `Contract` and `Order` objects and inherits their rules. These are the ones documented in the Object Reference, and they bite whether or not CPQ is installed.

| Fact | Consequence |
|---|---|
| `Contract.AccountId` is required; `Contract.ContractNumber` is an autonumber | A contract cannot exist without an account, and you cannot choose its number |
| `Contract.Status` is a label picklist; `Contract.StatusCode` is its category (`Draft`, `InApproval`, `Activated`) and is not writable | Query and filter on `StatusCode`; write `Status` |
| Contracts must be created non-activated, and `Status` is the only field accepted on the activating update | Activation is always two DML operations |
| After activation the status cannot change and the record cannot be deleted | There is no undo for a bad bulk activation |
| `EndDate` is read-only and equals `StartDate` + `ContractTerm` while `autoCalculateEndDate` is on | Map the term, not the end date, on migration |
| `ActivatedById` / `ActivatedDate` are populated by the platform; there is no `IsActivated` field | Detect activation with `StatusCode = 'Activated'`, not a boolean |
| `OwnerExpirationNotice` is a restricted picklist of 15/30/45/60/90/120 days | Any other window needs a scheduled flow |
| `ContractLineItem` requires an `AssetId` and belongs to service contracts (Entitlement Management) | Commercial lines live on `Order` / `OrderItem`, not here |
| `Order.ContractId` is nillable, and `Order.AccountId` and `ContractId` update only while `StatusCode` is `Draft` | An order can exist with no contract, but it cannot be re-parented after activation |
| Orders follow the same activation rule as contracts, and can return to `Draft` only when no child reduction order products exist | Reduction is the point of no return, not activation |

Every claim in that table is cited line-by-line in `references/metadata-examples.md` and `references/gotchas.md` (Gotchas 6–12). The deployable `ContractSettings`, `OrderSettings`, `ContractStatus` value set, activation validation rule, renewal-tracking custom fields and renewal-reminder flow intent are all in `references/metadata-examples.md`.

### Contract Creation Requirements

A CPQ contract is created by setting `SBQQ__Contracted__c = true` on an Opportunity that is in a Closed Won stage and has a primary CPQ Quote with at least one subscribed Quote Line. The system reads the primary Quote (`SBQQ__PrimaryQuote__c`) and creates child `SBQQ__Subscription__c` records under the resulting standard Contract object. Each subscription record captures the product, quantity, pricing, subscription start date, and subscription end date from the Quote Line.

If no Quote Lines have `SBQQ__SubscriptionPricing__c` set, no subscription records are created and the contract lifecycle features (amendment, renewal) will not function.

### Amendment Quotes and Subscription Line Locking

An amendment quote is created from an active contract and allows quantity changes, product additions, and product removals. The critical behavior: **existing subscription lines on an amendment quote carry the original contracted price**. Updated list prices in the price book are applied only to net-new lines added during the amendment. This is intentional — it protects customers from unexpected price increases mid-contract.

Co-termination is applied automatically during amendment: all subscription lines are forced to share the same end date as the earliest-ending subscription on the contract. Term precedence is: Quote Line level > Quote Group level > Quote header level.

Amendments also generate co-terming proration. If a line originally ran 12 months and the amendment starts at month 6, the amended quantity is prorated to the remaining 6 months.

### Renewal Quotes

A renewal quote is generated from an active contract, linked via the `SBQQ__RenewedContract__c` lookup on the resulting Opportunity. The term of the renewal quote defaults to `SBQQ__DefaultRenewalTerm__c` on the Contract. If this field is blank, CPQ falls back to the term defined in CPQ Settings.

Renewal quotes reprice all lines at **current** price book prices unless contracted prices exist for the account. This is the opposite behavior from amendments, where existing lines are locked.

### Large-Scale Amendment Processing

When a contract has more than approximately 1,000 subscription lines, synchronous amendment generation times out. CPQ provides an asynchronous path: instead of clicking the Amend button on the contract record, an administrator or developer calls the `SBQQ.ContractManipulationAPI.amend()` method, which queues a batch job. The resulting amendment quote is linked to the contract once the job completes. Monitoring is done via `AsyncApexJob` or via the CPQ amendment status field on the contract.

---

## Common Patterns

### Pattern: Standard Amendment from Active Contract

**When to use:** Changing quantity or adding/removing products on a contract with fewer than ~200 subscription lines.

**How it works:**
1. Navigate to the active Contract record.
2. Click the **Amend** button (CPQ quick action).
3. CPQ creates a draft Amendment Quote. Existing subscription lines appear locked (grayed out for price edits).
4. Add new products or adjust quantities. New products price from the current price book.
5. Calculate the quote. CPQ applies co-termination and proration.
6. Approve and activate the amendment quote. CPQ updates the existing Contract and `SBQQ__Subscription__c` records.

**Why not direct Contract edits:** Editing the Contract or Subscription records directly bypasses CPQ pricing logic, proration calculation, and the approval workflow. This results in mismatched subscription records and broken renewal quotes downstream.

### Pattern: Renewal Quote Generation

**When to use:** Contract is approaching expiration and the account intends to continue service.

**How it works:**
1. Confirm `SBQQ__DefaultRenewalTerm__c` is set on the Contract (months).
2. Click the **Renew** button on the active Contract (or enable Auto Renew in CPQ Settings to trigger this automatically on activation).
3. CPQ creates a Renewal Opportunity and a Renewal Quote, linked via `SBQQ__RenewedContract__c`.
4. All lines are repriced at current price book prices (not contracted prices unless a `SBQQ__ContractedPrice__c` record exists for the account/product).
5. Negotiate and approve the renewal quote as a standard CPQ quote.

**Why not clone the original quote:** Cloning does not set up the `SBQQ__RenewedContract__c` relationship, so the renewed contract lifecycle tracking breaks. Revenue reporting and contract history will be incorrect.

### Pattern: Async Large-Scale Amendment

**When to use:** Contract has 1,000+ subscription lines and synchronous Amend fails or times out.

**How it works:**
1. Use Apex or a scheduled job to call `SBQQ.ContractManipulationAPI.amend(contractId)`.
2. This queues an `AsyncApexJob`. The amendment quote is created asynchronously.
3. Monitor `AsyncApexJob` for the `SBQQ.AmendmentBatchJob` class.
4. Once complete, the amendment quote appears on the Contract's related list.
5. Proceed with standard amendment review and approval.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Fewer than ~200 subscription lines, simple quantity change | Synchronous Amend button | Sufficient for governor limits; no setup overhead |
| 1,000+ subscription lines | Async `SBQQ.ContractManipulationAPI.amend()` | Synchronous processing will hit CPU and SOQL limits |
| List price changed and amendment should reflect new price for existing lines | Do NOT attempt — this is not supported | Existing lines are locked to contracted price; only new lines get current pricing |
| Contract approaching end, auto-renewal enabled | Auto-Renew CPQ Setting | System creates Renewal Opportunity automatically on contract activation |
| Renewal with negotiated pricing different from list | Manual Renew + edit Renewal Quote | Auto-Renew prices at list; negotiate after quote generation |
| Customer wants to remove a product mid-contract | Amendment — set quantity to 0 or remove the line | Direct deletion of `SBQQ__Subscription__c` breaks renewal logic |

---

## Recommended Workflow

1. **Decide which layer you are on, then read the matching file.** Standard `Contract` / `Order` work reads `references/metadata-examples.md` (§1–§6) and Gotchas 6–12. CPQ work reads the Common Patterns section above and Gotchas 1–5. Revenue Cloud or Subscription Management is not this skill — stop and route to `architect/revenue-cloud-architecture` or `architect/subscription-management-architecture`.
2. **Retrieve the live state before changing it.** `sf project retrieve start --metadata "Settings:Contract" --metadata "Settings:Order" --metadata "StandardValueSet:ContractStatus"`. The `StandardValueSet` deploy deactivates every value you omit, so the retrieved file is the only safe starting point. Record `autoCalculateEndDate`, `enableOrders`, `enableReductionOrders` and the full `Status` label list — the Questions table above turns each of these into a build decision.
3. **Confirm prerequisites for the specific task.** For CPQ: `SBQQ__Contracted__c = true` on the Opportunity and at least one Quote Line with `SBQQ__SubscriptionPricing__c` populated, or no `SBQQ__Subscription__c` records are created. For standard contracts: `AccountId`, `StartDate` and `ContractTerm` on every row you intend to load, because `EndDate` cannot be written while auto-calculate is on.
4. **Write the metadata from `references/metadata-examples.md`.** Settings first, then the `ContractStatus` value set, then custom fields, then the validation rule, then the flow — the deploy order in §8 exists because each step depends on the one before it. Do not invent `ContractSettings` elements; the guide documents exactly two.
5. **Lint before you deploy.** `python3 skills/admin/contract-and-renewal-management/scripts/check_contract_and_renewal_management.py --manifest-dir force-app/main/default` — it rejects undocumented settings elements, dependent Order flags with `enableOrders` false, a `ContractStatus` set with no Activated-category value, validation rules naming fields that are not in the manifest, and renewal queries filtered on anything but `EndDate`.
6. **Deploy `--dry-run` first, then for real, then verify.** Run the five checks in `references/metadata-examples.md` §9: settings landed, `EndDate` calculates, the validation rule blocks the right save, no Status label is stranded outside the `Activated` category, and order activation left the line items intact.
7. **Execute the contract work itself and re-verify.** Follow the matching entry in Common Patterns above (Standard Amendment, Renewal Quote Generation, or Async Large-Scale Amendment). Activation is always two DML operations — payload first, `Status` alone second — and there is no undo, so run it against a sandbox copy of the real data before production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `SBQQ__Contracted__c = true` set on Opportunity AND at least one Quote Line has `SBQQ__SubscriptionPricing__c` populated
- [ ] CPQ Settings for Renewal Term, Co-Termination, and Amendment Pricing reviewed and confirmed
- [ ] Amendment quote does not show updated list prices on locked existing subscription lines (expected behavior — verify no custom workaround is breaking this)
- [ ] Co-termination end dates on all amendment lines are consistent and match the earliest subscription end date
- [ ] For large-scale amendments (1000+ lines), async processing is used and `AsyncApexJob` status is monitored
- [ ] Renewal Opportunity and Quote are linked via `SBQQ__RenewedContract__c` (not a cloned quote)
- [ ] `SBQQ__DefaultRenewalTerm__c` is set correctly on the Contract

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **List price changes do not flow into amendment quotes for existing lines** — Once a subscription is created from a contract, the subscription's price is locked. An amendment quote will show the original contracted price for existing lines, even if the price book entry was updated after contract activation. Only net-new lines added in the amendment get current pricing. Practitioners who update price books expecting renewal-price parity on amendments will be surprised.

2. **Co-termination can shorten line terms unexpectedly** — When a contract has lines with staggered start dates, co-termination forces all lines to end on the same date as the earliest-ending line. This means some lines may receive significantly shorter prorated terms than expected. The customer may perceive this as an incorrect charge. Always preview the co-termination date before activating an amendment on a contract with mixed-term lines.

3. **`SBQQ__RenewedContract__c` must be set for contract history tracking** — Manually cloning a quote and relabeling it a "renewal" skips the `SBQQ__RenewedContract__c` linkage. CPQ uses this lookup to chain contract history, calculate contracted price inheritance, and drive revenue recognition rollups. Skipping it silently breaks downstream contract reporting.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Activated Contract with SBQQ__Subscription__c records | Standard Contract record with child Subscription records representing each subscribed product line |
| Amendment Quote | Draft CPQ Quote with locked existing lines and editable new lines; co-termination applied automatically |
| Renewal Opportunity and Quote | Opportunity linked to the expiring Contract via SBQQ__RenewedContract__c; Quote repriced at current price book rates |
| Async Amendment Job Status | AsyncApexJob record for SBQQ.AmendmentBatchJob — monitor for large-scale amendment completion |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable XML — `ContractSettings`, `OrderSettings`, the `ContractStatus` / `OrderStatus` value sets, the activation validation rule, renewal-tracking custom fields, the renewal-reminder flow intent and its SOQL, plus package.xml, deploy order and five verification queries |
| `references/gotchas.md` | Before any activation, migration or settings deploy — 12 behaviours with what happens / when it occurs / how to avoid; 1–5 are CPQ, 6–12 are the standard `Contract` / `Order` graph grounded line-by-line |
| `references/examples.md` | Four worked scenarios: missing subscription records, wrong amendment pricing, wrong renewal term, and a standard-contract activation rejected mid-load — plus the direct-edit anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing AI-generated contract or order metadata, Apex or advice before it reaches an org |
| `references/well-architected.md` | Choosing between auto-renewal and manual renewal, or citing the source behind any claim in this skill (`## Official Sources Used`) |
| `templates/contract-and-renewal-management-template.md` | Starting a working session — records the context gathered, the pattern chosen, and the pricing verification table |
| `scripts/check_contract_and_renewal_management.py` | Before every deploy — `--manifest-dir` lints the settings, value set, validation rule and renewal query against the rules in this skill |

---

## Related Skills

- `admin/cpq-pricing-rules` — Use when contracted prices, price rules, or discount schedules need to be configured to govern amendment and renewal pricing behavior
- `admin/cpq-product-catalog-setup` — Use when subscription-type products are not generating subscriptions during contract creation (usually a product configuration issue upstream of contracts)
- `admin/cpq-approval-workflows` — Use when amendment or renewal quotes need approval routing before activation
- `admin/quotes-and-quote-templates` — Use when the artefact upstream of the contract is a Quote and the question is quote syncing, quote templates, or which quote becomes the contract
- `admin/opportunity-management` — Use when the trigger for contracting is the Opportunity stage model rather than anything on the Contract itself
- `admin/approval-processes` — Use when the `In Approval Process` status needs a real approval behind it, including who can recall and what happens on rejection
- `admin/validation-rules` — Use when the activation guard in `references/metadata-examples.md` §4 needs to grow into a rule set, or when a rule is blocking a data load
- `admin/flow-for-admins` — Use when building the schedule-triggered renewal reminder whose intent and query are specified in `references/metadata-examples.md` §6
- `admin/commerce-order-management` — Use for Salesforce Order Management, order summaries, and the enhanced-commerce order objects rather than the plain `Order` / `OrderItem` pair
- `architect/order-management-architecture` — Use when the question is whether orders belong in Salesforce at all, or how they reconcile with an ERP
- `architect/subscription-management-architecture` — Use when designing the amendment/renewal architecture itself rather than configuring it
- `architect/revenue-cloud-architecture` — Use when the org is on Revenue Cloud and the objects in play are `AssetActionSource`, `SourceQuoteId`, `IsPricingContract` or `HasContractCotermination` rather than CPQ's `SBQQ__*` graph
- `apex/cpq-api-and-automation` — Use when amending or renewing contracts from Apex rather than from Setup
