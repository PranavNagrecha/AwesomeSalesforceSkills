---
name: cpq-approval-workflows
description: "Use this skill when configuring or troubleshooting Salesforce CPQ Advanced Approvals: setting up SBAA__ApprovalRule__c, SBAA__ApprovalVariable__c for cross-line aggregation, SBAA__ApprovalChain__c for ordered approver sequences, escalation timeouts, Smart Approvals for re-quote skip logic, and permission set assignment for the Advanced Approvals managed package. Trigger keywords: CPQ Advanced Approvals, SBAA approval rule, approval variable, approval chain, discount approval, line-level approval, Smart Approvals, requote approval. NOT for standard Salesforce approval processes (use the approval-processes skill), CPQ pricing configuration (use cpq-pricing-rules), or quote template setup."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "set up discount approval workflow in CPQ so quotes above a threshold require manager approval"
  - "approval rule in CPQ not evaluating correctly when discount spans multiple quote lines"
  - "configure Smart Approvals so unchanged lines do not require re-approval on a requote"
  - "approval chain in CPQ to route quote to multiple approvers in a specific sequence"
  - "CPQ approval escalation timeout not triggering after the configured number of days"
  - "which permission sets are required for Advanced Approvals managed package in CPQ"
  - "SBAA ApprovalVariable to aggregate maximum discount across all quote line items"
tags:
  - cpq
  - advanced-approvals
  - sbaa
  - approval-rules
  - approval-chains
  - smart-approvals
  - approval-variables
  - discount-approval
  - managed-package
inputs:
  - "Whether the Salesforce CPQ and CPQ Advanced Approvals managed packages are installed (namespaces SBQQ__ and SBAA__)"
  - "Business approval thresholds: discount percentages, revenue values, or product categories that trigger approval"
  - "Approver hierarchy: single approver, sequential chain, parallel approvers within a step, or group-based routing"
  - "Whether Smart Approvals (skip re-approval for unchanged fields on requotes) should be enabled"
  - "Escalation policy: timeout duration in days per rule, escalation target approver"
  - "Which profiles or roles need the CPQ Advanced Approvals permission set assigned"
outputs:
  - "Configured SBAA__ApprovalRule__c records with conditions referencing quote or quote-line fields"
  - "SBAA__ApprovalVariable__c records for cross-line aggregation (e.g., max discount across all lines)"
  - "SBAA__ApprovalChain__c records defining ordered approver sequences with optional parallel steps"
  - "Smart Approvals configuration on applicable approval rules"
  - "Escalation configuration on each approval rule with timeout period and escalation approver"
  - "Permission set assignment checklist for CPQ Advanced Approvals users"
  - "Approval workflow design document covering triggers, chains, variables, and escalation"
dependencies:
  - cpq-product-catalog-setup
  - cpq-pricing-rules
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# CPQ Approval Workflows

Use this skill when configuring or troubleshooting the CPQ Advanced Approvals managed package (namespace `SBAA__`): creating approval rules that evaluate fields across quote line items using Approval Variables, building sequential or parallel Approval Chains, enabling Smart Approvals to skip re-approval on unchanged requote fields, configuring escalation timeouts, and assigning the required permission sets. This skill does not cover standard Salesforce approval processes or CPQ pricing configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the **CPQ Advanced Approvals managed package** (`SBAA__`) is installed separately from the base Salesforce CPQ package (`SBQQ__`). Both must be present. Check via Setup > Installed Packages.
- Confirm users who submit, approve, and administer approvals have the **"CPQ Advanced Approvals" permission set** assigned — this is a separate permission set from the base "Salesforce CPQ" permission set. Missing this permission set causes silent failures where approval buttons or records do not appear.
- Identify whether the approval trigger must evaluate **quote-level fields** (e.g., total quote discount), **single quote-line fields** (e.g., line discount), or **aggregated values across all lines** (e.g., maximum discount across all line items). Line-level aggregation requires `SBAA__ApprovalVariable__c`, not a direct field reference.
- Understand the most common wrong assumption: **standard Salesforce approval processes cannot evaluate across quote line items**. A standard approval process evaluates a single record; it cannot compute "the maximum discount across all lines." `SBAA__ApprovalVariable__c` is the only mechanism that solves this.
- Identify whether **Smart Approvals** should be enabled. When enabled, a requote that changes only non-approval-relevant fields will not require re-approval; if any approval-relevant field changes, all previous approvers must re-approve.

---

## Core Concepts

### CPQ Advanced Approvals Package and Namespace

CPQ Advanced Approvals is a separate managed package with the namespace `SBAA__`. It extends Salesforce CPQ (`SBQQ__`) and adds objects specifically for quote-level approval workflows. Installing CPQ does not install Advanced Approvals — they require separate installation steps and separate AppExchange listings.

Core objects introduced by the package:

| Object | Purpose |
|---|---|
| `SBAA__ApprovalRule__c` | Defines when an approval is required (conditions, approver, escalation) |
| `SBAA__ApprovalCondition__c` | A single condition on a rule (field, operator, value) |
| `SBAA__ApprovalVariable__c` | Aggregates a value across all quote line items (e.g., max discount) |
| `SBAA__ApprovalChain__c` | Defines a sequential or parallel ordered list of approvers |
| `SBAA__Approver__c` | Represents a single approver step within a chain |

Permission set: **"CPQ Advanced Approvals"** must be assigned to every user who interacts with approvals (submitters, approvers, administrators). This permission set is separate from the CPQ base permission sets.

### Approval Rules and Approval Variables

An `SBAA__ApprovalRule__c` record is the core unit: it defines the threshold condition and the approver to route to when that threshold is met.

**Approval Conditions** (`SBAA__ApprovalCondition__c`) reference a field on the Quote (`SBQQ__Quote__c`) or an Approval Variable. Operators include: equals, not equals, greater than, less than, contains. Multiple conditions on a single rule are ANDed together. OR logic across separate conditions requires separate approval rules.

**Approval Variables** (`SBAA__ApprovalVariable__c`) solve a problem that standard approval processes cannot: computing an aggregated value across all quote line items. For example, a rule that fires when "any single line discount exceeds 30%" requires knowing the maximum discount value across all lines. An Approval Variable is configured to aggregate a specific field on `SBQQ__QuoteLine__c` using a function (Max, Min, Sum, Average) and the result is then available as a field reference in an Approval Condition. Without Approval Variables, cross-line discount approvals cannot be implemented.

**Approver assignment** on a rule can be:
- A specific user (User lookup on `SBAA__ApprovalRule__c`)
- A field on the quote that contains a user ID (dynamic user reference, e.g., the Account Owner)
- Routed through an Approval Chain for sequential or parallel multi-approver scenarios

### Approval Chains

`SBAA__ApprovalChain__c` defines an ordered sequence of approvers. Each step is an `SBAA__Approver__c` record referencing the chain. Steps can be:

- **Sequential**: each approver must approve before the next is notified. This is the default and the most common pattern for escalating approval hierarchies (line manager to VP to CFO).
- **Parallel within a step**: multiple `SBAA__Approver__c` records with the same step number require all to approve before the chain advances.

An approval rule is linked to an approval chain rather than a single user when multi-step approval is required. The chain handles routing; the rule handles the trigger condition.

### Smart Approvals

Smart Approvals is a feature of CPQ Advanced Approvals that avoids requiring full re-approval when a quote is re-submitted after changes. The behavior:

- If the re-submitted quote changes **only non-approval-relevant fields** (e.g., the quote description or expiration date), existing approvals are carried forward and the quote does not go back through the approval process.
- If the re-submitted quote changes **any approval-relevant field** (any field referenced in an active approval condition), **all approvers must re-approve** — even if their specific condition was not affected by the change.

Smart Approvals is enabled per rule. It does not reduce the approval requirement when relevant fields change — it only eliminates unnecessary re-approval cycles for cosmetic changes.

### Escalation

Each `SBAA__ApprovalRule__c` can have an escalation policy: a timeout period (in days) after which, if the approver has not acted, the approval is routed to a designated escalation approver. Escalation is configured directly on the approval rule record via `SBAA__EscalationDays__c` and `SBAA__EscalationUser__c`. Escalation requires the `SBAA.EscalateApprovals` scheduled Apex job to be active in Setup > Scheduled Jobs — without this job, escalation timeouts never fire regardless of the rule configuration.

---

## Common Patterns

### Pattern: Line-Level Discount Threshold via Approval Variable

**When to use:** A quote must be approved when any single line item has a discount exceeding a threshold (e.g., 30%), which requires knowing the maximum discount across all lines.

**How it works:**
1. Create an `SBAA__ApprovalVariable__c` record:
   - Name: `Max Line Discount`
   - Object: `SBQQ__QuoteLine__c`
   - Aggregation Function: `Max`
   - Field: `SBQQ__Discount__c`
2. Create an `SBAA__ApprovalRule__c` record with the designated approver user or lookup field, and Active checked.
3. Create an `SBAA__ApprovalCondition__c` record referencing the rule:
   - Variable: the `Max Line Discount` variable
   - Operator: `Greater Than`
   - Value: `30`
4. Test by creating a CPQ quote with a line at 31% discount and verifying the approval is triggered; test a quote with all lines at 29% and verify no approval is required.

**Why not a standard approval process:** Standard approval processes evaluate a single record. There is no native mechanism to evaluate a field across multiple child records (quote lines) within a standard approval process. `SBAA__ApprovalVariable__c` is the only correct solution for cross-line aggregation.

### Pattern: Sequential Approval Chain for Tiered Authority

**When to use:** Different discount thresholds require different approver levels in sequence — for example, discounts above 20% need manager approval, and discounts above 40% additionally require CFO approval.

**How it works:**
1. Create an `SBAA__ApprovalChain__c` record: `High Discount Chain`.
2. Create `SBAA__Approver__c` records for each step:
   - Step order 1: Sales Manager user reference
   - Step order 2: CFO user reference
3. Create an `SBAA__ApprovalRule__c` with condition `Max Line Discount > 40%` and link it to `High Discount Chain`.
4. Create a second `SBAA__ApprovalRule__c` with condition `Max Line Discount > 20%` and assign the Sales Manager directly (no chain needed for single-approver rules).

**Why not a flat rule per approver:** Without a chain, triggering two rules separately does not enforce ordering — both approvers could be notified simultaneously, which does not match the escalating authority model. Chains enforce the sequential constraint so the CFO is only notified after the Sales Manager approves.

### Pattern: Smart Approvals for Requote Scenarios

**When to use:** Sales reps frequently adjust non-commercial fields on requotes (e.g., quote name, expiration date) and should not be blocked by the full approval cycle for changes that do not affect pricing or discounts.

**How it works:**
1. Enable Smart Approvals on each applicable `SBAA__ApprovalRule__c` using the Smart Approvals checkbox in the rule record.
2. Document which fields are "approval-relevant" (those referenced in conditions). Any change to these fields on a requote forces full re-approval.
3. Communicate to sales reps that changing discount, quantity, or price-impacting fields always triggers re-approval; changing only administrative fields does not.

**Why not disable re-approval entirely:** Skipping re-approval when discount-relevant fields change would allow a rep to obtain approval at 20% discount and then change it to 40% without additional approval. Smart Approvals enforces re-approval exactly when the trigger conditions could be affected.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Approval triggered by a field on the quote (not lines) | `SBAA__ApprovalRule__c` with condition on Quote field | Direct field reference; no variable needed |
| Approval triggered by maximum or total discount across all lines | `SBAA__ApprovalVariable__c` (Max/Sum) + Approval Condition | Standard approvals cannot aggregate across child records |
| Multiple approvers required in a fixed sequence | `SBAA__ApprovalChain__c` with ordered `SBAA__Approver__c` steps | Enforces sequential routing; parallel steps possible within a step number |
| Re-approval required only when pricing fields change on requote | Smart Approvals enabled on each rule | Skips re-approval for non-relevant field changes; still re-approves when conditions could be affected |
| Approver has not responded after N days | Escalation config on `SBAA__ApprovalRule__c` | Routes to escalation user after timeout; requires scheduled job active |
| OR logic across two separate conditions | Two separate Approval Rules each with one condition | Conditions within one rule are ANDed; separate rules cover OR scenarios |
| Standard Salesforce approval process for a CPQ discount approval | Do NOT use — use CPQ Advanced Approvals instead | Standard processes cannot evaluate across quote line items |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify package installation and permission sets.** Confirm `SBAA__` namespace is present under Setup > Installed Packages. Confirm the "CPQ Advanced Approvals" permission set exists and is assigned to all users who will submit or approve quotes. Without this permission set, approval buttons and records will not appear — this is the most common cause of "approvals not working" reports.

2. **Design the approval matrix before configuring records.** Document each approval threshold: the triggering condition (field, operator, value), whether it requires a quote-level field or a line-level aggregation, the approver or approver chain, whether Smart Approvals should be enabled, and the escalation timeout. This design document becomes the canonical reference for all rule records.

3. **Create Approval Variables for any line-level aggregations.** For each threshold that depends on a value aggregated across quote lines (e.g., max discount, total discount amount), create an `SBAA__ApprovalVariable__c` record specifying the child object (`SBQQ__QuoteLine__c`), the field, and the aggregation function. Verify the variable resolves against test quote line data before building rules that reference it.

4. **Create Approval Rules and Conditions.** For each approval threshold, create one `SBAA__ApprovalRule__c` record. Attach `SBAA__ApprovalCondition__c` records referencing either quote fields or Approval Variables from step 3. If multiple approvers are needed in sequence, link the rule to an `SBAA__ApprovalChain__c` rather than a single user. Enable Smart Approvals on each rule where requote skip logic is desired.

5. **Configure Approval Chains for multi-step approvals.** Create `SBAA__ApprovalChain__c` and `SBAA__Approver__c` records for any rules requiring sequential or parallel multi-step routing. Assign step order numbers to enforce sequence; use the same step number for approvers that should act in parallel within a step.

6. **Verify escalation setup.** If escalation is required on any rule, set `SBAA__EscalationDays__c` and `SBAA__EscalationUser__c` on the rule. Then confirm the `SBAA.EscalateApprovals` scheduled Apex job is active in Setup > Scheduled Jobs. Without this job, escalation timeouts never fire.

7. **Test end-to-end in a sandbox.** Create CPQ quotes that cross each threshold and verify the correct approver is notified. Test below-threshold quotes to confirm no spurious approvals fire. Test a requote with Smart Approvals enabled: change only a non-relevant field and confirm approval is carried forward; then change a discount field and confirm re-approval is required. Document test results before promoting to production.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] CPQ Advanced Approvals managed package (`SBAA__`) is installed and version is compatible with the installed CPQ version
- [ ] "CPQ Advanced Approvals" permission set is assigned to all submitters, approvers, and administrators
- [ ] All `SBAA__ApprovalRule__c` records are Active and have at least one `SBAA__ApprovalCondition__c`
- [ ] All `SBAA__ApprovalVariable__c` records reference the correct child object (`SBQQ__QuoteLine__c`), field, and aggregation function
- [ ] Approval Chains have `SBAA__Approver__c` records with explicit step order numbers; no two sequential approvers share the same step number unintentionally
- [ ] Smart Approvals is enabled on each rule where requote skip logic is desired; approval-relevant fields are documented
- [ ] Escalation rules have both `SBAA__EscalationDays__c` and `SBAA__EscalationUser__c` set; `SBAA.EscalateApprovals` scheduled job is active in Setup > Scheduled Jobs
- [ ] End-to-end approval test passed in sandbox: above-threshold quote triggered approval, below-threshold quote did not
- [ ] Smart Approvals requote test passed: non-relevant field change skipped re-approval; discount field change required re-approval
- [ ] Approval workflow design document is complete and all rule records match the documented design

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Standard approval processes cannot aggregate across quote line items** — A standard Salesforce approval process evaluates a single record at submission time. It cannot evaluate a field value across all child `SBQQ__QuoteLine__c` records. `SBAA__ApprovalVariable__c` with a Max/Sum/Min/Average function is the only supported solution for cross-line aggregation logic.

2. **Smart Approvals re-approves all approvers when any relevant field changes** — A common misconception is that Smart Approvals re-approves only the approver whose specific condition was affected by the field change. The actual behavior: if any approval-relevant field changes on a requote, every approver in every rule that previously approved must re-approve. There is no selective re-approval by rule.

3. **Escalation requires the `SBAA.EscalateApprovals` scheduled Apex job** — Setting `SBAA__EscalationDays__c` on a rule does not by itself cause escalation. The escalation is only evaluated when the scheduled job runs. If this job is not scheduled or has been deactivated, no escalations will ever trigger. Always verify the job is active in Setup > Scheduled Jobs when configuring escalation.

4. **The "CPQ Advanced Approvals" permission set is separate from CPQ base permission sets** — Installing CPQ Advanced Approvals creates a new permission set. Users who already have "Salesforce CPQ" or "Salesforce CPQ Admin" permission sets do not automatically receive Advanced Approvals permissions. Forgetting this assignment causes approval buttons to be invisible or approval record access to fail silently with no error message.

5. **All conditions on a single approval rule are ANDed — OR logic requires separate rules** — All `SBAA__ApprovalCondition__c` records on a single `SBAA__ApprovalRule__c` are evaluated with AND logic. If OR logic is required (e.g., trigger approval if discount > 30% OR total revenue > $100K), two separate approval rules must be created, each with its own condition.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `SBAA__ApprovalRule__c` records | Active rules defining each approval threshold, approver, and escalation policy |
| `SBAA__ApprovalCondition__c` records | Individual conditions on each rule referencing quote fields or Approval Variables |
| `SBAA__ApprovalVariable__c` records | Aggregation definitions for cross-line metrics (max discount, sum of revenue, etc.) |
| `SBAA__ApprovalChain__c` + `SBAA__Approver__c` records | Sequential or parallel approver chains for multi-step routing |
| Permission set assignment list | Record of which users have the CPQ Advanced Approvals permission set |
| Approval workflow design document | Design matrix: each rule's threshold, approver, chain, Smart Approvals flag, escalation timeout |
| Completed review checklist | Signed-off checklist confirming all rules, variables, and chains are correctly configured |

---

## Related Skills

- cpq-pricing-rules — Configure the price waterfall and discount mechanisms that approval thresholds evaluate against
- cpq-product-catalog-setup — Set up product bundles and options before approval rules that reference product-level fields
- approval-processes — Use for standard Salesforce approval processes on non-CPQ objects; do not use for cross-line CPQ discount approvals
- quote-to-cash-requirements — Use during requirements gathering to map approval policies to CPQ mechanisms
