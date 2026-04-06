---
name: einstein-activity-capture-api
description: "Use when querying Einstein Activity Capture (EAC) activity metrics, accessing synced email and event data via Apex, reporting on captured activities, or understanding EAC's read-only API surface and SOQL limits. Triggers: 'ActivityMetric SOQL', 'EAC data not in reports', 'UnifiedActivity query', 'query synced emails from EAC', 'activity capture SOQL returns no rows'. NOT for email template design, email deliverability configuration, or enabling/disabling EAC through Setup UI."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
tags:
  - einstein-activity-capture
  - activity-metrics
  - eac
  - unified-activity
  - email-sync
  - soql
triggers:
  - "how do I query EAC synced emails and calendar events from Apex"
  - "ActivityMetric SOQL returns no rows or empty results"
  - "EAC data is not showing up in reports or triggers"
  - "how to read activity capture counts per contact or lead"
  - "UnifiedActivity object query for captured activities"
inputs:
  - "org EAC edition (standard vs Unlimited with enhanced storage)"
  - "whether EAC Write-Back is enabled (Summer '25+)"
  - "which objects are in scope: ActivityMetric, EmailMessage, Task, Event, or UnifiedActivity"
  - "reporting requirements: aggregate counts vs individual activity records"
outputs:
  - "SOQL patterns for querying EAC data through supported API surfaces"
  - "architectural guidance on EAC read-only constraints and reporting workarounds"
  - "review findings on EAC data access gaps and recommended patterns"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Einstein Activity Capture API

Use this skill when an org uses Einstein Activity Capture to sync emails and calendar events from Gmail or Outlook, and a developer needs to read that synced data programmatically, query activity metrics, or understand why EAC records are invisible to standard SOQL, triggers, and reports.

---

## Before Starting

Gather this context before working on anything in this domain:

- **EAC edition and storage model:** Pre-Summer '25 EAC stored synced activity data in an external AWS-managed store invisible to SOQL, triggers, and standard report types. Summer '25+ orgs with EAC Write-Back can optionally write synced activities to standard Salesforce storage. Confirm which model the org uses before writing queries.
- **Most common wrong assumption:** Developers assume that because emails appear in the Activity Timeline UI, they are queryable via `[SELECT Id FROM EmailMessage WHERE ...]` or `[SELECT Id FROM Task WHERE ...]`. For standard EAC without Write-Back, they are not. SOQL against those objects returns zero rows for EAC-sourced records.
- **Supported read surfaces:** The primary programmatic surfaces are (1) `ActivityMetric` — aggregate engagement counts per lead/contact per day, and (2) `UnifiedActivity` — a newer synthetic object available in orgs with enhanced EAC storage. Raw EmailMessage and Task records from EAC sync are not in the standard SOQL layer unless Write-Back is active.
- **Read-only by design:** EAC-managed records cannot be written, triggered against, or included in standard rollup summaries through normal Apex DML. Attempts to insert or update these records throw exceptions.

---

## Core Concepts

### EAC Data Lives Outside Standard Salesforce Storage (Pre-Write-Back)

Before Summer '25 EAC Write-Back, all synced email and calendar activity data resided in a Salesforce-managed external store. The Activity Timeline UI component reads from that store using internal APIs, which is why the timeline looks populated even when SOQL returns nothing. Standard objects like `Task`, `Event`, and `EmailMessage` do not contain EAC-originated records in this model. This is not a permission issue — it is a storage architecture boundary. No amount of sharing settings or FLS adjustments will surface data that is not in the standard data store.

### ActivityMetric: The Supported SOQL Surface for Aggregate Counts

`ActivityMetric` is a standard Salesforce object that EAC populates with aggregate activity engagement counts per `Who` target (Lead or Contact). Each row represents one `Who` + one calendar date + one metric type combination. Common fields include `EmailCount`, `MeetingCount`, `EmailOpenCount`, and `EmailReplyCount`. This object IS queryable via SOQL and is the primary way Apex code and reports can consume EAC data in non-Write-Back orgs. Counts are rolled up by EAC internally; they are not real-time row-by-row records of individual activities.

### UnifiedActivity: Newer Synthetic Query Surface

`UnifiedActivity` is a read-only synthetic object introduced for orgs with enhanced EAC storage. It exposes individual captured activities — emails, meetings, calls — as queryable records. It is NOT the same as Task or Event. It has its own field schema and cannot be used in DML. Not all orgs have this object available; presence depends on the EAC edition and whether enhanced storage is provisioned.

### EAC Reporting Constraints

EAC data is available in a dedicated **Einstein Activity Capture** report type in the Reports tab, separate from the standard Activities report type. The two report types cannot be joined in a single report. `EmailMessage` records from EAC cannot be joined with `Task` or `Event` in one report type even in Write-Back-enabled orgs because EAC EmailMessage and standard EmailMessage are logically separate. Reports on ActivityMetric are possible through the dedicated EAC report type.

---

## Common Patterns

### Querying Activity Engagement Counts via ActivityMetric

**When to use:** The goal is to read aggregate email or meeting engagement counts for a list of leads or contacts — for example, to calculate a custom activity score or surface engagement data in a Lightning Web Component.

**How it works:** Query `ActivityMetric` filtering by `WhoId` (the Lead or Contact ID) and optionally `ActivityDate`. Aggregate the metric fields your use case needs. Because this is a standard SOQL query the governor limit rules apply normally.

```apex
// Fetch last 30 days of email activity counts for a set of contact IDs
Set<Id> contactIds = new Set<Id>{ '003...', '003...' };
Date cutoff = Date.today().addDays(-30);

List<ActivityMetric> metrics = [
    SELECT WhoId, ActivityDate, EmailCount, MeetingCount, EmailOpenCount
    FROM ActivityMetric
    WHERE WhoId IN :contactIds
      AND ActivityDate >= :cutoff
    ORDER BY ActivityDate DESC
];

Map<Id, Integer> emailCountByContact = new Map<Id, Integer>();
for (ActivityMetric m : metrics) {
    Integer current = emailCountByContact.containsKey(m.WhoId)
        ? emailCountByContact.get(m.WhoId) : 0;
    emailCountByContact.put(m.WhoId, current + (Integer) m.EmailCount);
}
```

**Why not the alternative:** Querying `Task` or `EmailMessage` for synced data returns empty results in standard EAC orgs. ActivityMetric is the only supported aggregate read surface.

### Surfacing EAC Data in a Custom Component Without Write-Back

**When to use:** A Lightning Web Component or Visualforce page needs to show activity engagement data for a record, and the org uses standard EAC without Write-Back.

**How it works:** Build an Apex controller that queries `ActivityMetric` filtered to the record's related contacts or leads. Return aggregate totals to the component. Never attempt to query `Task WHERE ActivityType = 'Email'` expecting EAC records — this will always return empty for synced activities in standard EAC orgs.

**Why not the alternative:** The Activity Timeline UI component already surfaces raw timeline entries. Custom Apex is appropriate when you need aggregated metrics in business logic, scoring, or custom UX that goes beyond what the timeline shows.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need aggregate email/meeting counts for contacts | Query `ActivityMetric` | Supported SOQL surface for aggregate EAC data |
| Need individual synced email records in Apex | Check if Write-Back is enabled; use `UnifiedActivity` if available | Raw sync records are not in standard Task/EmailMessage without Write-Back |
| Need reports on captured activity | Use EAC-specific report type in Reports tab | Standard Activities report type does not include EAC data |
| Need to trigger Apex on an EAC email sync | Not directly possible — use scheduled batch instead | EAC records do not fire standard object triggers |
| Need to write to or modify EAC-synced records | Redesign — EAC records are read-only | DML against EAC records is not supported in production |
| Org is Summer '25+ with Write-Back | Verify standard EmailMessage/Task contains synced records before querying | Write-Back copies records into standard storage; confirm via sample SOQL |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm EAC storage model** — determine whether the org is using standard EAC (external store, ActivityMetric only) or has Write-Back enabled (Summer '25+). Check EACSettings metadata or ask the org admin. This determines every subsequent SOQL decision.
2. **Identify required data shape** — clarify whether the use case needs aggregate counts (ActivityMetric is sufficient) or individual activity records (requires UnifiedActivity or Write-Back). Do not assume individual records are available.
3. **Write and test SOQL against the confirmed surface** — query ActivityMetric for aggregate data. If UnifiedActivity is available, verify the org has enhanced storage provisioned before relying on it in production.
4. **Guard against empty results defensively** — always code defensively: EAC data may not be populated for contacts with no connected accounts, and dates before EAC was enabled will have no rows.
5. **Validate in an org with EAC connected accounts** — EAC data requires a live connected Gmail or Outlook account. Developer Edition orgs or sandboxes without connected accounts will always return zero rows regardless of the query.
6. **Review report requirements separately** — if the use case includes reports, confirm the EAC report type is used and that cross-joining with standard Activities is not expected.
7. **Document storage model assumption** — add a code comment or configuration note specifying which EAC storage model the code was written for, so future maintainers know the context.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed whether org uses standard EAC or Write-Back-enabled EAC before choosing query surface.
- [ ] All EAC data reads use `ActivityMetric` (aggregate) or `UnifiedActivity` (individual, if available) — not `Task`, `Event`, or `EmailMessage` for synced records in non-Write-Back orgs.
- [ ] No Apex trigger logic assumes it will fire when EAC syncs an email or calendar event.
- [ ] No DML (insert/update/delete) targets EAC-managed records in production code.
- [ ] Report requirements are satisfied using the EAC report type, not the standard Activities report type.
- [ ] Code is guarded against empty results when no connected accounts exist or EAC is not enabled.
- [ ] Test classes seed `ActivityMetric` in `@isTest` context rather than relying on sandbox data.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Activity Timeline looks populated but SOQL returns nothing** — The timeline UI reads from the EAC external store using internal APIs. SOQL against Task/Event/EmailMessage returns zero EAC rows in standard orgs. These are separate data paths.
2. **ActivityMetric is populated per connected account user only** — Users who have not connected a Gmail or Outlook account have no ActivityMetric rows. Bulk queries across an entire org will silently skip unconnected users.
3. **EAC report types cannot be joined with standard Activities** — EmailMessage from EAC and standard EmailMessage records live in separate report type families. Attempting to combine them in one report is not supported.
4. **Sandbox EAC behavior does not match production** — Sandboxes do not replicate EAC connected account connections. Developers testing EAC queries in sandbox with no connected accounts will always get zero rows.
5. **ActivityMetric is read-only in production; DML throws exceptions** — Any attempt to insert, update, or delete ActivityMetric rows from production Apex fails with a `System.DmlException`. DML on ActivityMetric is supported only in `@isTest` contexts for seeding test data.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| EAC storage model determination | Assessment of whether the org uses standard EAC or Write-Back-enabled EAC |
| ActivityMetric query pattern | SOQL and Apex service code for reading aggregate engagement counts |
| EAC reporting guidance | Recommendation for which report type to use and what cross-joins are not possible |
| Review findings | Issues found in existing code that incorrectly targets Task/Event/EmailMessage for EAC data |

---

## Related Skills

- `apex/soql-fundamentals` — use for general SOQL query optimization and governor limit guidance alongside EAC queries.
- `apex/platform-cache` — use when ActivityMetric query results should be cached to reduce repeated SOQL calls per page load.
- `agentforce/einstein-copilot-for-sales` — use when the broader Einstein for Sales feature set (Opportunity Scoring, Pipeline Inspection) is in scope alongside EAC.
