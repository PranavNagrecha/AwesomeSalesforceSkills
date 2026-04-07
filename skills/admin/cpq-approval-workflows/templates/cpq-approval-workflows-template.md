# CPQ Approval Workflows — Work Template

Use this template when working on tasks in this area. Fill in each section before starting implementation.

---

## Scope

**Skill:** `cpq-approval-workflows`

**Request summary:** (fill in what the user asked for)

**In scope:**
- [ ] Approval Variable configuration for cross-line aggregation
- [ ] Approval Rule creation with conditions
- [ ] Approval Chain setup for multi-step sequential or parallel routing
- [ ] Smart Approvals configuration on rules
- [ ] Escalation configuration (timeout, escalation user)
- [ ] Permission set assignment for Advanced Approvals users

**Out of scope (route to other skills):**
- Standard Salesforce approval processes on non-CPQ objects → `approval-processes` skill
- CPQ pricing / discount schedule configuration → `cpq-pricing-rules` skill
- Quote template and document design → `cpq-quote-templates` skill

---

## Context Gathered

Fill in before starting work:

- **CPQ Advanced Approvals package installed (`SBAA__`)?** Yes / No / Unknown
- **"CPQ Advanced Approvals" permission set assigned to relevant users?** Yes / No / Unknown
- **Approval threshold type:** Quote-level field only / Line-level aggregation required / Both
- **Approval logic:** Single approver / Sequential chain / Parallel within step
- **Smart Approvals required?** Yes / No
- **Escalation required?** Yes (timeout: ___ days, escalation user: ___) / No
- **Known constraints or existing rules to preserve:**

---

## Approval Matrix Design

Complete this table before creating any records. One row per approval threshold.

| Rule Name | Trigger Field or Variable | Operator | Threshold Value | Approver / Chain | Smart Approvals | Escalation Days |
|---|---|---|---|---|---|---|
| (example) Max Line Discount > 25% | Max Line Discount (variable) | Greater Than | 25 | Sales Manager | Yes | 3 |
| | | | | | | |
| | | | | | | |

---

## Approval Variables Needed

For each threshold that requires aggregation across quote lines:

| Variable Name | Child Object | Field | Aggregation Function | Filter (if any) |
|---|---|---|---|---|
| | `SBQQ__QuoteLine__c` | | Max / Min / Sum / Average | |
| | `SBQQ__QuoteLine__c` | | | |

---

## Approval Chain Design

For each rule that routes to multiple approvers in sequence:

**Chain name:** ______________________

| Step Order | Approver (User or Dynamic Field) | Parallel with Step? |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Line-Level Discount Threshold via Approval Variable (single approver)
- [ ] Sequential Approval Chain for Tiered Authority
- [ ] Smart Approvals for Requote Scenarios
- [ ] Other: ______________________

Why this pattern was chosen:

---

## Checklist

Copy from the SKILL.md review checklist and tick items as you complete them:

- [ ] CPQ Advanced Approvals managed package (`SBAA__`) confirmed installed
- [ ] "CPQ Advanced Approvals" permission set confirmed assigned to all relevant users
- [ ] All `SBAA__ApprovalRule__c` records are Active with at least one `SBAA__ApprovalCondition__c`
- [ ] All `SBAA__ApprovalVariable__c` records reference correct child object, field, and aggregation function
- [ ] Approval Chains have `SBAA__Approver__c` records with explicit step order numbers
- [ ] Smart Approvals enabled on each rule where requote skip logic is desired; approval-relevant fields documented
- [ ] Escalation rules have both `SBAA__EscalationDays__c` and `SBAA__EscalationUser__c` set; `SBAA.EscalateApprovals` scheduled job confirmed active
- [ ] End-to-end approval test passed in sandbox: above-threshold quote triggered approval
- [ ] Below-threshold test passed: no spurious approvals fired
- [ ] Smart Approvals requote test passed (if applicable)
- [ ] Approval workflow design document complete and records match design

---

## Approval-Relevant Fields Registry

List the fields referenced in active approval conditions. These fields trigger re-approval on requotes when Smart Approvals is enabled.

| Object | Field API Name | Referenced in Rule | Last Reviewed |
|---|---|---|---|
| `SBQQ__QuoteLine__c` | `SBQQ__Discount__c` | (rule name) | |
| `SBQQ__Quote__c` | | | |

---

## Test Scenarios

| Scenario | Expected Outcome | Tested | Pass / Fail |
|---|---|---|---|
| Quote with max line discount above threshold | Approval fires; correct approver notified | | |
| Quote with max line discount below threshold | No approval fires | | |
| Quote with max line discount exactly at threshold | (confirm whether > or >= applies) | | |
| Requote: non-relevant field change (Smart Approvals on) | Previous approval carried forward; no re-approval | | |
| Requote: discount field change (Smart Approvals on) | Full re-approval required for all approvers | | |
| Approval not acted on after escalation timeout | Escalation user notified; original approver still able to approve | | |

---

## Notes

Record any deviations from the standard pattern and why. Include any rule interactions, edge cases discovered during testing, or decisions made about threshold values.

---

## Official Sources Consulted

- Salesforce CPQ Advanced Approvals — Advanced Approvals for Salesforce CPQ Managed Package: https://help.salesforce.com/s/articleView?id=sf.cpq_adv_approvals.htm
- Smart Approvals: https://help.salesforce.com/s/articleView?id=sf.cpq_smart_approvals.htm
- Approval Chains: https://help.salesforce.com/s/articleView?id=sf.cpq_approval_chains.htm
- Trailhead — Salesforce CPQ Advanced Approvals for Admins: https://trailhead.salesforce.com/content/learn/modules/salesforce-cpq-advanced-approvals-for-admins
