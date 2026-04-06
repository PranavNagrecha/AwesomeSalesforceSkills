# Entitlements and Milestones — Work Template

Use this template when designing or configuring Salesforce Entitlement Management for an org.

## Scope

**Skill:** `entitlements-and-milestones`

**Request summary:** (fill in what the user asked for — e.g., "configure 3-tier SLA entitlements for Acme Corp with email alerts at 75% and 100% elapsed")

---

## Context Gathered

Answer these questions before starting any configuration:

- **Entitlement Management enabled?** Yes / No — (verify in Setup > Entitlement Settings)
- **Business Hours objects configured?** List names and coverage windows (e.g., "24/7 Platinum", "M–F 8am–5pm Standard")
- **Support tiers in scope:** (e.g., Platinum, Gold, Standard)
- **SLA commitments per tier:**
  | Tier | First Response | Resolution | Coverage |
  |---|---|---|---|
  | | | | |
- **Intake channels creating cases:** Email-to-Case / Web-to-Case / API / UI (mark all that apply)
- **Products & Price Books in use for support contracts?** Yes / No
- **Lightning Experience or Classic?** (affects entitlement template product attachment)
- **Existing entitlement records on accounts?** Yes / No / Partial

---

## Entitlement Process Design

Fill in one block per support tier:

### Tier: _______________

- **Process name:** _______________
- **Version label:** _______________
- **Business hours (process level):** _______________
- **Start condition:** Case Created / Status Change / (other: _______)
- **Exit condition:** Case Closed / (other: _______)

#### Milestones

| Milestone Name | Time Limit | Recurrence Type | BH Override | Warning Actions | Violation Actions | Success Actions |
|---|---|---|---|---|---|---|
| First Response | | No Recurrence | | 50%: email agent; 75%: email agent+manager | 100%: email VP + field update | Stamp First_Response_Met__c |
| Resolution | | No Recurrence | | 50%: email agent; 75%: email agent+manager | 100%: email VP + field update | Stamp Resolution_Met__c |

---

## Entitlement Template Plan (if applicable)

- **Template name:** _______________
- **Process referenced:** _______________
- **Business hours referenced:** _______________
- **Duration (days):** _______________
- **Creation mechanism:** Classic product attachment / Lightning Record-Triggered Flow
- **Flow name (if Lightning):** _______________
- **Flow trigger:** OpportunityLineItem insert (Opportunity.StageName = Closed Won) / Order activation / (other: _______)

---

## Entitlement Lookup Automation

- **Flow name:** _______________
- **Trigger:** Case Before Save (Create)
- **Logic:** Query Entitlement WHERE AccountId = Case.AccountId AND Status = Active, LIMIT 1; set Case.EntitlementId
- **Fallback for no-account cases:** (default entitlement name: _______)

---

## Approach

- Which pattern from SKILL.md applies?
  - [ ] Multi-tier SLA process with progressive warning actions
  - [ ] Entitlement templates for automatic entitlement creation
  - [ ] Independent recurrence for ongoing response SLA
  - [ ] Other: _______________
- Reason for choice: _______________

---

## Review Checklist

- [ ] Entitlement Management is enabled in Setup
- [ ] Business Hours objects are active and correctly scoped (24/7 vs. business hours per tier)
- [ ] One entitlement process created per support tier
- [ ] Each process has at least one warning action per milestone (not only violation actions)
- [ ] Recurrence type confirmed correct for each milestone
- [ ] Entitlement and Milestone Tracker related lists/components added to Case page layouts
- [ ] Before-Save Flow populates Case.EntitlementId on all automated case creation channels
- [ ] Entitlement template creation mechanism confirmed (Flow for Lightning, Classic UI for Classic)
- [ ] Milestone timer behavior tested in sandbox with shortened time limit
- [ ] Process versioning strategy documented for future SLA term changes

---

## Notes

Record any deviations from the standard pattern and the reason:

- _______________
