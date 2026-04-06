# Service Metrics Data Model — Work Template

Use this template when designing or implementing service KPI reporting in a Salesforce Service Cloud org.

## Scope

**Skill:** `service-metrics-data-model`

**Request summary:** (fill in what the user asked for — e.g., "build an SLA compliance dashboard," "add MTTR metric to Case," "troubleshoot missing CaseMilestone records")

---

## Context Gathered

Answer these questions before proceeding. They determine which approach applies.

- **Entitlements enabled?** Yes / No (Setup > Entitlement Settings)
- **Entitlement Process active and assigned to Cases?** Yes / No
- **Business Hours configured?** Yes / No — if Yes, record the name:
- **Business Hours assigned to the relevant Entitlement?** Yes / No
- **Which milestones are active?** (e.g., First Response, Resolution — list names exactly as configured)
- **Time horizon for MTTR:** Calendar time (simpler) / Business hours (contractually accurate)
- **Reporting tool:** Native Salesforce reports / External BI (Tableau, Power BI, etc.)
- **Data volume:** Estimated cases per month × milestones per case = expected CaseMilestone rows/month

---

## Metric-to-Field Mapping

| Metric | Source Object | Source Field(s) | Derivation |
|--------|--------------|-----------------|------------|
| MTTR (calendar) | Case | `CreatedDate`, `ClosedDate`, `IsClosed` | Formula: `IF(IsClosed, (ClosedDate - CreatedDate) * 24 * 60, NULL)` |
| MTTR (business hours) | Case | `CreatedDate`, `ClosedDate`, `IsClosed`, `Entitlement.BusinessHoursId` | Apex: `BusinessHours.diff(bhId, CreatedDate, ClosedDate)` → `MTTR_BH_Mins__c` |
| First Response Elapsed Time | CaseMilestone | `ElapsedTimeInMins` | Filter: `MilestoneType.Name = 'First Response'` |
| Resolution Elapsed Time | CaseMilestone | `ElapsedTimeInMins` | Filter: `MilestoneType.Name = 'Resolution'` |
| SLA Compliance (per milestone) | CaseMilestone | `IsCompleted`, `IsViolated` | Compliant: `IsCompleted=true AND IsViolated=false` |
| SLA Miss (late completion) | CaseMilestone | `IsCompleted`, `IsViolated` | Late: `IsCompleted=true AND IsViolated=true` |
| Open Overdue Milestone | CaseMilestone | `IsCompleted`, `IsViolated` | Overdue: `IsCompleted=false AND IsViolated=true` |

---

## MTTR Approach

- [ ] Calendar MTTR — create Formula Number field on Case: `MTTR_Calendar_Mins__c`
  - Formula: `IF(IsClosed, (ClosedDate - CreatedDate) * 24 * 60, NULL)`
  - Field type: Number (10, 2)

- [ ] Business-Hours MTTR — create custom Number field + Apex trigger
  - Custom field: `MTTR_BH_Mins__c` (Number, 10, 2) on Case
  - Trigger: after update, when `IsClosed` transitions to `true`
  - `BusinessHours.diff(case.Entitlement.BusinessHoursId ?? defaultBhId, case.CreatedDate, case.ClosedDate)`
  - Store result in `MTTR_BH_Mins__c`

**Chosen approach:**

**BusinessHoursId source:** (entitlement-derived / org default / hardcoded — state which and why)

---

## SLA Compliance Query Design

```sql
-- Template: SLA compliance by milestone type and month
SELECT
    MilestoneType.Name                                        milestone_type,
    CALENDAR_MONTH(Case.ClosedDate)                           closed_month,
    COUNT(Id)                                                 total_terminal,
    SUM(CASE WHEN IsViolated = false AND IsCompleted = true
             THEN 1 ELSE 0 END)                               compliant_count,
    SUM(CASE WHEN IsViolated = true THEN 1 ELSE 0 END)        violated_count,
    AVG(ElapsedTimeInMins)                                    avg_elapsed_mins
FROM CaseMilestone
WHERE (IsCompleted = true OR IsViolated = true)
  AND Case.ClosedDate >= [DATE_RANGE]
GROUP BY MilestoneType.Name, CALENDAR_MONTH(Case.ClosedDate)
ORDER BY CALENDAR_MONTH(Case.ClosedDate), MilestoneType.Name
```

**Adjustments needed for this org:** (e.g., additional grouping by Queue, Entitlement tier, Case priority)

---

## Custom Report Type Plan

| CRT Name | Primary Object | Related Objects | Join Type | Purpose |
|----------|---------------|-----------------|-----------|---------|
| `CaseMilestone with Case and MilestoneType` | CaseMilestone | Case, MilestoneType | Inner join | SLA compliance reporting |
| (add as needed) | | | | |

- [ ] CRT status set to "Deployed" before testing

---

## Checklist

Copy from SKILL.md review checklist and tick items as complete.

- [ ] Entitlements enabled and at least one active Entitlement Process confirmed
- [ ] CaseMilestone records exist for a sample of test cases
- [ ] Business Hours correctly assigned to the Entitlement Process
- [ ] MTTR formula or Apex trigger tested against closed cases with known timestamps
- [ ] `BusinessHours.diff()` called with the correct BusinessHoursId
- [ ] SLA compliance queries filter to terminal-state milestones only (`IsCompleted=true OR IsViolated=true`)
- [ ] `IsViolated=true AND IsCompleted=true` late completions correctly categorized
- [ ] Custom Report Type deployed and joins validated
- [ ] Milestone type filter uses exact admin-configured milestone names

---

## Known Deviations and Notes

(Record any departures from the standard patterns and the reason — e.g., "Using calendar MTTR only because org SLA contracts are calendar-time-based," "Single entitlement tier so defaulting to org Business Hours.")
