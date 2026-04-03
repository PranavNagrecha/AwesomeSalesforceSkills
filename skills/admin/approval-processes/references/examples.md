# Examples: Approval Processes

---

## Example: Opportunity Discount Approval

**Requirement:** Any Opportunity with discount above 20% requires Sales Director approval before it can move to `Proposal/Quote`.

**Pattern:**
1. Entry criteria: `Discount_Percent__c > 20`
2. Approver source: `Opportunity.Owner.Manager.Manager`
3. Submission action: lock record, send email alert to approver
4. Final approval action: set `Discount_Approved__c = TRUE`
5. Final rejection action: set Stage back to `Negotiation/Review`

**Why Approval Process fits:** One object, clear approver, clear pending state, clear approve/reject outcomes.

---

## Example: Expense Approval With Amount Bands

**Requirement:** Expense requests under $1,000 go to Manager. $1,000-$10,000 go to Director. Above $10,000 goes to Finance VP after Director approval.

**Pattern:**
- Step 1: Manager approval for all submitted records
- Step 2: Director approval when `Amount__c >= 1000`
- Step 3: Finance VP approval when `Amount__c > 10000`

**Critical design note:** The approver fields must exist and be populated before submission. If `Director__c` is blank, the approval breaks at runtime.

---

## Example: When Standard Approval Process Is the Wrong Tool

**Requirement:** Contract review needs Legal, Security, and Finance responses in parallel, plus SLA timers, rework loops, and different rules by product line.

**Recommendation:** Use Flow plus a custom approval object instead of a standard Approval Process.

**Why:** Standard approval will become fragile because the process needs:
- parallel approvals,
- richer status tracking,
- exception handling,
- and cross-object coordination.
