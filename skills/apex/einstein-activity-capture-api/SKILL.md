---
name: einstein-activity-capture-api
description: "Use when querying Einstein Activity Capture (EAC) activity metrics, accessing synced email and event data via Apex, reporting on captured activities, or understanding EAC's read-only API surface and SOQL limits. Triggers: 'ActivityMetric SOQL', 'EAC data not in reports', 'UnifiedActivity query', 'query synced emails from EAC', 'activity capture SOQL returns no rows'. NOT for email template design or email deliverability configuration. NOT for enabling, configuring, or troubleshooting EAC in Setup — use admin/einstein-activity-capture-setup."
category: apex
salesforce-version: "Spring '25+ (legacy reporting retires Spring '27)"
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
  - "EAC storage architecture: legacy external store vs Sync Email as Salesforce Activity (Summer '25+ opt-in)"
  - "org EAC edition (standard vs Unlimited with enhanced storage)"
  - "whether legacy Activity Metrics / A360 reporting is still in use (retiring Spring '27)"
  - "which objects are in scope: ActivityMetric, EmailMessage, Task, Event, or UnifiedActivity"
  - "reporting requirements: aggregate counts vs individual activity records"
outputs:
  - "SOQL patterns for querying EAC data through supported API surfaces"
  - "architectural guidance on EAC read-only constraints and reporting workarounds"
  - "review findings on EAC data access gaps and recommended patterns"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-08-14
---

# Einstein Activity Capture API

Use this skill when an org uses Einstein Activity Capture to sync emails and calendar events from Gmail or Outlook, and a developer needs to read that synced data programmatically, query activity metrics, or understand why EAC records are invisible to standard SOQL, triggers, and reports — **or** why legacy Activity Metrics fields suddenly return null.

---

## Before Starting

Gather this context before working on anything in this domain:

- **EAC storage architecture (decide first):** **Legacy EAC** stores synced activity in an external store — SOQL against `Task` / `EmailMessage` returns zero rows and syncs do not fire standard object triggers. **Sync Email as Salesforce Activity** (Summer '25+) writes captured email as standard `Task` / `EmailMessage` records queryable with ordinary SOQL and report types. Orgs created — or enabling EAC for the first time — after Summer '25 get this automatically and have no access to the legacy EAC reports; orgs that enabled EAC earlier must opt in. Confirm which model the org uses before writing queries or trigger logic.
- **Legacy reporting retirement (Spring '27, February 2027):** **Activity Metrics**, the **Activities Dashboard**, **Recommended Connections**, and **Activity 360 Reports** retire — including `UnifiedEmail`, `UnifiedEmailParticipant`, `UnifiedMeeting`, `UnifiedMeetingParticipant`, `UnifiedTask` and `UnifiedTaskParticipant`. Activity Metrics fields stop populating and custom code referencing them returns **null**, not an exception. Plan migration to **Activities with Accounts** / **Activities with Opportunities** (or Task/EmailMessage SOQL) before the deadline.
- **Most common wrong assumption:** Developers assume that because emails appear in the Activity Timeline UI, they are queryable via `[SELECT Id FROM EmailMessage WHERE ...]`. On **legacy** EAC they are not. On **Sync Email as Salesforce Activity** they are — the opposite mistake (still querying `ActivityMetric` only) builds on a retiring surface.
- **Supported read surfaces:** On legacy EAC, `ActivityMetric` (aggregate, retiring Spring '27) and, where already provisioned, `UnifiedActivity`. On Sync Email as Salesforce Activity, standard `Task` / `EmailMessage` are the long-term surfaces.
- **Read-only by design:** `ActivityMetric` and EAC-managed synthetic objects cannot be written through production Apex DML. Sync Email records follow normal Task/EmailMessage DML rules.

---

## Core Concepts

### EAC Data Lives Outside Standard Salesforce Storage (Legacy EAC)

Before **Sync Email as Salesforce Activity**, synced email and calendar activity resided in a Salesforce-managed external store. The Activity Timeline UI reads from that store using internal APIs, which is why the timeline looks populated even when SOQL returns nothing. Standard objects like `Task`, `Event`, and `EmailMessage` do not contain EAC-originated records in this model. This is not a permission issue — it is a storage architecture boundary.

### Sync Email as Salesforce Activity (Summer '25+)

When enabled, captured email syncs into standard **`Task`** and **`EmailMessage`** records. Auto-captured emails appear in standard activity report types and are visible to ordinary SOQL, flows, and Apex triggers. This is the documented replacement path for legacy Activity Metrics / A360 reporting before the Spring '27 retirement.

### ActivityMetric: Legacy Aggregate Surface (Retiring Spring '27)

`ActivityMetric` holds aggregate engagement counts per `Who` target (Lead or Contact). It remains queryable on legacy architectures but is on a **published retirement path** — fields stop populating and references return null ahead of removal. Do not start new designs on Activity Metrics; audit existing Apex, flows, and reports that reference it.

### A360 Objects (Retiring Spring '27)

The Activity 360 object family retires with A360 Reports. Salesforce Help enumerates exactly six objects: `UnifiedEmail`, `UnifiedEmailParticipant`, `UnifiedMeeting`, `UnifiedMeetingParticipant`, `UnifiedTask`, `UnifiedTaskParticipant`. Existing A360 report types stop returning data when retired.

`UnifiedActivity` is **not** on that published list — it is a separately documented object representing an activity captured from EAC or another source. Treat it as neither confirmed-retiring nor confirmed-safe: it is gated on Activity 360 Reporting having been enabled before Summer '25, so verify availability in the target org rather than assuming either way, and do not start new designs on it.

### EAC Reporting Constraints

EAC data is available in a dedicated **Einstein Activity Capture** report type in the Reports tab, separate from the standard Activities report type. The two report types cannot be joined in a single report. `EmailMessage` records from EAC cannot be joined with `Task` or `Event` in one report type even in Write-Back-enabled orgs because EAC EmailMessage and standard EmailMessage are logically separate. Reports on ActivityMetric are possible through the dedicated EAC report type.

---

## Common Patterns

### Querying Activity Engagement Counts via ActivityMetric (legacy EAC only)

**When to use:** Legacy EAC org that has not migrated, and the goal is aggregate email or meeting counts. Do not start new designs here — Activity Metrics retires Spring '27 and fields return null before removal. For Sync Email as Salesforce Activity, aggregate `Task` / `EmailMessage` instead (see Decision Guidance).

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

**Why not the alternative:** On **legacy** EAC, querying `Task` or `EmailMessage` for synced data returns empty results. ActivityMetric is the interim aggregate surface there — not a long-term one. On Sync Email as Salesforce Activity, `Task` / `EmailMessage` aggregation is the replacement.

### Surfacing EAC Data in a Custom Component Without Write-Back (legacy EAC only)

**When to use:** A Lightning Web Component needs engagement totals for a record on **legacy** EAC (no Sync Email architecture). Treat this as migration debt.

**How it works:** Build an Apex controller that queries `ActivityMetric` filtered to the record's related contacts or leads. Return aggregate totals to the component. Never attempt to query `Task WHERE ActivityType = 'Email'` expecting EAC records on legacy EAC — that returns empty.

**Why not the alternative:** The Activity Timeline UI already surfaces raw timeline entries. On Sync Email architecture, query `Task` / `EmailMessage` instead of ActivityMetric.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need aggregate email/meeting counts for contacts | **New work:** aggregate `Task` / `EmailMessage` on Sync Email architecture (persist to a custom field if the score must stay queryable). **Legacy interim only:** `ActivityMetric`, with a Spring '27 migration plan | ActivityMetric is on a published retirement path; fields return null before removal |
| Need individual synced email records in Apex | **Sync Email architecture:** query `Task` / `EmailMessage`. **Legacy:** `UnifiedActivity` only if already provisioned | The six A360 `Unified*` objects have a published Spring '27 end date; `UnifiedActivity` is not on that list but is gated on pre-Summer-'25 A360 enablement — verify, don't assume |
| Need reports on captured activity | **Migrate:** Activities with Accounts / Activities with Opportunities on Sync Email architecture; legacy EAC report type retires Spring '27 | Dedicated EAC/A360 report types are on retirement path |
| Need to trigger Apex on an EAC email sync | **Legacy:** scheduled batch on `ActivityMetric` — no trigger fires; **Sync Email:** ordinary `Task` / `EmailMessage` trigger | Architecture-dependent — see Security note below |
| Need to write to or modify EAC-synced records | **Sync Email:** normal Task/EmailMessage DML rules. **Legacy:** ActivityMetric is read-only in production | ActivityMetric DML throws in production |
| Org is migrating to Sync Email as Salesforce Activity | Audit Activity Metrics / A360 references; validate Task/EmailMessage SOQL before cutover | Retirement is Spring '27; nulls precede hard removal |

### Security note for trigger-driven Sync Email designs

The sharing **declaration** on a trigger is fixed; the **outcome** of each database operation is not. Do not treat these as two independent axes.

- **Declaration (undeclarable):** Apex triggers cannot have an explicit sharing declaration. They always run implicitly in a without-sharing context — `Trigger.new` may include captured email the running user cannot otherwise read.
- **Outcome (per operation):** Database operations in the trigger body — SOQL, SOSL, DML, `Database` methods — run in **user mode** unless system mode is explicitly specified. User mode enforces the running user's sharing rules, FLS, and object permissions, and **overrides** the trigger's implicit without-sharing context for that operation. Qualify this by **`apiVersion` in `.trigger-meta.xml`**, not by org release: at **67.0+** a bare query already runs in user mode. `WITH SYSTEM_MODE` / `AccessLevel.SYSTEM_MODE` opts out — FLS and object permissions are skipped, and record sharing falls back to the trigger's without-sharing context.

Set the access mode explicitly on every query in the trigger and its handler. This is **not** "triggers always run in system mode", and it is **not** "sharing and access mode are independent."

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm EAC storage architecture** — legacy external store vs **Sync Email as Salesforce Activity**. Check EAC settings / admin skill; this determines every SOQL and trigger decision.
2. **Audit retirement exposure** — search Apex, flows, and reports for Activity Metrics fields, A360 / Unified* objects, and Recommended Connections. Run `scripts/check_einstein_activity_capture_api.py`.
3. **Identify required data shape** — aggregate (legacy `ActivityMetric`, retiring) vs individual records (`Task` / `EmailMessage` on Sync Email architecture).
4. **Write and test SOQL against the confirmed surface** — never assume Task/EmailMessage contain EAC data on legacy EAC; never assume ActivityMetric is a long-term surface on Sync Email orgs.
5. **Guard against empty results and null metrics** — unconnected accounts yield no rows; retiring Activity Metrics yields null without exceptions.
6. **Validate in an org with EAC connected accounts** — sandboxes often lack live connections.
7. **Document architecture assumption** — comment which EAC model the code targets.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed legacy vs Sync Email as Salesforce Activity architecture before choosing query surface.
- [ ] No new dependencies on Activity Metrics, A360 report types, or Unified* objects without a Spring '27 migration plan.
- [ ] Trigger assumptions match architecture (none on legacy EAC; valid Task/EmailMessage triggers on Sync Email — with explicit access mode).
- [ ] No production DML against `ActivityMetric`.
- [ ] Report requirements use Activities with Accounts/Opportunities (Sync Email) or documented legacy interim types with retirement date.
- [ ] Code handles empty SOQL and null Activity Metrics gracefully.
- [ ] Test classes seed `ActivityMetric` only in `@isTest`; live validation requires connected accounts.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Activity Timeline looks populated but SOQL returns nothing** — The timeline UI reads from the EAC external store using internal APIs. SOQL against Task/Event/EmailMessage returns zero EAC rows in standard orgs. These are separate data paths.
2. **ActivityMetric is populated per connected account user only** — Users who have not connected a Gmail or Outlook account have no ActivityMetric rows. Bulk queries across an entire org will silently skip unconnected users.
3. **EAC report types cannot be joined with standard Activities** — EmailMessage from EAC and standard EmailMessage records live in separate report type families. Attempting to combine them in one report is not supported.
4. **Sandbox EAC behavior does not match production** — Sandboxes do not replicate EAC connected account connections. Developers testing EAC queries in sandbox with no connected accounts will always get zero rows.
5. **ActivityMetric is read-only in production; DML throws exceptions** — DML on ActivityMetric is supported only in `@isTest` contexts for seeding test data.
6. **Activity Metrics null before retirement** — fields stop populating ahead of Spring '27 removal; engagement scores built on ActivityMetric silently read as zero.

---

## Official Sources Used

- EAC Activity Metrics, Dashboard, Recommended Connections and A360 Reports Retirement — https://help.salesforce.com/s/articleView?id=005384640&language=en_US&type=1 — source for the Spring '27 (February 2027) date, the four retiring features, the six A360 objects, the null-return failure mode, and the Activities with Accounts / Activities with Opportunities replacement path.
- Activity 360 Reporting, Activity Metrics, Activities Dashboard Upcoming Retirement — https://help.salesforce.com/s/articleView?id=004633781&language=en_US&type=1 — source for the Summer '25 split: orgs created or enabling EAC after Summer '25 get Sync Email as Salesforce Activity automatically with no access to legacy EAC reports; earlier orgs must opt in.
- UnifiedEmail Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_unifiedemail.htm
- ActivityMetric Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_activitymetric.htm
- Using the with sharing, without sharing, and inherited sharing Keywords — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_keywords_sharing.htm — "Apex triggers can't have an explicit sharing declaration"; "Triggers always run implicitly in a without sharing context"; "Database operations within trigger bodies ... run in user mode unless system mode is explicitly specified"; "User mode overrides the trigger's without sharing context and effectively enforces a with sharing context in the trigger body." Qualify by apiVersion, not org release.
- Set an Access Mode for Database Operations — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_enforce_usermode.htm — user-mode database operations always respect sharing; system mode defers sharing to the trigger/class sharing context.

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
