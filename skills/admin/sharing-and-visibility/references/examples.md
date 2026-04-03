# Examples: Sharing and Visibility

---

## Example: Private Case Model With Cross-Functional Read Access

**Requirement:** Cases should be visible only to the case owner, their management chain, and a QA team that audits all high-severity cases.

**Design:**
- OWD: `Private`
- Role hierarchy: service managers see their team's Cases
- Criteria-based sharing rule: `Priority = High` shared read-only to public group `Case_QA_Auditors`

**Why this works:** Baseline access stays restrictive. The QA team gets only the subset it needs.

---

## Example: Owner-Based Rule for Sales-to-Finance Handoff

**Requirement:** Finance needs read access to Opportunities owned by the Sales Operations role.

**Design:**
- OWD: `Private`
- Owner-based sharing rule:
  - Owned by: role `Sales Operations`
  - Shared with: public group `Finance Review Team`
  - Access: `Read Only`

**Why this works:** The access pattern follows ownership, so owner-based sharing is simpler than criteria logic.

---

## Example: Manual Sharing Is the Wrong Permanent Fix

**Scenario:** Service managers keep asking admins to manually share escalated Cases with a legal team.

**Observed pattern:** 20-30 manual shares per week for the same group.

**Recommendation:** Replace manual shares with a criteria-based rule such as:

```text
If Case.RecordType = "Escalation"
AND Legal_Review_Required__c = TRUE
share with public group `Legal_Case_Reviewers`
```

If the same "exception" happens weekly, it is not an exception.
