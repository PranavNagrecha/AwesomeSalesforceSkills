# NPSP Program Management Module (PMM) — Work Template

Use this template when working on PMM configuration, troubleshooting, or service delivery setup tasks.

## Scope

**Skill:** `npsp-program-management`

**Request summary:** (fill in what the user asked for — e.g., "Set up a new job training program with weekly cohorts and bulk service delivery" or "Fix: required fields not enforced in bulk entry")

---

## Context Gathered

Answer these before starting any PMM work:

- **PMM package version:** (check Setup > Installed Packages > Program Management Module)
- **NPSP core package version:** (check Setup > Installed Packages > Nonprofit Success Pack)
- **Program structure:** (list program names, associated services, and cohort schedule)
- **Delivery entry method:** [ ] Bulk Service Deliveries quick action  [ ] Individual ServiceDelivery__c records  [ ] ServiceSchedule__c + attendance action
- **Known constraints:** (any limits, existing automation, or cross-org integrations)
- **Required fields for service delivery:** (list fields that must not be blank on save)

---

## Program Setup Checklist

Complete in order — each step depends on the previous:

### Step 1: Program__c Records
- [ ] Program__c created with Status = Active
- [ ] Program Issues and Target Population populated (optional but recommended for reporting)
- [ ] Program Name matches the naming convention agreed with stakeholders

### Step 2: Service__c Records
- [ ] One or more Service__c records created under each Program__c
- [ ] Each Service__c has a valid pmdm__Program__c lookup (no orphaned services)
- [ ] Service names are distinct enough for staff to tell apart in bulk entry dropdowns

### Step 3: ProgramCohort__c Records (if using cohorts)
- [ ] ProgramCohort__c records created with Start Date and End Date
- [ ] Cohort names follow a consistent naming pattern (e.g., "Spring 2025 — Job Training")

### Step 4: ProgramEngagement__c Records
- [ ] ProgramEngagement__c records created for each enrolled Contact
- [ ] Each engagement has a valid pmdm__Program__c lookup
- [ ] Stage set appropriately (Enrolled / Active / Graduated / Withdrawn)
- [ ] ProgramCohort__c assigned if cohorts are in use

### Step 5: ServiceSchedule__c and ServiceParticipant__c (if using scheduled delivery)
- [ ] ServiceSchedule__c created for each recurring session
- [ ] Service__c lookup populated on each schedule
- [ ] Start date, end date, and recurrence configured
- [ ] ServiceParticipant__c records created for each active ProgramEngagement__c per schedule

### Step 6: Bulk Service Delivery Configuration (if using quick action)
- [ ] Bulk_Service_Deliveries_Fields field set verified: (1) Client, (2) Program Engagement, (3) Service
- [ ] Validation rules exist on ServiceDelivery__c for all fields that must be required
- [ ] End-to-end test completed: bulk entry for at least one client creates a valid ServiceDelivery__c record

---

## Validation Rules Needed

List any fields that must be required in Bulk Service Delivery (field-set Required flag is NOT sufficient):

| Field API Name | Condition | Error Message |
|---|---|---|
| pmdm__DeliveryDate__c | `ISBLANK(pmdm__DeliveryDate__c)` | Delivery Date is required on all service delivery records. |
| pmdm__Quantity__c | `ISBLANK(pmdm__Quantity__c) \|\| pmdm__Quantity__c <= 0` | Quantity must be greater than zero. |
| (add more as needed) | | |

---

## Known Gotchas for This Engagement

Check which of these apply to this org before completing the work:

- [ ] Bulk entry field order: Client first, Program Engagement second, Service third — verified?
- [ ] Concurrent staff entry: is staff count high enough to risk rowlock errors? If yes, document the staggering approach.
- [ ] No rollup to NPSP: stakeholders confirmed that service delivery data will NOT appear in NPSP gift/donation reports?
- [ ] pmdm__ namespace: all SOQL, Flow, and automation references confirmed to include pmdm__ prefix?
- [ ] Orphaned services: validation rule on Service__c requiring pmdm__Program__c lookup — in place?

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Full Program Setup from Scratch
- [ ] Enforcing Required Fields with Validation Rules
- [ ] Recording Attendance for a Scheduled Program
- [ ] Other (describe):

Reason for pattern choice:

---

## Test Results

| Test Scenario | Pass / Fail | Notes |
|---|---|---|
| Create Program__c and Service__c — Service appears in bulk entry dropdown | | |
| Bulk entry: Client selection filters Program Engagement column correctly | | |
| Bulk entry: Program Engagement selection filters Service column correctly | | |
| Bulk entry: save with required field blank triggers validation error | | |
| ServiceDelivery__c record created with correct pmdm__Program__c context | | |
| PMM packaged report shows correct delivery counts for the program | | |

---

## Notes

Record any deviations from the standard pattern and why:

- Deviation:
- Reason:
- Impact:
