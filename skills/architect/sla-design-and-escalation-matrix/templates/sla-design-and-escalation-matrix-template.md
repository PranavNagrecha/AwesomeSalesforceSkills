# SLA Design and Escalation Matrix — Work Template

Use this template when designing SLA tiers, milestone thresholds, and escalation actions for a Salesforce Service Cloud implementation.

---

## Scope

**Skill:** `sla-design-and-escalation-matrix`

**Request summary:** (fill in what the user asked for — e.g., "Design SLA tiers for a 3-tier B2B support model")

**Date:** (fill in)

**Reviewed by:** (fill in — support ops lead, account management, etc.)

---

## Context Gathered

- **Support tiers and customer segments:** (e.g., Enterprise = accounts > $100K ARR; Professional = accounts $10K–$100K ARR; Basic = all others)
- **Case priority levels in use:** (e.g., P1 = Service Down, P2 = Major Impairment, P3 = Minor Issue, P4 = Question)
- **Operating regions and time zones:** (e.g., US West Coast, EMEA, APAC)
- **24/7 tiers (if any):** (e.g., Enterprise P1 is 24/7; all other tiers are business hours only)
- **Known constraints:** (e.g., 3 entitlement processes maximum due to org cleanup, or specific notification user IDs)

---

## Section 1: Tier Definition Table

| Tier | Priority | First Response Target | Resolution Target | Business Hours Record |
|------|----------|-----------------------|-------------------|-----------------------|
| (e.g., Enterprise) | P1 | (e.g., 1 hour) | (e.g., 4 hours) | (e.g., Enterprise 24/5) |
| Enterprise | P2 | | | |
| Enterprise | P3 | | | |
| Enterprise | P4 | | | |
| (e.g., Professional) | P1 | | | |
| Professional | P2 | | | |
| Professional | P3 | | | |
| Professional | P4 | | | |
| (e.g., Basic) | P1 | | | |
| Basic | P2 | | | |
| Basic | P3 | | | |
| Basic | P4 | | | |

**Notes:**
- All targets are in business hours unless noted as calendar hours.
- Add or remove rows to match the actual tier and priority structure.

---

## Section 2: Escalation Matrix

For each tier and priority level, define the notification target and automated action at each milestone threshold.

### Tier: [Tier Name] — Priority: [Priority Level]

| Threshold | Elapsed Time at Threshold | Notification Target | Automated Action |
|-----------|--------------------------|---------------------|------------------|
| 50% | (calculated: e.g., 30 min for 1h target) | (e.g., Assigned Agent) | (e.g., Email Alert: "50% warning") |
| 75% | (calculated) | (e.g., Team Lead) | (e.g., Email Alert: "75% warning") |
| 90% | (calculated) | (e.g., Support Manager) | (e.g., Email Alert + Task: "Pre-breach") |
| 100% | (target time — this is breach) | (e.g., VP Support + Manager) | (e.g., Email Alert + Field Update: Violated = true) |

Duplicate this sub-table for each tier-priority combination.

---

## Section 3: Business Hours Mapping Table

List every object that must reference a Business Hours record. Both the entitlement process AND each escalation rule entry must be mapped.

| Object Type | Object Name | Business Hours Record | Notes |
|-------------|-------------|----------------------|-------|
| Entitlement Process | (e.g., Enterprise SLA) | (e.g., Enterprise 24/5) | |
| Entitlement Process | (e.g., Professional SLA) | (e.g., Professional M-F 8-6) | |
| Entitlement Process | (e.g., Basic SLA) | (e.g., Basic M-F 9-5) | |
| Escalation Rule Entry | (e.g., Enterprise P1 Entry) | (e.g., Enterprise 24/5) | Must match entitlement process |
| Escalation Rule Entry | (e.g., Professional P1 Entry) | (e.g., Professional M-F 8-6) | Must match entitlement process |
| Escalation Rule Entry | (e.g., Basic P1 Entry) | (e.g., Basic M-F 9-5) | Must match entitlement process |

**Verification step:** For each Business Hours record name listed above, verify in Setup > Business Hours that the record exists, has the correct days and times, and is NOT the "Default" record (unless explicitly verified as correctly configured).

---

## Section 4: Milestone Configuration Plan

For each milestone to be created in Salesforce, document the following:

| Milestone Name | Entitlement Process | Entry Criteria | Time Target | Actions at 50% | Actions at 75% | Actions at 90% | Actions at 100% |
|----------------|---------------------|----------------|-------------|----------------|----------------|----------------|-----------------|
| (e.g., First Response - P1) | (e.g., Enterprise SLA) | (e.g., Priority = P1) | (e.g., 60 min) | Email: Agent | Email: Lead | Email: Manager + Task | Email: VP + Field Update |
| (e.g., Resolution - P1) | (e.g., Enterprise SLA) | (e.g., Priority = P1) | (e.g., 240 min) | Email: Agent | Email: Lead | Email: Manager + Task | Email: VP + Field Update |

Repeat for every tier-priority combination. Remember: one milestone per entry-criteria set (no OR conditions).

---

## Section 5: Platform Limits Validation

| Limit | Platform Maximum | Design Total | Status |
|-------|-----------------|--------------|--------|
| Entitlement Processes | 2,000 | (fill in) | Pass / Fail |
| Milestones per Entitlement Process | 10 | (fill in per process) | Pass / Fail |
| Milestone Actions per Milestone | 40 total across all action types | (fill in) | Pass / Fail |
| Escalation Rule Entries | 3,000 | (fill in) | Pass / Fail |

---

## Section 6: Review Checklist

- [ ] Tier definition table reviewed and signed off by support operations lead
- [ ] All SLA time targets cross-referenced with customer contract or support policy document
- [ ] Escalation matrix reviewed with support managers — notification targets are current users or queues (not individuals who may leave)
- [ ] Business hours mapping table complete — every entitlement process AND every escalation rule entry has a named Business Hours record assigned
- [ ] "Default" Business Hours record has been inspected in Setup — its actual hours are documented here: ____________
- [ ] Platform limits validation shows all designs are within limits
- [ ] No milestone entry criteria use OR conditions (each condition set = one milestone)
- [ ] For SLA targets under 60 minutes: custom automation approach is documented or stakeholders accept timing variance

---

## Notes and Deviations

(Record any deviations from the standard pattern and the reason — e.g., "Tier 3 Basic P1 uses calendar hours by stakeholder request because the team operates 24/7 during peak season.")
