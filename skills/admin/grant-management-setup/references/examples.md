# Examples — Grant Management Setup

## Example 1: Setting Up a FundingAward with Quarterly Disbursement Tranches in Nonprofit Cloud for Grantmaking

**Context:** A community foundation on Nonprofit Cloud with the Grantmaking license needs to configure a $120,000 multi-year capacity-building grant to a grantee organization, disbursed in four quarterly tranches of $30,000 each. The grants manager needs to track each payment independently and see the full disbursement schedule on the award record.

**Problem:** Without proper FundingDisbursement configuration, grants staff either create four separate FundingAward records (breaking rollup reporting) or track tranches in a spreadsheet outside Salesforce (no audit trail, no automation, no reporting integration).

**Solution:**

```
(Corrected 2026-10-03 to the documented field names and picklist values in the
Nonprofit Cloud Developer Guide; the earlier version used invented fields such as
Grantee__c, AwardAmount__c, DisbursementAmount, a Draft status, and a Closed award status.)

1. Create FundingAward record:
   - AwardeeId = [Grantee Account]
   - Amount = 120000
   - StartDate = 2025-01-01, EndDate = 2025-12-31
   - Status = Active
   - FundingOpportunityId = [Capacity Building funding opportunity]

2. Create four FundingDisbursement child records on the FundingAward:
   Tranche 1: ScheduledDate = 2025-01-15, Amount = 30000, Status = Scheduled
   Tranche 2: ScheduledDate = 2025-04-15, Amount = 30000, Status = Scheduled
   Tranche 3: ScheduledDate = 2025-07-15, Amount = 30000, Status = Scheduled
   Tranche 4: ScheduledDate = 2025-10-15, Amount = 30000, Status = Scheduled

3. Add totals on FundingAward (custom fields, maintained by a Flow or a
   roll-up summary if the org allows one on this master-detail relationship):
   - Total_Disbursed__c = SUM of FundingDisbursement.Amount WHERE Status = 'Paid'
   - Remaining_Balance__c = Amount - Total_Disbursed__c
   UNVERIFIED (2026-10-03): whether roll-up summary fields are allowed from
   FundingDisbursement to FundingAward was not confirmed; plan a Flow if not.

4. Build a Flow on FundingDisbursement to:
   - Notify grants manager when ScheduledDate is within 14 days and Status = Scheduled
   - Set FundingAward.Status to 'Completed' when every FundingDisbursement is Paid or Cancelled
```

**Why it works:** FundingDisbursement is purpose-built for tranche tracking. Each disbursement has an independent status, scheduled date, and amount field, enabling pipeline reports, payment reminders, and rollup calculations without custom objects. The parent-child relationship preserves the full award context on every tranche record.

---

## Example 2: Tracking Grant Deliverables Using FundingAwardRequirement Status Workflow

**Context:** A healthcare foundation on Nonprofit Cloud for Grantmaking requires grantees to submit a 6-month Progress Report and a Final Report before the second and final disbursement tranches are released. The grants team needs a structured way to track submission, review, and approval of each deliverable — and to block payment until requirements are met.

**Problem:** Without FundingAwardRequirement, grants teams use Chatter posts or Tasks to track deliverables. These produce no structured data, cannot be queried in SOQL, cannot gate automation, and make audit reporting impossible.

**Solution:**

```
(Corrected 2026-10-03: the standard object already has a FundingDisbursementId lookup,
Type values are Combined Report, Contract, Financial Report, and Narrative Report,
there is no Draft disbursement status, and a validation rule cannot see the
requirements that point at a disbursement.)

1. At award setup, create two FundingAwardRequirement records on the FundingAward:
   Requirement 1:
     - Name = "6-Month Progress Report"
     - Type = Narrative Report
     - DueDate = 2025-07-01T17:00:00Z
     - Status = Open
     - FundingDisbursementId = [Tranche 2 FundingDisbursement]

   Requirement 2:
     - Name = "Final Report"
     - Type = Combined Report
     - DueDate = 2025-12-01T17:00:00Z
     - Status = Open
     - FundingDisbursementId = [Tranche 4 FundingDisbursement]

2. When the grantee submits (Experience Cloud or staff action):
   - Set IsSubmitted = true, SubmittedDate = now, Status = Submitted
   - Notify the grants manager for review

3. When the grants manager decides:
   - Set ApprovalStatus = Approved (or Rejected) and Status = Approved (or Rejected)
   - A Rejected report goes back to In Progress with feedback in Description

4. Gate the payment with a before-save record-triggered Flow on FundingDisbursement:
   - When Status changes to 'Paid', get FundingAwardRequirement records where
     FundingDisbursementId = this record and Status != 'Approved'
   - If any exist, show the error "All requirements linked to this disbursement
     must be Approved before payment can be processed."
```

**Why it works:** FundingAwardRequirement's `Status`, `ApprovalStatus`, and `IsSubmitted` fields carry the review lifecycle. Linking requirements to specific disbursements enables targeted gating: only the tranches tied to unmet requirements are blocked, not the entire award. This produces an auditable, reportable, automatable deliverable tracking system with no custom objects required.

---

## Anti-Pattern: Using Separate FundingAward Records per Tranche

**What practitioners do:** Create one FundingAward record for each disbursement (e.g., "Smith Foundation Grant — Q1 2025," "Smith Foundation Grant — Q2 2025") to represent each payment tranche separately.

**What goes wrong:**
- Total award amount cannot be reported as a single figure — grants pipeline reports show 4x the actual committed funding.
- FundingAwardRequirement records must be duplicated across all four "award" records, breaking requirement tracking.
- Relationship to the funder Account becomes ambiguous — four records for one grant creates noise in the funder's related list.
- Roll-up reporting on "Total Awarded to Grantee" double- or quadruple-counts the grant.

**Correct approach:** Create one FundingAward per grant agreement. Use FundingDisbursement child records to represent each tranche. The parent-child model is the correct data structure for scheduled payment plans.

---

## Example 3: Turn On Grantmaking, Grant Access, And Deploy The Same-Record Payment Rules

**Context:** A foundation with the Nonprofit Cloud for Grantmaking licence sets up its first programme. The setup must be repeatable in a sandbox first, and the payment rules must deploy with the release.

**Step 1: confirm the licence** (Object Reference, PermissionSetLicense):

```soql
SELECT MasterLabel, DeveloperName, Status, TotalLicenses, UsedLicenses
FROM PermissionSetLicense
WHERE MasterLabel LIKE '%Grantmaking%'
```

**Step 2: the Setup procedure** (Grantmaking Guide, Spring '26):

1. In a sandbox first: Setup > Quick Find **Grantmaking** > **Grantmaking Settings** > turn on Grantmaking. This cannot be undone, and Salesforce recommends not turning it on in an org with the Grants Management managed package installed.
2. Setup > **Permission Sets**: assign **Grantmaking Manager** to grants staff (it auto-assigns the Grantmaking permission set licence) and **Grantmaking for Experience Cloud** to portal users. Put any custom field access in a custom permission set and combine them in a permission set group.
3. If applications use Individual Application: Object Manager > **Individual Application** > **Record Types** > New, label `Grantmaking`, based on Master, active. Then Setup > Quick Find **Application RecordType Config** > **New Application RecordType Config**: Application Usage Type = Grantmaking, Object Name = Individual Application, Record Type Name = `Grantmaking`.
4. App Launcher > **Funding Award** > New: complete Amount, the contract timeframe, and Budget; then add requirements and the disbursement schedule as related records.

**Step 3: the deployable same-record rules.** A disbursement can move to Paid only from Approved or Processing, and needs a disbursement date. `force-app/main/default/objects/FundingDisbursement/validationRules/Paid_Requires_Approval.validationRule-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Paid_Requires_Approval</fullName>
    <active>true</active>
    <description>A tranche moves to Paid only from Approved or Processing, and Paid needs a disbursement date.</description>
    <errorConditionFormula>AND(
    ISPICKVAL(Status, "Paid"),
    OR(
        ISBLANK(DisbursementDate),
        AND(
            ISCHANGED(Status),
            NOT(ISPICKVAL(PRIORVALUE(Status), "Approved")),
            NOT(ISPICKVAL(PRIORVALUE(Status), "Processing"))
        )
    )
)</errorConditionFormula>
    <errorDisplayField>Status</errorDisplayField>
    <errorMessage>Move this disbursement to Approved or Processing and enter the disbursement date before marking it Paid.</errorMessage>
</ValidationRule>
```

A requirement cannot be Approved before it was submitted. `force-app/main/default/objects/FundingAwardRequirement/validationRules/Approval_Requires_Submission.validationRule-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ValidationRule xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Approval_Requires_Submission</fullName>
    <active>true</active>
    <description>Approved requires a submitted requirement with a submission date.</description>
    <errorConditionFormula>AND(
    OR(ISPICKVAL(Status, "Approved"), ISPICKVAL(ApprovalStatus, "Approved")),
    OR(NOT(IsSubmitted), ISBLANK(SubmittedDate))
)</errorConditionFormula>
    <errorDisplayField>Status</errorDisplayField>
    <errorMessage>Mark the requirement as submitted, with a submitted date, before approving it.</errorMessage>
</ValidationRule>
```

Field names (`Status`, `DisbursementDate`, `ApprovalStatus`, `IsSubmitted`, `SubmittedDate`) and picklist values come from the NPC Guide's FundingDisbursement and FundingAwardRequirement references; the element names come from the Metadata API ValidationRule reference. The rule uses the prior `Status` rather than `IsApproved`, because the guide lists `IsApproved` without the Create or Update property, so users cannot set it. Records created directly as Paid (historical loads) pass the status check because `ISCHANGED` is false on insert. UNVERIFIED (2026-10-03): that the picklist API values equal the documented labels ("Paid", "Approved", "Processing").

**Step 4: manifest members:**

| Component | Type | `package.xml` member form |
|---|---|---|
| Disbursement rule | `ValidationRule` | `<members>FundingDisbursement.Paid_Requires_Approval</members><name>ValidationRule</name>` |
| Requirement rule | `ValidationRule` | `<members>FundingAwardRequirement.Approval_Requires_Submission</members><name>ValidationRule</name>` |
| Grants team access | `PermissionSetGroup` | `<members>Grants_Team</members><name>PermissionSetGroup</name>` |

The cross-record gate (no Paid tranche while a requirement pointing at it is not Approved) is the before-save flow in Example 2, step 4, because a validation rule only evaluates the record being saved.

**Why it works:** the irreversible switch is tried in a sandbox first, access comes from the standard permission sets that carry the licence, and the payment rules that can live on one record are deployable files, while the rule that spans records lives in a flow.

