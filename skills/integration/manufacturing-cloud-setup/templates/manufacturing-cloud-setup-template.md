# Manufacturing Cloud Setup — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `manufacturing-cloud-setup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Manufacturing Cloud license confirmed active (standard objects visible): YES / NO
- Sales Agreement schedule frequency (Monthly / Quarterly / Yearly):
- Term length per typical agreement:
- Order data source for actuals (Order/OrderItem standard / external ERP):
- Rebate program in scope: YES / NO; tier model:
- Channel Revenue Management required (true two-step distribution): YES / NO

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: First-time Sales Agreement setup with ABF activation
- [ ] Pattern 2: Actual-vs-planned variance investigation
- [ ] Pattern 3: Volume-tier rebate program

## Checklist

- [ ] Sales Agreement schedule frequency / term decided before activation
- [ ] `SalesAgreementProductSchedule` rows present after activation
- [ ] `OrderItem.SalesAgreementId` populated by Order ingest path
- [ ] ABF recalc DPE definition activated AND scheduled
- [ ] First ABF recalc run manually executed; `AccountProductForecast` populated
- [ ] Rebate Payout DPE definition activated (if rebates in scope)
- [ ] Channel Revenue Management module enabled ONLY if two-step distribution applies
- [ ] Run-rate variance dashboard built off `AccountProductForecast` (not custom rollup)
- [ ] DPE activation step added to org runbook for sandbox-refresh recovery

## Notes

Record any deviations from the standard pattern and why.
