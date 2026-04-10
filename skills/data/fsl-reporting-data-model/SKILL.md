---
name: fsl-reporting-data-model
description: "Use this skill when building Salesforce reports and dashboards on FSL operational data: job completion metrics, travel time analytics, first-time fix rate, utilization, and service performance. Trigger keywords: FSL reporting, ServiceAppointment reports, ActualDuration ActualTravelTime, first-time fix rate custom field, FSL utilization metrics. NOT for CRM Analytics / Field Service Intelligence (Einstein Analytics), ServiceReport PDF generation, or non-FSL service reporting."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
triggers:
  - "How to build first-time fix rate report in FSL without native field"
  - "ServiceAppointment ActualDuration not populating in FSL reports"
  - "FSL travel time analytics requires mobile check-in to populate ActualTravelTime"
  - "ServiceReport object is not a standard Salesforce report — how to access completion data"
  - "FSL utilization reporting by resource and territory"
tags:
  - fsl
  - field-service
  - reporting
  - service-appointment
  - analytics
  - fsl-reporting-data-model
inputs:
  - "Desired FSL operational metrics (FTF rate, utilization, travel time, job duration)"
  - "Whether FSL Mobile check-in is consistently used (required for travel time data)"
  - "Whether CRM Analytics / FSI license is available (out of scope for this skill)"
outputs:
  - "Report type and field selections for FSL operational metrics"
  - "Custom formula or Flow pattern for first-time fix rate"
  - "Data model explanation for ServiceAppointment reporting fields"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# FSL Reporting Data Model

This skill activates when a Salesforce administrator or developer needs to build native Salesforce reports and dashboards on Field Service operational data. FSL's reporting model has several non-obvious behaviors: key metrics like ActualTravelTime only populate when mobile check-in is used, first-time fix rate has no native field and requires custom logic, and the ServiceReport object is a customer-facing PDF — not a standard Salesforce Report.

---

## Before Starting

Gather this context before working on anything in this domain:

- Determine whether FSL Mobile check-in is consistently used by technicians. `ActualDuration` and `ActualTravelTime` on ServiceAppointment are only populated when technicians use the mobile app check-in workflow — orgs that don't enforce mobile usage will have empty travel time data.
- Confirm whether CRM Analytics / Field Service Intelligence is licensed. This skill covers native Salesforce Reports; FSI/Einstein Analytics is out of scope.
- Understand what "first-time fix rate" means in the business context — FSL does not have a native FTF field. It must be calculated from appointment statuses (no "Cannot Complete" predecessor).
- Identify whether reporting needs to be at the Work Order level, ServiceAppointment level, or both.

---

## Core Concepts

### ServiceAppointment — Primary Reporting Object

`ServiceAppointment` is the core FSL reporting object. Key fields for operational reporting:

| Field | Populated When | Notes |
|---|---|---|
| `ActualDuration` | Technician checks out via FSL Mobile | Null if mobile check-in not used |
| `ActualTravelTime` | Technician checks in via FSL Mobile | Null if mobile check-in not used |
| `ArrivalWindowStart/End` | Appointment booked with arrival window | When customer was told to expect technician |
| `SchedStartTime/EndTime` | Scheduled by FSL engine | When FSL assigned the technician |
| `Status` | Lifecycle transitions | Completed, Cannot Complete, etc. |
| `ServiceTerritoryId` | Territory assignment | For territory-level reports |
| `ActualStartTime/EndTime` | Mobile check-in/check-out | Real start/end times |

### First-Time Fix Rate — No Native Field

FSL has no native "first-time fix rate" field or formula. FTF must be calculated as the percentage of Work Orders completed with only one ServiceAppointment that did not have a predecessor "Cannot Complete" appointment.

**Pattern 1 (custom formula):** Add a custom formula field on WorkOrder: `IF(COUNT(ServiceAppointments) = 1 AND ServiceAppointments[0].Status = 'Completed', 1, 0)`. Note: formula fields cannot directly access child record sets — this requires a Rollup Summary or Flow.

**Pattern 2 (Flow + custom field):** A record-triggered Flow on ServiceAppointment fires when Status = 'Completed'. The Flow checks whether any predecessor SA on the same WO has Status = 'Cannot Complete'. If none, it stamps a `First_Time_Fix__c = true` checkbox on the WorkOrder.

**Pattern 3 (SOQL-based report metric):** Build a report using the ServiceAppointment report type with a cross-filter: "ServiceAppointments where WorkOrder has no other ServiceAppointment with Status = Cannot Complete." This is the most practical for a standard report.

### ServiceReport — NOT a Standard Report

`ServiceReport` is a Salesforce object representing a customer-facing PDF work completion document (similar to a field service delivery receipt). It is NOT a Salesforce Report object and does not appear in the standard Reports tab. Operational metrics are not in ServiceReport — they are in ServiceAppointment and WorkOrder.

### Travel Analytics — Mobile Dependency

`ActualTravelTime` is populated only when:
1. The technician uses FSL Mobile
2. The technician clicks "En Route" (check-in start) and "On Site" (arrival) in the mobile app

Orgs that allow technicians to update ServiceAppointment status without the mobile app will have null `ActualTravelTime` for those records. Travel analytics in such orgs will be systematically incomplete.

---

## Common Patterns

### Resource Utilization Report

**When to use:** Operations manager needs to see scheduled hours vs. available hours per technician per week.

**How it works:** Create a custom report type joining ServiceResource → AssignedResource → ServiceAppointment. Include fields: ServiceResource Name, SchedStartTime, SchedEndTime, ActualStartTime, ActualEndTime. Add formula columns for scheduled duration and actual duration. Group by ServiceResource + week.

### On-Time Arrival Report

**When to use:** Measuring whether technicians arrive within the committed arrival window.

**How it works:** ServiceAppointment report with calculated field: `IF(ActualStartTime <= ArrivalWindowEnd, 'On Time', 'Late')`. This requires ActualStartTime to be populated — again, requires FSL Mobile check-in.

---

## Decision Guidance

| Metric | Object | Source Fields | Gotcha |
|---|---|---|---|
| Job duration | ServiceAppointment | ActualDuration | Only populated with mobile check-in |
| Travel time | ServiceAppointment | ActualTravelTime | Only populated with mobile check-in |
| On-time arrival | ServiceAppointment | ActualStartTime vs. ArrivalWindowEnd | Requires mobile check-in |
| First-time fix rate | WorkOrder + ServiceAppointment | Custom Flow field | No native field |
| Customer work report PDF | ServiceReport | Not a standard Report | Different object entirely |

---

## Recommended Workflow

1. **Identify required metrics** — Catalog each metric, its data source field, and whether mobile check-in is a prerequisite.
2. **Verify mobile check-in adoption** — Query `SELECT COUNT() FROM ServiceAppointment WHERE ActualDuration = null AND Status = 'Completed'`. High count means mobile check-in is not consistently used — flag this as a data quality issue before reporting.
3. **Build FTF rate mechanism** — Choose Pattern 2 (Flow + custom field) for real-time FTF tracking. Deploy Flow, backfill historical data.
4. **Create report types** — Use the ServiceAppointment report type as the primary type for all job-level metrics. Use Work Order for WO-level aggregation.
5. **Build dashboards** — Use chart components for FTF trend, utilization by territory, and on-time arrival rate. Add metric components for weekly/monthly totals.
6. **Document data quality dependencies** — Note explicitly in dashboard documentation that travel time and duration metrics require FSL Mobile check-in usage.

---

## Review Checklist

- [ ] Mobile check-in adoption rate verified before building travel time reports
- [ ] ServiceReport object understood as customer-facing PDF, not operational report source
- [ ] FTF rate custom logic (Flow + field) deployed and backfilled
- [ ] Report type correctly joins ServiceAppointment to ServiceResource for utilization
- [ ] ActualDuration vs. SchedDuration fields compared to measure schedule accuracy
- [ ] Dashboard documentation notes mobile check-in data dependency

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **ActualDuration and ActualTravelTime are null without mobile check-in** — These fields are only populated when technicians use the FSL Mobile app's En Route and On Site status transitions. Reports built on these fields will show blank data for orgs not enforcing mobile usage.
2. **ServiceReport is a customer-facing PDF object — not a standard report** — Accessing work completion data for operational reporting requires ServiceAppointment and WorkOrder, not ServiceReport.
3. **First-time fix rate has no native FSL field** — Building FTF without a custom field or Flow produces no real-time metric. The custom logic must be deployed before FTF trend reporting is meaningful.
4. **Reporting on travel time across districts is unreliable without full mobile adoption** — Even 10% non-mobile usage in a territory creates systematic gaps in travel analytics, making territory-level comparisons misleading.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FTF rate Flow design | Record-triggered Flow on ServiceAppointment for first-time fix rate calculation |
| FSL operational report list | Standard report types and field selections for key FSL metrics |

---

## Related Skills

- architect/fsl-optimization-architecture — Understanding scheduled vs. actual time to measure optimization effectiveness
- data/fsl-resource-and-skill-data — Resource data context for utilization reporting
