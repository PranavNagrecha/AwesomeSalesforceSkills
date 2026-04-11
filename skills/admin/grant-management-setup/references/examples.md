# Examples — Grant Management Setup

## Example 1: Setting Up a FundingAward with Quarterly Disbursement Tranches in Nonprofit Cloud for Grantmaking

**Context:** A community foundation on Nonprofit Cloud with the Grantmaking license needs to configure a $120,000 multi-year capacity-building grant to a grantee organization, disbursed in four quarterly tranches of $30,000 each. The grants manager needs to track each payment independently and see the full disbursement schedule on the award record.

**Problem:** Without proper FundingDisbursement configuration, grants staff either create four separate FundingAward records (breaking rollup reporting) or track tranches in a spreadsheet outside Salesforce (no audit trail, no automation, no reporting integration).

**Solution:**

```
1. Create FundingAward record:
   - Grantee__c = [Grantee Account lookup]
   - AwardAmount__c = 120000
   - AwardDate__c = 2025-01-01
   - Status = Active
   - FundingProgram__c = [Capacity Building Program]

2. Create four FundingDisbursement child records on the FundingAward:
   Tranche 1: ScheduledDate = 2025-01-15, DisbursementAmount = 30000, Status = Scheduled
   Tranche 2: ScheduledDate = 2025-04-15, DisbursementAmount = 30000, Status = Draft
   Tranche 3: ScheduledDate = 2025-07-15, DisbursementAmount = 30000, Status = Draft
   Tranche 4: ScheduledDate = 2025-10-15, DisbursementAmount = 30000, Status = Draft

3. Build a Roll-Up Summary field (or Flow-based rollup) on FundingAward:
   - TotalDisbursed__c = SUM of FundingDisbursement.DisbursementAmount WHERE Status = 'Paid'
   - RemainingBalance__c = AwardAmount__c - TotalDisbursed__c

4. Build a Flow on FundingDisbursement to:
   - Notify grants manager when ScheduledDate is within 14 days and Status = Scheduled
   - Update FundingAward.Status to 'Closed' when all FundingDisbursements reach 'Paid'
```

**Why it works:** FundingDisbursement is purpose-built for tranche tracking. Each disbursement has an independent status, scheduled date, and amount field, enabling pipeline reports, payment reminders, and rollup calculations without custom objects. The parent-child relationship preserves the full award context on every tranche record.

---

## Example 2: Tracking Grant Deliverables Using FundingAwardRequirement Status Workflow

**Context:** A healthcare foundation on Nonprofit Cloud for Grantmaking requires grantees to submit a 6-month Progress Report and a Final Report before the second and final disbursement tranches are released. The grants team needs a structured way to track submission, review, and approval of each deliverable — and to block payment until requirements are met.

**Problem:** Without FundingAwardRequirement, grants teams use Chatter posts or Tasks to track deliverables. These produce no structured data, cannot be queried in SOQL, cannot gate automation, and make audit reporting impossible.

**Solution:**

```
1. At award setup, create two FundingAwardRequirement records on the FundingAward:
   Requirement 1:
     - Name = "6-Month Progress Report"
     - Type = Progress Report
     - DueDate = 2025-07-01
     - Status = Open
     - LinkedDisbursement__c = [Tranche 2 FundingDisbursement lookup]

   Requirement 2:
     - Name = "Final Report"
     - Type = Final Report
     - DueDate = 2025-12-01
     - Status = Open
     - LinkedDisbursement__c = [Tranche 4 FundingDisbursement lookup]

2. Build a Flow triggered when a grantee submits the report (e.g., via Experience Cloud
   portal or staff action):
   - Update FundingAwardRequirement.Status from Open → Submitted
   - Send email notification to grants manager for review

3. Build a Flow triggered when grants manager sets Status = Approved:
   - Update linked FundingDisbursement.Status from Draft → Scheduled
   - Log a completion timestamp

4. Add a Validation Rule on FundingDisbursement:
   - Prevents Status from moving to 'Paid' if any linked FundingAwardRequirement
     with LinkedDisbursement__c = this record has Status != 'Approved'
   - Error message: "All requirements linked to this disbursement must be Approved
     before payment can be processed."
```

**Why it works:** FundingAwardRequirement's Status field (Open → Submitted → Approved) maps directly to the review lifecycle. Linking requirements to specific disbursements enables targeted gating: only the tranches tied to unmet requirements are blocked, not the entire award. This produces an auditable, reportable, automatable deliverable tracking system with no custom objects required.

---

## Anti-Pattern: Using Separate FundingAward Records per Tranche

**What practitioners do:** Create one FundingAward record for each disbursement (e.g., "Smith Foundation Grant — Q1 2025," "Smith Foundation Grant — Q2 2025") to represent each payment tranche separately.

**What goes wrong:**
- Total award amount cannot be reported as a single figure — grants pipeline reports show 4x the actual committed funding.
- FundingAwardRequirement records must be duplicated across all four "award" records, breaking requirement tracking.
- Relationship to the funder Account becomes ambiguous — four records for one grant creates noise in the funder's related list.
- Roll-up reporting on "Total Awarded to Grantee" double- or quadruple-counts the grant.

**Correct approach:** Create one FundingAward per grant agreement. Use FundingDisbursement child records to represent each tranche. The parent-child model is the correct data structure for scheduled payment plans.
