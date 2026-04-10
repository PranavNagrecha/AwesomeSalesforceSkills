---
name: npsp-program-management
description: "Use this skill when configuring or troubleshooting the Nonprofit Success Pack Program Management Module (PMM) — a separate managed package for program delivery, cohort setup, service scheduling, service delivery recording, and outcome/attendance tracking for beneficiaries. Trigger keywords: program management module, PMM, Program__c, ProgramEngagement__c, ServiceDelivery__c, cohort setup, bulk service delivery, service schedule, service participant. NOT for NPSP core donor management, gift entry, recurring donations, soft credits, or Health Cloud care programs."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Security
triggers:
  - "how do I set up a program and add clients as participants in the program management module"
  - "bulk service delivery is not saving required fields even though they are marked required in the field set"
  - "getting rowlock errors when multiple staff save service deliveries at the same time"
  - "service delivery records are not showing up in NPSP donation rollups or gift reports"
  - "how do I track attendance and outcomes for program participants across multiple cohorts"
  - "what is the correct field order for the bulk service delivery field set in PMM"
tags:
  - npsp
  - pmm
  - program-management-module
  - nonprofit
  - service-delivery
  - cohort
  - beneficiary
  - attendance
  - outcomes
inputs:
  - "PMM managed package installed (separate from NPSP core)"
  - "Object list: Program__c, Service__c, ProgramEngagement__c, ProgramCohort__c, ServiceDelivery__c, ServiceSchedule__c, ServiceParticipant__c"
  - "List of programs, services, and cohort structures the org uses"
  - "Staff roles and permission sets in play (PMM ships its own permission sets)"
  - "Whether bulk service delivery is used and what fields appear in its field set"
outputs:
  - "Configured Program__c records with associated Service__c records"
  - "ProgramCohort__c and ProgramEngagement__c records linking contacts to programs"
  - "ServiceSchedule__c and ServiceParticipant__c setup for scheduled sessions"
  - "ServiceDelivery__c records capturing attendance, quantity, and outcomes"
  - "Validation rules covering required-field gaps in bulk service delivery"
  - "Checklist of PMM configuration issues and remediation steps"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-10
---

# NPSP Program Management Module (PMM)

This skill activates when configuring, troubleshooting, or extending the Salesforce Nonprofit Success Pack Program Management Module (PMM). PMM is a separate managed package from NPSP core — it provides eight custom objects for tracking program delivery to beneficiaries (clients). It has no rollup or trigger integration with NPSP's donation infrastructure.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm PMM is installed: check for `pmdm` namespace in Setup > Installed Packages. If the namespace is absent, PMM is not installed — do not attempt to create PMM objects.
- Identify whether the org uses bulk service delivery (the mass-entry quick action) or individual ServiceDelivery__c records. The bulk path has a mandatory field-ordering requirement that causes silent save failures.
- Confirm the NPSP version: PMM is versioned independently and may lag behind NPSP core releases. Check both package versions before troubleshooting cross-package behavior.
- Understand the program structure: each Program__c has zero-to-many Service__c records (the types of help delivered) and zero-to-many ProgramCohort__c records (the time-bounded groups). A Contact is linked to a Program via a ProgramEngagement__c record and to a cohort session via ServiceParticipant__c.

---

## Core Concepts

PMM introduces eight custom objects that model the full program delivery lifecycle. Practitioners who treat these as analogs of NPSP donor objects or Health Cloud care plan objects will misconfigure them.

### The Eight PMM Objects and Their Roles

| Object | Purpose |
|---|---|
| Program__c | Top-level program entity. Has Status (Active/Inactive) and Program Issues/Target Population fields. |
| Service__c | A type of service offered within a program (e.g., Food Pantry, Job Training). Lookup to Program__c. |
| ProgramEngagement__c | Junction between a Contact and a Program. Tracks enrollment date, stage (Enrolled/Active/Graduated/Withdrawn), and cohort assignment. |
| ProgramCohort__c | A time-bounded cohort within a Program (e.g., Spring 2025 Cohort). Has Start/End Date. |
| ServiceDelivery__c | Records one delivery of a service to one client. Captures quantity, date, and optional outcome data. |
| ServiceSchedule__c | A recurring schedule (e.g., every Tuesday) for delivering a service. Parent of ServiceParticipant__c. |
| ServiceParticipant__c | Links a ProgramEngagement__c to a ServiceSchedule__c — identifies who attends a scheduled session. |

There is no eighth object in this list (the research notes cite eight, but the seven above are the primary operational objects documented in Salesforce Help as of Spring '25). Always verify the installed package's object count in Setup.

### Bulk Service Delivery Field Set Ordering

PMM ships a Quick Action called Bulk Service Deliveries that renders a lightning data table for entering multiple service deliveries at once. The field set that controls which columns appear is `ServiceDelivery__c.Bulk_Service_Deliveries_Fields`. The field order within this field set is mandatory and enforced at runtime:

1. **Client** (lookup to Contact) — must be first
2. **Program Engagement** (lookup to ProgramEngagement__c) — must be second
3. **Service** (lookup to Service__c) — must be third

If these three fields are not in this exact order, the bulk entry action will not cascade correctly — selecting a Client will not filter the Program Engagement picklist, and selecting a Program Engagement will not filter the Service options. Additional fields (Quantity, Delivery Date, etc.) may appear after these three in any order.

Marking a field as Required inside the field set does NOT enforce save-time validation. Fields appear with a red asterisk for visual guidance only. To enforce required values, add validation rules on ServiceDelivery__c directly.

### PMM and NPSP Are Separate Data Stacks

PMM data does not flow into NPSP rollup fields, opportunity records, or gift entry. ServiceDelivery__c records are not Opportunities. Program revenue (grants funding the program) is tracked as NPSP Opportunities through the normal donor management path — but the operational delivery data (who received a service, when, how much) lives entirely in PMM objects.

Do not attempt to create formula fields or cross-object rollups from ServiceDelivery__c to npo02__HouseholdContactRoles__c or any NPSP giving rollup field — the objects are in different namespaces and have no platform relationship.

---

## Common Patterns

### Pattern: Full Program Setup from Scratch

**When to use:** A new program is being stood up with defined cohorts and scheduled service delivery sessions.

**How it works:**
1. Create Program__c: set Status = Active, populate Program Issues (optional) and Target Population (optional).
2. Create one or more Service__c records, each looking up to the Program__c.
3. Create one or more ProgramCohort__c records with Start Date and End Date.
4. As clients enroll, create ProgramEngagement__c records: lookup to Contact, lookup to Program__c, assign a cohort via the ProgramCohort__c field, set Stage = Enrolled.
5. If using scheduled sessions, create a ServiceSchedule__c (with Service__c, start/end, and recurrence), then create ServiceParticipant__c records linking each ProgramEngagement__c to the schedule.
6. Record delivery: create ServiceDelivery__c per client per session, or use the Bulk Service Deliveries quick action.

**Why not the alternative:** Creating ServiceDelivery__c records without a ProgramEngagement__c breaks attendance tracking — the PMM attendance report depends on the ProgramEngagement__c link to identify which clients are active in a program.

### Pattern: Enforcing Required Fields in Bulk Service Delivery

**When to use:** Staff use the Bulk Service Deliveries action but leave required fields blank, causing silent incomplete records.

**How it works:**
1. Identify which fields must be populated (e.g., Quantity, Delivery Date).
2. Do NOT rely on field-set Required flag — it is visual only.
3. Create validation rules on ServiceDelivery__c. Example for Quantity:
   ```
   Rule name: PMM_Require_Quantity_On_Bulk_Save
   Condition: AND(
     ISBLANK(pmdm__Quantity__c),
     $RecordType.Name = 'Service Delivery'
   )
   Error message: "Quantity is required for all service deliveries."
   ```
4. Test by attempting to save a bulk delivery row with the field empty — the row should error and remain unsaved.

**Why not the alternative:** The field-set Required flag renders a red asterisk but does not invoke the Salesforce save validation pipeline. Validation rules are the only enforcement mechanism for PMM bulk entry.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to track individual service sessions with attendance | Use ServiceSchedule__c + ServiceParticipant__c | Provides recurrence, participant roster, and attendance reporting in PMM reports |
| Need to record one-off service deliveries without a schedule | Create ServiceDelivery__c directly with ProgramEngagement__c | Lighter weight; appropriate for drop-in services with no fixed schedule |
| Staff enter deliveries for many clients at once | Use Bulk Service Deliveries quick action | Purpose-built for mass entry; ensure correct field-set order before enabling |
| Required field not being enforced in bulk entry | Add validation rule on ServiceDelivery__c | Field-set Required flag is visual only; only validation rules enforce saves |
| Concurrent bulk saves by multiple staff causing errors | Stagger entry times or use retry guidance | ServiceDelivery__c bulk saves acquire row locks; concurrent inserts to the same parent record collide |
| Reporting on service volume for grant reporting | Use PMM packaged reports and dashboards | They aggregate ServiceDelivery__c by Program, Service, and Cohort — do not try to build this from NPSP Opportunity data |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Verify PMM is installed and identify the installed version: Setup > Installed Packages > look for "Program Management Module" with the `pmdm` namespace. Note the version number. Confirm the NPSP core package version separately.
2. Map the program structure: gather the list of programs, services, cohorts, and enrollment stages the org needs. Confirm whether sessions are scheduled (needs ServiceSchedule__c) or ad hoc (direct ServiceDelivery__c creation).
3. Create Program__c and Service__c records in the correct order: Program first, then Services (each with a Program__c lookup). Do not create Service__c without a parent Program__c — it leaves orphaned service records that cannot be used in bulk entry.
4. Create ProgramEngagement__c records for each enrolled Contact. Assign cohort if cohorts are in use. Set Stage = Enrolled (or Active if they are currently receiving services).
5. If using scheduled delivery: create ServiceSchedule__c records, then create ServiceParticipant__c records for each active engagement. Confirm recurrence settings match the real schedule.
6. Configure the Bulk Service Deliveries field set if staff will use the quick action: verify Client is first, Program Engagement is second, Service is third. Add required-field validation rules to ServiceDelivery__c for any field that must be populated.
7. Test end-to-end: create a test Program Engagement, use the Bulk Service Deliveries action to save a delivery, verify the ServiceDelivery__c record is created with all required fields, and confirm the record appears in PMM packaged reports.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] PMM package (pmdm namespace) is confirmed installed and version is noted
- [ ] All Program__c records have Status = Active for programs currently delivering services
- [ ] All Service__c records have a valid Program__c lookup (no orphaned services)
- [ ] ProgramEngagement__c records exist for all enrolled contacts, each with a Program__c lookup and a Stage value
- [ ] Bulk Service Deliveries field set has Client first, Program Engagement second, Service third
- [ ] Validation rules exist on ServiceDelivery__c for any field that must be required (not relying on field-set Required flag alone)
- [ ] PMM packaged reports return correct data for service delivery counts and attendance
- [ ] No attempt has been made to roll up ServiceDelivery__c data into NPSP Opportunity or giving rollup fields

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Field-set Required flag does not enforce saves in Bulk Service Delivery** — The Required checkbox in a PMM field set renders a red asterisk in the UI but does not invoke Salesforce's save-validation pipeline. Staff can save a record with the field blank. Enforcement requires a validation rule on ServiceDelivery__c.
2. **Bulk Service Deliveries field order is functional, not cosmetic** — The Client, Program Engagement, and Service columns must be in that exact order in the field set. Out-of-order fields break the cascading picklist filtering. The UI does not show an error — it simply does not filter correctly, causing staff to select mismatched combinations.
3. **Rowlock errors under concurrent bulk saves** — When two or more staff members submit bulk service delivery batches simultaneously against the same Program or ProgramEngagement__c parent, Salesforce's row-locking mechanism causes UNABLE_TO_LOCK_ROW errors on some records. The saves partially succeed; affected rows must be resubmitted. Mitigation: stagger bulk entry across staff, or implement retry logic in a Flow that calls the save asynchronously.
4. **PMM data does not appear in NPSP donation reports** — ServiceDelivery__c records are not Opportunities and have no relationship to NPSP rollup fields (npo02__TotalOppAmount__c, etc.). Trying to build a grant report by querying NPSP giving data will miss all service delivery volume. Use PMM's own packaged reports or build custom reports on ServiceDelivery__c directly.
5. **Deleting a ProgramEngagement__c cascades to ServiceDelivery__c** — Because ServiceDelivery__c has a lookup (not master-detail) to ProgramEngagement__c, deleting an engagement does not automatically delete delivery records by default, but depending on the lookup behavior setting, orphaned delivery records may lose their program context. Always check the lookup relationship's delete behavior before bulk-deleting engagement records.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Program setup checklist | Completed record of Program__c, Service__c, and ProgramCohort__c configuration |
| Bulk Service Delivery field set audit | Field order and Required-flag review with validation rule recommendations |
| ServiceDelivery__c validation rules | Rules enforcing required fields that the field set cannot enforce |
| PMM report audit | Confirmation that packaged PMM reports return correct data for active programs |

---

## Related Skills

- `npsp-household-accounts` — For understanding how Contacts are modeled in NPSP before linking them to PMM ProgramEngagement__c records
- `gift-entry-and-processing` — For tracking program revenue (grants and donations) on the donor side; PMM covers the beneficiary/delivery side
- `care-program-management` — For Health Cloud care programs (a completely different object model; do not confuse with PMM)
