# FSL Scheduling Optimization Design — Work Template

Use this template when designing, configuring, or troubleshooting the Field Service Lightning Optimizer.

## Scope

**Skill:** `fsl-scheduling-optimization-design`

**Request summary:** (fill in what the user or project needs)

---

## Context Gathered

Record answers to the Before Starting questions before proceeding.

| Question | Answer |
|---|---|
| FSL Optimizer license confirmed active? | ☐ Yes / ☐ No / ☐ Unknown |
| Current optimization type in use | Global / In-Day / Resource Schedule / None |
| Geographic territory profile | Rural / Suburban / Urban / Mixed |
| Travel mode currently configured | Aerial (default) / Street-Level Routing (add-on) |
| Predictive traffic needed? | ☐ Yes / ☐ No |
| Scheduling decision context | Pre-day bulk planning / Same-day disruption / Single resource |
| % of appointments with null DueDate | (run SOQL report — see data quality check below) |
| % of appointments with null Priority | (run SOQL report) |

---

## Data Quality Pre-Check

Run this SOQL before any optimizer configuration or troubleshooting:

```soql
SELECT Id, Subject, DueDate, Priority, Status, ServiceTerritoryId
FROM ServiceAppointment
WHERE Status NOT IN ('Completed', 'Cancelled', 'Cannot Complete')
  AND (DueDate = null OR Priority = null)
ORDER BY CreatedDate DESC
```

**Result count:** ___________

If result count > 0: resolve data quality issues before proceeding with optimizer configuration.

---

## Optimization Type Selection

| Decision Factor | Your Situation |
|---|---|
| Planning horizon | Same-day / Next day / 2–7 days |
| When decisions are made | Pre-shift / During shift / Ad-hoc |
| Who triggers optimization | Automated (Flow/API) / Dispatcher manual / Scheduled job |
| Should existing confirmed appointments be moved? | ☐ Yes (Global OK) / ☐ No (use In-Day or lock appointments) |

**Selected optimization type:** ___________________________

**Justification:** (explain why this type fits the use case)

---

## Priority Tier Model

Define the priority tiers for this org before configuring the optimizer:

| Priority Value | Score (approx.) | Use Case | SLA Response Window |
|---|---|---|---|
| 1 | ~25,500 pts | Emergency / SLA breach imminent | < 4 hours |
| 2 | | Urgent | < 8 hours |
| 3 | | High — next business day | 1 business day |
| 4 | | Standard | 2–5 business days |
| 5–7 | | Routine maintenance | Flexible window |
| 8–10 | | Lowest urgency | Background / batch |

**How Priority is set on appointment creation:** (Flow / Apex / default value / manual)

---

## Travel Mode Decision

| Factor | Assessment |
|---|---|
| Territory density | Rural / Suburban / Urban |
| Road deviation from straight-line | Low / High |
| Traffic variation during workday | Minimal / Significant |
| Street-Level Routing license available? | ☐ Yes / ☐ No |

**Selected travel mode:** Aerial / Street-Level Routing

**Justification:**

---

## Optimization Run Configuration

| Setting | Value |
|---|---|
| Optimization job name | |
| Scheduling policy assigned | |
| Time horizon | ___ days |
| Trigger mechanism | Scheduled job / Flow invocable / Manual dispatcher |
| Trigger time (if scheduled) | |
| Territory scope | All territories / Specific territory list |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Weekly Global Optimization at Start of Day
- [ ] In-Day Optimization Triggered by Cancellation Event
- [ ] Resource Schedule Optimization for Single Technician Resequencing
- [ ] Other: ___________________________

**Justification:**

---

## Checklist

- [ ] FSL Optimizer license confirmed active
- [ ] Data quality pre-check run — null DueDate and Priority count is 0 or remediation plan is in place
- [ ] Correct optimization type selected and documented with justification
- [ ] Travel mode selected (Aerial or Street-Level Routing) with justification documented
- [ ] Scheduling policy assigned to optimizer run has Service Resource Availability work rule
- [ ] Time horizon set appropriately for optimization type
- [ ] Priority tier model defined — Priority 1 reserved for genuine emergencies
- [ ] Optimization run tested in sandbox with representative data
- [ ] Post-run unscheduled appointment rate reviewed and acceptable (<5% target)
- [ ] Optimizer job logs checked for errors after first production run
- [ ] Dispatcher runbook created for reviewing and confirming optimizer output

---

## Notes

Record any deviations from standard patterns and why:
