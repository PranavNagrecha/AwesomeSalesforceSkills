# Gotchas — CPQ Approval Workflows

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Smart Approvals Re-Approves All Approvers — Not Just Those Whose Conditions Were Affected

**What happens:** When Smart Approvals is enabled and a requote changes any approval-relevant field, every approver across every rule that previously approved must re-approve — not just the approver whose specific condition threshold was crossed by the changed field.

**When it occurs:** A sales rep has a quote approved at 28% max discount (triggering a Sales Manager approval) and 55% (triggering a VP chain approval). The rep updates only the line at 28% to 29%. Because `SBQQ__Discount__c` is an approval-relevant field, the VP — who was involved in a different rule — must also re-approve, even though the 50%+ threshold was not crossed by the change.

**How to avoid:** Document approval-relevant fields clearly for each rule and communicate to reps that any change to a discount field on any line restarts all approval flows, regardless of which specific threshold was affected. Design approval chains with this all-or-nothing re-approval behavior in mind — avoid overloading a single quote with many discrete approval thresholds when possible.

---

## Gotcha 2: Escalation Never Fires Without the `SBAA.EscalateApprovals` Scheduled Apex Job

**What happens:** Setting `SBAA__EscalationDays__c` and `SBAA__EscalationUser__c` on an `SBAA__ApprovalRule__c` record does not by itself cause escalation to happen. The escalation is only evaluated when the `SBAA.EscalateApprovals` scheduled Apex class runs.

**When it occurs:** After a CPQ org refresh, sandbox copy, or org migration, scheduled Apex jobs are often not re-activated. The escalation configuration looks correct in the rule records, but approvals that exceed the timeout period simply sit with the original approver indefinitely. Admins discover this only when a deal is stuck pending approval for weeks past the intended escalation window.

**How to avoid:** After any org refresh or package upgrade, verify the `SBAA.EscalateApprovals` job is present and active in Setup > Scheduled Jobs. If missing, re-schedule it via Setup > Apex Classes > Schedule Apex. Treat this job as a required infrastructure dependency alongside the package itself.

---

## Gotcha 3: The "CPQ Advanced Approvals" Permission Set Must Be Assigned Separately from CPQ Base Permission Sets

**What happens:** Users who have the "Salesforce CPQ" or "Salesforce CPQ Admin" permission sets assigned do not automatically gain access to CPQ Advanced Approvals functionality. The approval-related buttons, record access, and related lists are hidden from users missing the "CPQ Advanced Approvals" permission set, with no error message surfaced.

**When it occurs:** A new admin is onboarded and assigned the CPQ admin permission sets. They cannot see the Advanced Approvals tab, cannot edit approval rules, and cannot see the approval submission button on quote records. They report that "approvals are broken" when in fact the permission set is simply unassigned.

**How to avoid:** Maintain a separate permission set assignment checklist that explicitly includes "CPQ Advanced Approvals" as a line item distinct from the CPQ base sets. When setting up a new user or new org, assign all three: "Salesforce CPQ", "Salesforce CPQ Admin" (for admins), and "CPQ Advanced Approvals".

---

## Gotcha 4: Approval Conditions Within a Single Rule Are Always ANDed — OR Logic Silently Fails

**What happens:** A practitioner adds two `SBAA__ApprovalCondition__c` records to a single rule expecting them to be evaluated with OR logic (trigger approval if condition A OR condition B is true). Instead, both conditions must be true simultaneously for the rule to fire.

**When it occurs:** An admin creates a rule with two conditions: "Max Line Discount > 30%" AND "Quote Total Revenue > $100K". The intent was OR, but the implementation is AND. Quotes with a 35% discount but revenue of $80K do not trigger approval even though the discount threshold was crossed. The approval gap is invisible until a deal closes without required sign-off.

**How to avoid:** Always use separate `SBAA__ApprovalRule__c` records for OR logic. Create one rule per distinct threshold. Both rules can reference the same `SBAA__ApprovalVariable__c` records. Document the intended logic (AND vs. OR) in the approval workflow design document and validate the final rule count against the intended condition matrix.

---

## Gotcha 5: Approval Variables Aggregate Across ALL Quote Lines — Including Deleted or Inactive Lines

**What happens:** `SBAA__ApprovalVariable__c` records aggregate across all `SBQQ__QuoteLine__c` child records. If a quote line is soft-deleted or set to optional but not explicitly excluded by a filter condition, the variable may include that line in its aggregation, causing the approval threshold to fire unexpectedly.

**When it occurs:** A rep adds a highly discounted optional product to the quote to show a comparison, then removes it before submitting. If the line record still exists in the database (CPQ sometimes retains deleted lines until quote recalculation completes), the Max discount variable may resolve to the removed line's discount, triggering approval for a discount no longer present on the final quote.

**How to avoid:** If the approval variable should exclude optional or deleted lines, set a filter on the `SBAA__ApprovalVariable__c` record using `SBAA__FilterField__c` and `SBAA__FilterValue__c` to exclude lines where `SBQQ__Optional__c = true` or the appropriate exclusion field. Test the variable behavior explicitly against quotes containing optional lines and soft-deleted lines before enabling rules in production.
