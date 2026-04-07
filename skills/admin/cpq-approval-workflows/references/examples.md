# Examples — CPQ Approval Workflows

## Example 1: Max Line Discount Approval Using an Approval Variable

**Context:** A manufacturing company uses Salesforce CPQ. Sales reps can discount individual quote lines. The business requires manager approval any time a single line item discount exceeds 25%. A standard Salesforce approval process was previously attempted and failed because it evaluated only the quote header record, not individual line items.

**Problem:** There is no single field on `SBQQ__Quote__c` that reliably reflects the maximum discount applied to any individual line. The quote header has a summary discount field, but reps were applying 30%+ discounts on specific line items while the header average remained below 25%. Standard approval processes did not catch this because they evaluate only the submitted parent record.

**Solution:**

Step 1 — Create the Approval Variable to aggregate across lines:

```
SBAA__ApprovalVariable__c:
  Name:               Max Line Discount
  SBAA__Object__c:    SBQQ__QuoteLine__c
  SBAA__Field__c:     SBQQ__Discount__c
  SBAA__Operator__c:  Max
  (SBAA__FilterField__c left blank — aggregate all lines)
```

Step 2 — Create the Approval Rule:

```
SBAA__ApprovalRule__c:
  Name:              Max Line Discount Over 25 Percent
  SBAA__Approver__c: [Sales Manager user record or dynamic user field on quote]
  SBAA__Active__c:   true
```

Step 3 — Create the Approval Condition referencing the variable:

```
SBAA__ApprovalCondition__c:
  SBAA__Rule__c:      Max Line Discount Over 25 Percent
  SBAA__Variable__c:  Max Line Discount
  SBAA__Operator__c:  Greater Than
  SBAA__Value__c:     25
```

Step 4 — Test by creating a CPQ quote with lines at 20%, 24%, and 26% discount. The variable resolves to 26, which is greater than 25, and the approval fires. Test a quote where the highest line discount is 24%: the variable resolves to 24, which is not greater than 25, and no approval fires.

**Why it works:** The `SBAA__ApprovalVariable__c` runs a `Max` aggregation across all `SBQQ__QuoteLine__c` records on the quote when the approval submission is evaluated. The condition then compares the resolved aggregate against the threshold. This is impossible with a standard approval process because standard processes evaluate only the submitted record, not its children.

---

## Example 2: Sequential Approval Chain for High-Discount Quotes

**Context:** A SaaS company has a two-tier approval policy: quotes with any line discount above 30% require Sales Manager approval; quotes above 50% require both Sales Manager and VP of Sales approval in sequence. The VP should only be notified after the Sales Manager has approved.

**Problem:** Two separate approval rules routing to different approvers independently would notify both simultaneously, violating the sequential requirement. The VP should not be in the approval thread for quotes the Sales Manager is still evaluating.

**Solution:**

Step 1 — Create the shared Approval Variable:

```
SBAA__ApprovalVariable__c:
  Name:               Max Line Discount
  SBAA__Object__c:    SBQQ__QuoteLine__c
  SBAA__Field__c:     SBQQ__Discount__c
  SBAA__Operator__c:  Max
```

Step 2 — Create the 30% single-approver rule (Sales Manager only):

```
SBAA__ApprovalRule__c:
  Name:              Discount 30 to 50 Percent — Sales Manager
  SBAA__Approver__c: [Sales Manager user]
  SBAA__Active__c:   true

SBAA__ApprovalCondition__c:
  Rule:     Discount 30 to 50 Percent — Sales Manager
  Variable: Max Line Discount
  Operator: Greater Than
  Value:    30
```

Step 3 — Create the Approval Chain for quotes above 50%:

```
SBAA__ApprovalChain__c:
  Name: High Discount Manager Then VP

SBAA__Approver__c (step 1):
  SBAA__Chain__c:      High Discount Manager Then VP
  SBAA__Approver__c:   [Sales Manager user]
  SBAA__StepOrder__c:  1

SBAA__Approver__c (step 2):
  SBAA__Chain__c:      High Discount Manager Then VP
  SBAA__Approver__c:   [VP of Sales user]
  SBAA__StepOrder__c:  2
```

Step 4 — Create the 50%+ rule linked to the chain:

```
SBAA__ApprovalRule__c:
  Name:                    Discount Over 50 Percent — Chain
  SBAA__ApprovalChain__c:  High Discount Manager Then VP
  SBAA__Active__c:         true

SBAA__ApprovalCondition__c:
  Rule:     Discount Over 50 Percent — Chain
  Variable: Max Line Discount
  Operator: Greater Than
  Value:    50
```

Step 5 — Test: a quote with 35% max line discount triggers only the Sales Manager rule. A quote with 55% max line discount triggers both rules; the chain holds the VP notification until the Sales Manager approves. A quote with 28% max triggers no rules.

**Why it works:** `SBAA__ApprovalChain__c` enforces sequential routing via the step order on `SBAA__Approver__c` records. The VP (step 2) is held until step 1 is complete. Parallel routing within a step is also possible by assigning the same step order number to multiple `SBAA__Approver__c` records.

---

## Example 3: Smart Approvals to Avoid Redundant Re-Approval on Requotes

**Context:** An enterprise software company's CPQ quotes frequently go through multiple revision cycles. After initial approval, sales reps often update the expiration date or add a note — changes that have no bearing on discounts. Without Smart Approvals, each requote submission restarts the full approval cycle.

**Problem:** Every requote triggers a full re-approval cycle even when only administrative fields were changed, slowing sales velocity and generating unnecessary work for approvers.

**Solution:**

Enable Smart Approvals on each applicable rule by setting the Smart Approvals checkbox on the `SBAA__ApprovalRule__c` record:

```
SBAA__ApprovalRule__c:
  Name:                          Max Line Discount Over 25 Percent
  SBAA__SmartApprovalEnabled__c: true
```

Document the approval-relevant fields for this rule (those referenced in active conditions or variables):
- `SBQQ__Discount__c` on `SBQQ__QuoteLine__c` (via Max Line Discount variable)

Communicate to reps: changing `ExpirationDate`, `SBQQ__Notes__c`, or quote name on a requote will not re-trigger approval. Changing any discount on any line will re-trigger full re-approval from all approvers.

**Why it works:** When a quote is resubmitted, Advanced Approvals checks whether any approval-relevant fields changed since the last approval was granted. If none changed, it carries the previous approval forward without routing. If any relevant field changed, it invalidates all previous approvals and routes again. This eliminates redundant cycles for cosmetic changes while maintaining integrity for pricing changes.

---

## Anti-Pattern: Using a Standard Salesforce Approval Process for Line-Level Discount Approval

**What practitioners do:** Create a standard `ApprovalProcess` on `SBQQ__Quote__c` with entry criteria or a formula field that attempts to capture the maximum line discount — for example, a custom formula field on the quote that uses `MAX()` over a child relationship, or entry criteria with a formula referencing line-level fields.

**What goes wrong:** Salesforce approval process entry criteria do not support aggregate functions over child records. A formula field on the quote attempting to reflect the maximum line discount requires a roll-up summary field, which is not available between `SBQQ__Quote__c` and `SBQQ__QuoteLine__c` when CPQ manages the relationship. The result is that line-level discounts are either not evaluated at all, or evaluated using a stale summary value that does not reflect the current state of all lines.

**Correct approach:** Use `SBAA__ApprovalVariable__c` with `Operator = Max` targeting `SBQQ__Discount__c` on `SBQQ__QuoteLine__c`. This is the purpose-built mechanism for cross-line aggregation and is the only approach that correctly evaluates all line items in real time during approval submission.
