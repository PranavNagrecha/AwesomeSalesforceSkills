---
name: quote-to-cash-requirements
description: "Use when gathering, designing, or validating the end-to-end quote-to-cash process on standard Salesforce: Opportunity to Quote (with line items) to Synced Quote to Approval Process to Quote PDF to Order creation. Trigger keywords: quote approval, discount policy, quote PDF limits, order from quote, quote sync, quote template. NOT for CPQ/Revenue Cloud pricing rules, discount schedules, or guided selling — use CPQ skills for those."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - User Experience
triggers:
  - "How do I set up an approval process that fires when a rep gives a discount over 20%?"
  - "We need to generate a quote PDF and send it to the customer — what are the limits?"
  - "How do I convert an approved quote into an order automatically?"
  - "Only one quote should be synced to the opportunity at a time — how does that work?"
  - "We need a discount approval workflow before a quote can be marked Accepted"
  - "What are the standard quote-to-cash stages and handoffs in Salesforce without CPQ?"
tags:
  - quote
  - quote-to-cash
  - approval-process
  - discount-policy
  - order
  - quote-template
  - synced-quote
  - sales-cloud
  - opportunity
inputs:
  - "Current opportunity and quote object usage (fields in use, existing statuses)"
  - "Discount thresholds that require manager or director approval"
  - "Quote document output requirements (logo, line item table, terms)"
  - "Whether orders need to be created from accepted quotes"
  - "Approval chain: who approves at each discount tier"
outputs:
  - "Quote-to-cash process map (stages, owners, handoffs)"
  - "Approval process design for discount/amount thresholds"
  - "Quote Template configuration guidance"
  - "Order creation requirements document"
  - "Gap list vs. CPQ: when standard objects are insufficient"
dependencies:
  - products-and-pricebooks
  - approval-processes
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Quote-to-Cash Requirements

Use this skill when mapping, designing, or auditing the standard Salesforce quote-to-cash process — from Opportunity through Quote, approval, PDF generation, and Order handoff. It is grounded in standard Sales Cloud objects and does not cover CPQ/Revenue Cloud.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org uses **standard Quotes** (enabled in Setup > Quotes Settings) or CPQ/Revenue Cloud. If CPQ is in play, stop here and route to CPQ skills.
- Identify the **discount approval thresholds** — typically expressed as a percentage off list price, a total deal amount, or both.
- Determine whether **Orders** need to be auto-created or manually created from accepted quotes, and whether Order Products need to carry over from Quote Line Items.
- Check if the org uses **multi-currency** — this affects Pricebook assignment on Quotes and Quote Line Items.
- Confirm the **Quote Template** requirements: logo, legal footer, line item grouping, bundled products display, and any per-customer branding variations.

---

## Core Concepts

### 1. The Standard Quote-to-Cash Object Chain

The canonical flow on standard Sales Cloud objects is:

```
Opportunity -> Quote (+ QuoteLineItem) -> Synced Quote -> Approval Process -> Quote Status = Accepted -> Order (+ OrderItem)
```

Key platform rules:
- A single Opportunity can have **multiple Quotes**, but only **one Synced Quote** at a time. Syncing a Quote copies the Quote's line items to the Opportunity's Products (OpportunityLineItem records). Syncing a second Quote removes the first sync.
- Quote Line Items are linked to PricebookEntry records — the Quote must reference the same Pricebook as the Opportunity.
- When a Quote Status is set to **Accepted**, you can manually create an Order from the Quote (via the Create Order button), which generates an Order with OrderItem records mirroring the QuoteLineItems. This is not automatic by default — a Flow or Apex trigger is needed to automate it.
- Orders generated from Quotes carry a reference to `QuoteId` on the Order record.

### 2. Approval Processes on Quotes

Salesforce Approval Processes can be triggered on the Quote object with entry criteria based on:
- `Discount` field (Quote-level overall discount %)
- `TotalPrice` or `GrandTotal` field
- Custom formula fields combining both

Critical constraints:
- The Quote record is **locked** during approval. Reps cannot edit line items while approval is pending — this is a common business-process pain point that must be called out in requirements.
- Only **one active approval process** can run on a record at a time. If multi-tier approvals (manager then director) are needed, configure them as **steps within a single process**, not separate processes.
- Email alerts used in approval steps must reference Quote-related merge fields (e.g., `{!Quote.Name}`, `{!Quote.GrandTotal}`) — these are not available via the standard Opportunity email templates.
- Approval entry criteria are evaluated **at submission time**; if the Quote is edited post-submission (after recall), criteria are re-evaluated on the next submission.

### 3. Quote Templates and PDF Generation

Quote Templates define the layout of the generated PDF document. Platform limits:
- Maximum **30 pages** per generated Quote PDF.
- Maximum **100 line items** rendered in a Quote Template.
- Templates are built in the Quote Template editor (not Lightning App Builder). They use a proprietary section/field layout — not standard page layouts.
- Rich-text fields on Quote are not supported in templates. Use plain-text custom fields for dynamic legal language.
- Quote Templates support conditional sections but logic is limited to show/hide based on field values — no scripting.

### 4. Order Creation and Handoff

Orders created from Quotes:
- Must have an Account and a Price Book (inherited from the Quote).
- OrderItems are created from QuoteLineItems — unit price, quantity, and product references carry over.
- The Order `Status` field starts at "Draft" by default. Activating the Order (Status = Activated) locks it — line items cannot be changed after activation.
- Contracts linked to Orders are a separate optional step in the lead-to-cash chain; Quote acceptance does not auto-create a Contract.

---

## Common Patterns

### Pattern: Tiered Discount Approval (Single Approval Process, Multiple Steps)

**When to use:** Business requires manager approval above 10% discount and director approval above 25% discount.

**How it works:**
1. Create one Approval Process on the Quote object.
2. Set entry criteria: `Quote.Discount >= 10` (or formula combining discount + deal size).
3. Step 1: Route to `Quote.Opportunity.Owner.Manager` with step-entry criteria `Quote.Discount < 25`. Mark step as "Go to Next Step" on approval.
4. Step 2: Route to a named Director user (or queue) with no additional step-entry criteria (catches >= 25%).
5. On Final Approval action: set `Quote.Status = Approved`.
6. On Rejection action: set `Quote.Status = Denied` and send email alert to rep.

**Why not two separate processes:** Salesforce only processes one approval at a time per record. A second process would not trigger if the first is already satisfied or would cause unpredictable behavior.

### Pattern: Auto-Create Order on Quote Acceptance via Flow

**When to use:** Business wants an Order automatically generated when a rep sets Quote Status to Accepted — without requiring a manual button click.

**How it works:**
1. Create a Record-Triggered Flow on Quote, fired on Update, with entry criteria `Status changed to Accepted`.
2. Use a Create Records element to create an Order: set `AccountId`, `Pricebook2Id`, `QuoteId`, `Status = Draft`, `EffectiveDate = TODAY()`.
3. Loop over QuoteLineItems related to the Quote and create OrderItem records for each: `OrderId`, `Product2Id`, `UnitPrice`, `Quantity`, `PricebookEntryId`.
4. Optionally set Quote `ContractId` if contract generation is also required.

**Why not a Process Builder trigger:** Process Builder is legacy. Flow is the current standard and gives more control over the OrderItem loop.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single discount threshold for approval | One-step Approval Process on Quote with entry criteria on Discount field | Simplest; native; no code required |
| Two or more discount tiers require different approvers | Single Approval Process with multiple steps, each with step-entry criteria | Salesforce only runs one approval process at a time on a record |
| Auto-create Order on quote acceptance | Record-Triggered Flow on Quote (Status = Accepted) | Approval Process Final Actions cannot create related child records; Flow can |
| Quote PDF needs custom branding per customer segment | Multiple Quote Templates assigned by Record Type or Flow logic | Quote Templates are per-template; not dynamic — use multiple templates |
| More than 100 line items on a single quote | Split quote into multiple quotes or upgrade to CPQ | Standard Quote Template limit is 100 line items rendered |
| Bundle products with configuration logic | Evaluate CPQ/Revenue Cloud | Standard Quote Line Items have no bundle hierarchy or attribute logic |
| Multi-currency quotes | Ensure Quote references the correct Pricebook with currency-specific PricebookEntries | Quote Line Items inherit currency from the Quote Pricebook — mismatch causes errors |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm standard vs. CPQ scope** — Verify Quotes are enabled in Setup > Quotes Settings and that the org is not running CPQ/Revenue Cloud. If CPQ is active, route to the CPQ skill.
2. **Map the approval policy** — Document discount thresholds, approver hierarchy, and what happens on rejection (Status change, rep notification). Confirm whether a single-level or multi-level approval is needed.
3. **Assess Quote Template requirements** — Gather layout specs: logo placement, line item grouping, conditional sections, legal text. Flag if more than 100 products are expected on a single quote (hard platform limit).
4. **Design the object and field model** — Identify custom fields needed on Quote or QuoteLineItem (e.g., custom discount %, override justification). Confirm Pricebook alignment with Opportunity.
5. **Build the Approval Process** — Configure entry criteria, steps, approver sources, lock behavior, and final approval/rejection actions. Test with a sandbox quote at each discount tier.
6. **Implement Order creation automation** — Build a Record-Triggered Flow on Quote to auto-create Order and OrderItems on Status = Accepted. Validate that OrderItem PricebookEntry references are correct.
7. **Validate end-to-end in sandbox** — Walk through: create Opportunity -> add Products -> create Quote -> sync Quote -> submit for approval -> approve -> verify Order created -> preview PDF against template limits.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Quotes feature is enabled in Setup (Setup > Quotes Settings > Enable Quotes)
- [ ] Approval process entry criteria match documented discount/amount thresholds
- [ ] Record lock behavior during approval has been communicated to business stakeholders
- [ ] Quote Template has been tested with the maximum expected line item count (confirm < 100)
- [ ] Order creation (manual or automated) tested end-to-end in sandbox
- [ ] Multi-currency Pricebook entries are consistent with Quote currency if multi-currency is enabled
- [ ] Approval rejection path sets Quote Status and notifies rep via email alert
- [ ] Flow for Order creation handles zero-quantity or $0 line items without errors

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Syncing a second Quote removes the first sync** — When you sync a new Quote to an Opportunity, all Opportunity Products (OpportunityLineItem records) are replaced with the new Quote's line items. Any Products manually added to the Opportunity are lost. This surprises reps who juggle multiple quote versions.
2. **Quote is locked during approval including line items** — The entire Quote record and its related QuoteLineItems are locked when an approval is pending. Reps cannot add, remove, or reprice products until the quote is recalled or a final decision is made.
3. **Approval Process Final Actions cannot create child records** — Final Approval/Rejection actions on an Approval Process support field updates, email alerts, tasks, and outbound messages — but not record creation. A Flow triggered by the resulting field update is required for Order creation.
4. **Quote Template PDF limit: 30 pages and 100 line items** — These are hard platform limits. Quotes exceeding 100 line items will silently truncate the PDF. There is no warning to the user.
5. **Quote currency is set at creation and cannot be changed** — The currency on a Quote is locked at creation time. If the Opportunity currency or Pricebook changes, the Quote must be deleted and recreated.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Quote-to-cash process map | Swimlane diagram showing stages, owners, object transitions, and approval handoffs |
| Approval process design document | Entry criteria, step definitions, approver sources, lock behavior, final actions |
| Quote Template specification | Layout sections, fields, conditional blocks, line item grouping, PDF output expectations |
| Order creation requirements | Trigger condition, field mapping from Quote to Order and QuoteLineItem to OrderItem |
| CPQ gap analysis | List of requirements that cannot be met by standard Quote objects, requiring CPQ evaluation |

---

## Related Skills

- `products-and-pricebooks` — Required prerequisite: products and Pricebook entries must exist before Quote Line Items can be added.
- `approval-processes` — Detailed approval process design and troubleshooting patterns.
- `opportunity-management` — Opportunity stage gates and how they interact with quote sync status.
- `architect/cpq-vs-standard-products-decision` — Use when line item volume, bundle logic, or pricing complexity exceeds standard Quote object capabilities.

---

## Official Sources Used

- Salesforce Help — Quotes Overview: https://help.salesforce.com/s/articleView?id=sf.quotes_overview.htm
- Salesforce Help — Syncing Quotes with Opportunities: https://help.salesforce.com/s/articleView?id=sf.quotes_syncing_overview.htm
- Trailhead — Negotiate Enterprise Quotes: https://trailhead.salesforce.com/content/learn/modules/sales-cloud-platform-quick-look/negotiate-enterprise-quotes
- Trailhead — Build a Discount Approval Process: https://trailhead.salesforce.com/content/learn/projects/build-a-discount-approval-process
- Salesforce Help — Create Orders from Quotes: https://help.salesforce.com/s/articleView?id=sf.quotes_create_orders.htm
- Salesforce Help — Quote Template Limits: https://help.salesforce.com/s/articleView?id=sf.quotes_doc_limits.htm
- Object Reference — Quote: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_quote.htm
- Object Reference — Order: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_order.htm
