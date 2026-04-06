---
name: service-metrics-data-model
description: "Use when designing or reporting on Salesforce Service Cloud service metrics — covers the Case, Entitlement, and CaseMilestone object model, MTTR derivation via BusinessHours.diff(), IsViolated semantics, and ElapsedTimeInMins field usage for SLA reporting. Trigger keywords: MTTR, mean time to resolve, case milestone, entitlement SLA, IsViolated, CaseMilestone, first response time, resolution time, service KPI. NOT for CRM Analytics (Tableau CRM / Einstein Analytics) dashboards or Field Service Lightning work order metrics."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Performance
  - Scalability
triggers:
  - "how do I calculate mean time to resolve cases in Salesforce"
  - "my CaseMilestone IsViolated is true even though the milestone was completed"
  - "how do I build a report showing SLA compliance and first response time by queue"
  - "what fields do I use to measure case resolution time against entitlement SLA"
  - "ElapsedTimeInMins on CaseMilestone is not matching what I expected"
tags:
  - service-metrics
  - case
  - casemilestone
  - entitlement
  - sla
  - mttr
  - service-cloud
  - data-model
inputs:
  - "Whether Entitlements are enabled in the org (Setup > Entitlement Settings)"
  - "Which Milestones are active on the Entitlement Process (e.g., First Response, Resolution)"
  - "Whether Business Hours are configured and assigned to the relevant Entitlement Process"
  - "Whether cases are closed via a specific record type or status value used for MTTR derivation"
  - "Which reporting tool is in use — native Salesforce reports vs. external BI — to decide field strategy"
outputs:
  - "Object model map (Case, Entitlement, CaseMilestone) with field-level guidance for service KPI reporting"
  - "MTTR derivation approach using BusinessHours.diff() or formula field on Case"
  - "SLA compliance SOQL query patterns for milestone-level and case-level reporting"
  - "Decision guidance for IsViolated vs. CompletionDate vs. TargetDate interpretation"
  - "Review checklist before publishing service metric reports"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Service Metrics Data Model

This skill activates when a practitioner needs to design, query, or troubleshoot Salesforce Service Cloud service metrics — including mean time to resolve (MTTR), SLA milestone compliance, first response tracking, and related KPI reporting. It covers the Case, Entitlement, and CaseMilestone object model, the semantics of key fields like `IsViolated`, `ElapsedTimeInMins`, and `TargetDate`, and how to derive metrics that have no native single field in the platform. It does NOT cover CRM Analytics (Tableau CRM / Einstein Analytics) or Field Service Lightning work order metrics.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Entitlements and Milestones must be enabled**: Setup > Entitlement Settings. Without this, `CaseMilestone` records are not created and SLA fields on Case are unavailable. Confirm the Entitlement Process is active and assigned to cases before any milestone-based reporting.
- **Business Hours matter for all time calculations**: Salesforce SLA milestone calculations respect Business Hours. `ElapsedTimeInMins` on `CaseMilestone` counts only business-hours minutes by default when a Business Hours record is assigned to the Entitlement Process. If Business Hours are not configured, elapsed time counts calendar minutes.
- **No native MTTR field exists**: There is no single `MTTR` or `ResolutionTimeMinutes` field on Case. Mean time to resolve must be derived from `Case.ClosedDate - Case.CreatedDate` (calendar time) or via `BusinessHours.diff()` in Apex for business-hours-aware MTTR. In SOQL/reports, use a custom formula field.
- **IsViolated is not the same as "milestone was not completed"**: A CaseMilestone where `IsViolated = true` and `CompletionDate` is populated means the milestone was completed — but completed after the `TargetDate`. This counterintuitive state catches practitioners off-guard when they treat `IsViolated = true` as "open" milestones in filters.

---

## Core Concepts

### Case Object — Foundation of Service Metrics

The `Case` object is the primary record for all service interactions. Key fields for service metric derivation:

- `CreatedDate` — timestamp when the case was opened; used as the start point for MTTR and elapsed-time calculations.
- `ClosedDate` — timestamp when case status transitioned to a Closed status value; used as the end point for MTTR. This field is null on open cases.
- `Status` — current case status; "Closed" statuses are admin-configurable. MTTR formulas must account for which status values are considered "closed."
- `EntitlementId` — lookup to the Entitlement record linking the case to an SLA tier. Without this populated, no Entitlement Process runs and no CaseMilestones are created for the case.
- `IsClosed` — boolean; use this rather than parsing `Status` text in formulas and SOQL for robustness across orgs with custom closed-status values.

**MTTR via formula field on Case** (calendar time):

```
IF(IsClosed,
   (ClosedDate - CreatedDate) * 24 * 60,
   NULL)
```

This gives MTTR in minutes as a formula Number field. It does not respect Business Hours. For business-hours-aware MTTR, use `BusinessHours.diff()` in Apex and store the result in a custom field updated via trigger.

### Entitlement Object — SLA Tier Linkage

The `Entitlement` object represents an SLA agreement (e.g., "Platinum Support — 24-hour response, 4-hour resolution"). It links an Account or Asset to an Entitlement Process that defines the Milestone sequence and timing.

Key fields:
- `EntitlementProcessId` — the Entitlement Process driving milestone creation and timing for associated Cases.
- `Status` — Active, Expired, or Inactive. Milestones are only created when Entitlement status is Active.
- `StartDate` / `EndDate` — define the validity window. Cases opened outside this window do not receive milestones even if an `EntitlementId` is set.
- `BusinessHoursId` — the Business Hours record applied to SLA time calculations for this entitlement. If null, calendar hours are used.

The Entitlement Process configures which Milestones fire, when they are due (offset from case creation or prior milestone completion), and what happens on violation (notifications, field updates, escalations via Process Builder/Flow).

### CaseMilestone Object — The SLA Measurement Unit

`CaseMilestone` is the junction object that tracks each milestone instance for each Case. It is the primary table for SLA compliance reporting.

Key fields:
- `CaseId` — parent Case lookup.
- `MilestoneTypeId` — which milestone type (e.g., "First Response," "Resolution") — joins to `MilestoneType`.
- `StartDate` — when the milestone clock started for this case.
- `TargetDate` — the deadline computed from the Entitlement Process offset + Business Hours. This is when the milestone must be completed to avoid violation.
- `CompletionDate` — timestamp when the milestone was marked complete. Null if the milestone is still open.
- `IsCompleted` — boolean; true when `CompletionDate` is populated.
- `IsViolated` — boolean; true when the milestone was not completed by `TargetDate`. Critically: **`IsViolated` can be `true` even when `IsCompleted` is `true` and `CompletionDate` is populated** — this means the milestone was completed late.
- `ElapsedTimeInMins` — the number of business-hours minutes elapsed from `StartDate` to `CompletionDate` (or to now, for open milestones). This is Salesforce-computed and respects the assigned Business Hours. Use this field for SLA performance comparisons rather than computing raw time deltas.

---

## Common Patterns

### Pattern: MTTR Derivation Without a Native Field

**When to use:** A support operations team needs a Case-level metric for mean time to resolve, usable in Salesforce reports and dashboards without Apex.

**How it works:**
1. Create a custom Number or Formula field on Case: `MTTR_Calendar_Mins__c` (Number, populated by trigger) or a Formula field (if Apex is not available).
2. For a formula field: `IF(IsClosed, (ClosedDate - CreatedDate) * 24 * 60, NULL)` — gives calendar-time minutes.
3. For business-hours-aware MTTR, write an Apex after-update trigger that calls `BusinessHours.diff(bhId, CreatedDate, ClosedDate)` and stores the result in `MTTR_BH_Mins__c` when `IsClosed` becomes true.
4. Report on `MTTR_Calendar_Mins__c` or `MTTR_BH_Mins__c` using Summary reports with AVG aggregation grouped by Case Owner, Queue, Priority, or Month.

**Why not just use ElapsedTimeInMins on CaseMilestone:** `ElapsedTimeInMins` measures the time for an individual milestone (e.g., First Response), not the full case resolution span. MTTR from case open to case close spans multiple milestones and requires Case-level fields.

### Pattern: SLA Compliance Rate Reporting via CaseMilestone

**When to use:** A service manager wants a monthly SLA compliance report showing what percentage of First Response and Resolution milestones were met on time by queue.

**How it works:**
1. Query `CaseMilestone` joined to `Case` and `MilestoneType`:
   - Filter on `IsCompleted = true` OR `IsViolated = true` (to exclude future open milestones from compliance calculations).
   - Use `IsViolated` to compute violated count; use `NOT IsViolated AND IsCompleted` to compute compliant count.
2. Build a Salesforce Summary report on `CaseMilestone` with the Custom Report Type joining `Case` and `MilestoneType`.
3. Group by `MilestoneType.Name` and Case `Owner.Queue` (via `Case.Queue` field or owner hierarchy).
4. Add custom summary formula: `MTTR_Compliance_Rate = (NOT_VIOLATED_COUNT / TOTAL_COMPLETED_COUNT) * 100`.

**Why not filter on IsViolated = false alone:** Open, in-progress milestones also have `IsViolated = false` (they have not been violated yet). Including them in a compliance denominator inflates compliance rate with incomplete data.

### Pattern: First Response Time Isolation

**When to use:** The SLA contract defines a maximum time to first response (e.g., 4 business hours). Reporting needs to show compliance per case per support tier.

**How it works:**
1. Query `CaseMilestone WHERE MilestoneType.Name = 'First Response'`.
2. Use `ElapsedTimeInMins` as the actual response time in business minutes.
3. Compare to the `TargetDate`-derived SLA threshold — or directly use `IsViolated`.
4. For cases where `CompletionDate` is set but `IsViolated = true`: elapsed time exceeded the Entitlement Process target; these are late responses, not missing responses.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need calendar-time MTTR on Case | Formula field: `(ClosedDate - CreatedDate) * 24 * 60` | Zero Apex; works declaratively in reports |
| Need business-hours-aware MTTR | Apex trigger calling `BusinessHours.diff()` storing result in custom field | Formula fields cannot call Apex methods; BH-aware metric requires Apex |
| Need SLA milestone compliance rate | Query `CaseMilestone` filtering on `IsCompleted = true OR IsViolated = true` | Excludes open future milestones from compliance denominator |
| IsViolated = true on a completed milestone | Milestone was completed late — after TargetDate | Not a data error; expected Salesforce behavior |
| Need to report on milestones still open and at risk | Filter `IsCompleted = false AND IsViolated = false AND TargetDate < NOW()` | These are overdue and not yet auto-violated — escalation candidates |
| Need elapsed time in minutes for a specific milestone | Use `ElapsedTimeInMins` on `CaseMilestone` | Platform-computed; respects Business Hours; do not re-derive manually |
| Multiple entitlement tiers with different SLAs | Store Entitlement.Name or SLA tier on Case via flow/formula for report grouping | CaseMilestone does not expose Entitlement tier directly; denormalize at report design time |
| MTTR needed across thousands of cases in external BI | Export Case with `CreatedDate`, `ClosedDate`, `IsClosed`, `MTTR_BH_Mins__c` | Bulk-exportable; pre-computed field avoids re-deriving BH logic outside Salesforce |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on service metrics data model tasks:

1. **Verify prerequisites**: Confirm Entitlements are enabled (Setup > Entitlement Settings). Confirm at least one Entitlement Process is Active and assigned to Cases via the `EntitlementId` lookup. Check that Business Hours records are configured and assigned to relevant Entitlement records. Without these, `CaseMilestone` records will not exist and SLA metrics cannot be reported.

2. **Map the metric requirement to the object and field**: Determine whether the metric is case-level (MTTR, handle time) or milestone-level (first response time, resolution SLA compliance). Case-level metrics require fields on `Case` (derive `MTTR`). Milestone-level metrics use `CaseMilestone.ElapsedTimeInMins`, `IsViolated`, `TargetDate`, `CompletionDate`.

3. **Design MTTR derivation**: For calendar MTTR, create a Formula Number field on Case: `IF(IsClosed, (ClosedDate - CreatedDate) * 24 * 60, NULL)`. For business-hours MTTR, write an Apex trigger on Case (after update, when `IsClosed` becomes true) that calls `BusinessHours.diff(bhId, case.CreatedDate, case.ClosedDate)` and stores the result in `MTTR_BH_Mins__c`. Confirm the correct `BusinessHoursId` is used — it should match the Entitlement's Business Hours assignment.

4. **Design SLA compliance queries and report types**: Create a Custom Report Type joining `CaseMilestone > Case > MilestoneType`. Use `IsViolated` and `IsCompleted` together to correctly categorize milestone outcomes: compliant (IsCompleted=true, IsViolated=false), late (IsCompleted=true, IsViolated=true), open at-risk (IsCompleted=false, IsViolated=false, TargetDate in past), open on-track (IsCompleted=false, IsViolated=false, TargetDate in future). Do not use `IsViolated = false` as a proxy for "compliant" — it includes unresolved milestones.

5. **Validate ElapsedTimeInMins accuracy**: Cross-check `ElapsedTimeInMins` on a sample of CaseMilestone records against the `StartDate` to `CompletionDate` delta using the assigned Business Hours. If Business Hours were changed after milestones were created, `ElapsedTimeInMins` may reflect the old Business Hours configuration. Confirm Business Hours alignment before publishing SLA reports.

6. **Build and test reports**: Build Salesforce Summary reports grouped by MilestoneType.Name and period. Add custom summary formulas for compliance rate. Validate that the denominator excludes open future milestones. For MTTR reports on Case, validate AVG MTTR against a known set of closed cases. Cross-check formula field values against manual calculations on sample records.

7. **Document SLA tier context for stakeholders**: Record which Entitlement Process and Business Hours configuration underpins each reported metric. Document the `IsViolated=true AND IsCompleted=true` interpretation for report consumers — late completions count as SLA misses, not failures to respond.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Entitlements and at least one active Entitlement Process confirmed in the org
- [ ] CaseMilestone records exist for a sample of test cases — not just an empty table
- [ ] Business Hours correctly assigned to the Entitlement Process and confirmed to reflect contractual SLA hours
- [ ] MTTR formula or Apex trigger tested against closed cases with known open/close timestamps
- [ ] `BusinessHours.diff()` called with the correct BusinessHoursId matching the Entitlement's assignment (not the default org business hours unless confirmed identical)
- [ ] SLA compliance SOQL or report filters exclude open in-progress milestones from the compliance denominator (`IsCompleted = true OR IsViolated = true`)
- [ ] `IsViolated = true AND IsCompleted = true` cases identified and correctly labeled as "late completions" not "open violations"
- [ ] CaseMilestone Custom Report Type deployed and joins validated with test data
- [ ] Milestone type grouping (`MilestoneType.Name`) confirmed to match admin-configured milestone names exactly (case-sensitive text match in filters)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **IsViolated = true does not mean the milestone is still open** — `IsViolated` is set to `true` when a milestone's `TargetDate` passes without completion. It remains `true` permanently even after the milestone is completed late. A CaseMilestone with `IsCompleted = true`, `CompletionDate` populated, and `IsViolated = true` represents a late completion — the most common misread in SLA reports.

2. **No native MTTR field exists** — There is no platform-provided `MTTR` field on Case. Practitioners who assume `ElapsedTimeInMins` on `CaseMilestone` gives them full case resolution time are wrong: `ElapsedTimeInMins` measures only the span of that individual milestone, not the full case lifecycle from creation to close.

3. **ElapsedTimeInMins reflects business hours at the time of calculation, not at case creation** — If Business Hours configuration changes after a CaseMilestone is created, the stored `ElapsedTimeInMins` may not accurately reflect the new Business Hours. Always validate against the effective Business Hours at the time of milestone creation.

4. **Entitlement StartDate/EndDate silently blocks milestone creation** — If a case is created while the Entitlement's `EndDate` is in the past (expired entitlement), no `CaseMilestone` records are created even if the `EntitlementId` is populated. Cases appear to have an SLA but have no milestones to track — a silent gap in SLA reporting coverage.

5. **CaseMilestone TargetDate uses the Entitlement's Business Hours, not the org default** — If a case is escalated and its Entitlement is changed mid-case to one with different Business Hours, existing open milestones retain their original `TargetDate`. New milestones created after the change use the new Entitlement's Business Hours. Reports comparing milestones across entitlement changes require careful interpretation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `service-metrics-data-model-template.md` | Work template for documenting service metrics requirements — captures metric-to-field mapping, MTTR derivation approach, SLA compliance query design, and known IsViolated edge cases |
| `check_service_metrics_data_model.py` | stdlib Python checker that scans Salesforce metadata XML for common issues: missing Entitlement configuration, formula field MTTR definitions, Case milestone field usage patterns |

---

## Related Skills

- `sales-reporting-data-model` — use for Reporting Snapshots and Historical Trend Reporting patterns when building point-in-time SLA compliance archives
- `soql-query-optimization` — use when SOQL queries against `CaseMilestone` or `Case` with large data volumes are slow or hitting governor limits
- `data-quality-and-governance` — use when assessing whether Entitlement assignment completeness across Cases is sufficient for reliable SLA reporting
- `opportunity-pipeline-migration` — reference for Apex trigger patterns (BusinessHours.diff() usage) when building the MTTR derivation trigger
