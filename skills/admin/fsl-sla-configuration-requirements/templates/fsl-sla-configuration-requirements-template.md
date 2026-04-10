# FSL SLA Configuration Requirements — Work Template

Use this template when designing or configuring Salesforce Field Service SLA enforcement using Work Order entitlement processes.

## Scope

**Skill:** `fsl-sla-configuration-requirements`

**Request summary:** (fill in what the user asked for — e.g., "configure 2-hour on-site response SLA for metro territory")

---

## Context Gathered

Answer these before configuring anything:

- **FSL enabled?** Yes / No
- **Entitlement Management enabled?** Yes / No (Setup > Entitlement Settings)
- **Service Territories defined?** Yes / No — list them:
  - Territory 1: _________________ | Operating Hours: _________________
  - Territory 2: _________________ | Operating Hours: _________________
- **Business Hours records available?** Yes / No — list them:
  - BH Record 1: _________________ (windows: _________________)
  - BH Record 2: _________________ (windows: _________________)
- **SLA commitments per tier:**
  | Tier / Territory | Initial Response | On-Site Arrival | Resolution | Measured In |
  |---|---|---|---|---|
  | | | | | Business Hours / Calendar |
  | | | | | Business Hours / Calendar |
- **Work Order completion status values:** _________________ (e.g., "Completed", "Cannot Complete")
- **Existing entitlement processes?** Yes / No — type (Case / Work Order): _________________

---

## Process Model Design

Fill in one row per entitlement process required:

| Process Name | Type | Business Hours Record | Milestones (Name / Time Limit / Recurrence) |
|---|---|---|---|
| | Work Order | | |
| | Work Order | | |

---

## Milestone Action Design

For each milestone, specify:

| Process | Milestone | Warning 1 (% / action) | Warning 2 (% / action) | Violation (action) | Success (action) |
|---|---|---|---|---|---|
| | Initial Response | 50% / email agent | 75% / email manager | 100% / email VP + field update | Stamp SLA_Met__c |
| | On-Site Arrival | | | | |
| | Resolution | | | | |

---

## Automation Plan

- [ ] **Entitlement Assignment Flow** — Record-Triggered Flow on Work Order (create) that reads ServiceTerritoryId and sets EntitlementId
  - Territory → Entitlement mapping: _________________ → _________________
- [ ] **Milestone Completion Flow** — Record-Triggered Flow on Work Order (update) when Status = completion value
  - Completion status values: _________________
  - Logic: Get WorkOrderMilestone where WOId = this WO AND CompletionDate = null → Update CompletionDate = Now

---

## Layout Checklist

- [ ] WorkOrderMilestone related list added to Work Order page layout
- [ ] Columns customized to include: Milestone Name, TargetDate, CompletionDate, IsViolated, Status
- [ ] Entitlements related list added to Work Order page layout
- [ ] Entitlements related list added to Account page layout

---

## Business Hours / Operating Hours Alignment

Confirm alignment per territory before go-live:

| Territory | Operating Hours | Entitlement Process | Process Business Hours | Aligned? |
|---|---|---|---|---|
| | | | | Yes / No |
| | | | | Yes / No |

---

## Test Plan

Before go-live, test in sandbox:

1. Create a Work Order in a sandbox org with a matching entitlement.
2. Set one milestone time limit to 1 minute.
3. Advance Work Order to a completion status before 1 minute elapses.
4. Verify: `WorkOrderMilestone.CompletionDate` is set and success action fired.
5. Repeat with Work Order advanced after 1 minute to verify violation action fires.
6. Verify warning actions fire at 50% and 75% elapsed time.

---

## Review Checklist

Copy from SKILL.md — tick as complete:

- [ ] Entitlement processes are of type Work Order (not Case)
- [ ] Business Hours records assigned at the process level for each SLA tier
- [ ] Business Hours and Operating Hours are aligned per service territory
- [ ] Each process has at least one warning action before violation
- [ ] Flow populates EntitlementId on Work Orders at creation from Service Territory
- [ ] Flow sets CompletionDate on WorkOrderMilestone records on Work Order completion
- [ ] WorkOrderMilestone related list includes TargetDate, CompletionDate, and IsViolated
- [ ] Tested in sandbox with shortened milestone time limit
- [ ] No Case entitlement processes applied to Work Orders

---

## Notes

Record deviations from the standard pattern and the reason:

- _(e.g., "Using Apex instead of Flow for completion because conditional milestone logic based on WOLI completion — see apex/entitlement-apex-hooks skill")_
