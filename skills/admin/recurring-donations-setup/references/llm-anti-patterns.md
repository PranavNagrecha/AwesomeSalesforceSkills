# LLM Anti-Patterns — Recurring Donations Setup

Common mistakes AI coding assistants make when generating or advising on Recurring Donations Setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming All Future Installments Exist as Opportunity Records

**What the LLM generates:** SOQL queries or Apex logic that fetches a list of future pledged Opportunities and expects to find one per upcoming month (e.g., 12 records for a monthly recurring donation):

```sql
-- Wrong: assumes 12 future Opportunities exist
SELECT Id, CloseDate, Amount
FROM Opportunity
WHERE npe03__Recurring_Donation__c = :rdId
AND StageName = 'Pledged'
AND IsClosed = false
ORDER BY CloseDate ASC
```

**Why it happens:** The legacy NPSP recurring donations model created up to 12 future pledged Opportunities at once. Training data from pre-2021 NPSP documentation or legacy org setups describes this behavior. LLMs pattern-match to this legacy behavior and apply it to ERD orgs incorrectly.

**Correct pattern:**

```text
In Enhanced Recurring Donations (ERD, default since March 2021):
- Exactly ONE open pledged Opportunity exists per active Recurring Donation
- Future installment dates are projections calculated from npe03__RecurringDonationSchedule__c
- To get the next installment: query the single open pledged Opportunity
- To get future projections: derive from the active schedule record's period/frequency

The above query is valid in ERD but will return only 1 record, not 12.
Code that iterates over this list must handle a list of size 1.
```

**Detection hint:** Look for loops or aggregations over open pledged Opportunities per Recurring Donation that expect count > 1. Any comment referencing "all future installments" or "upcoming 12 months of Opportunities" is a signal.

---

## Anti-Pattern 2: Treating the Upcoming Installments UI as a Record-Backed List

**What the LLM generates:** Instructions telling practitioners to "edit the future Opportunities shown in the Upcoming Installments tab" or advice that "you can see and manage all upcoming installment records from the Upcoming Installments related list":

```text
-- Wrong guidance:
"To change the amount for a future installment, find the Opportunity
in the Upcoming Installments list and edit it directly."
```

**Why it happens:** The Upcoming Installments UI looks like a related list of records, similar to how Opportunities appear in the standard related list. LLMs assume it is a standard related list backed by Opportunity records.

**Correct pattern:**

```text
The Upcoming Installments related list on a Recurring Donation is a
schedule projection UI, NOT a list of Opportunity records.

It calculates future dates from the active npe03__RecurringDonationSchedule__c record.
Edits to actual Opportunity records (amount, close date) are NOT reflected here.

To change what this UI shows:
- Modify the active npe03__RecurringDonationSchedule__c record
- Use the schedule change interface on the Recurring Donation with an Effective Date
```

**Detection hint:** Any guidance that says to edit installments "in the Upcoming Installments list" or "from the Upcoming Installments tab" — that list is read-only and projection-based.

---

## Anti-Pattern 3: Editing Recurring Donation Amount Directly Instead of Using Effective Date

**What the LLM generates:** Instructions to update the Amount field on the Recurring Donation record directly to change future installment amounts:

```apex
// Wrong: direct field edit without Effective Date
rd.npe03__Amount__c = 150;
update rd;
```

**Why it happens:** Editing a record's amount field is the natural intuition for "change the amount." LLMs default to direct field updates because that is the pattern for most Salesforce record updates. The Effective Date mechanism is NPSP-specific and not present in standard Salesforce.

**Correct pattern:**

```text
To change a Recurring Donation's amount for future installments:

1. Use the schedule change interface (NPSP UI) or create a new
   npe03__RecurringDonationSchedule__c record via Apex with:
   - Updated npe03__Amount__c
   - A future npe03__StartDate__c (Effective Date)
   - Status__c = 'Active'
2. NPSP will deactivate the old schedule record automatically
   (via UI) or you must set the old record to Inactive (via Apex)

Direct field edits to npe03__Amount__c on the Recurring Donation
may be overwritten by the nightly batch recalculation. Always
use the schedule mechanism for persistent changes.
```

**Detection hint:** Apex or Flow that writes directly to `npe03__Amount__c` on a Recurring Donation without also creating or updating a `npe03__RecurringDonationSchedule__c` record is suspect.

---

## Anti-Pattern 4: Querying npe03__RecurringDonationSchedule__c Without a Status Filter

**What the LLM generates:** Queries or Apex that fetches schedule records for a Recurring Donation without filtering by Active status:

```sql
-- Wrong: returns all schedule records including historical inactive ones
SELECT Id, npe03__Amount__c, npe03__InstallmentPeriod__c
FROM npe03__RecurringDonationSchedule__c
WHERE npe03__RecurringDonation__c = :rdId
```

**Why it happens:** LLMs commonly omit filters when generating "get related records" queries. The schedule record history behavior — where old schedules are kept as Inactive rather than deleted — is NPSP-specific and not widely represented in training data.

**Correct pattern:**

```sql
-- Correct: filter to only the active (current) schedule
SELECT Id, npe03__Amount__c, npe03__InstallmentPeriod__c,
       npe03__InstallmentFrequency__c, npe03__StartDate__c
FROM npe03__RecurringDonationSchedule__c
WHERE npe03__RecurringDonation__c = :rdId
AND Status__c = 'Active'
ORDER BY npe03__StartDate__c DESC
LIMIT 1
```

**Detection hint:** Any query against `npe03__RecurringDonationSchedule__c` that lacks a `Status__c = 'Active'` filter or returns multiple records and treats them as the single current schedule.

---

## Anti-Pattern 5: Assuming Legacy Recurring Donation Behavior in ERD Orgs

**What the LLM generates:** Guidance referencing the legacy NPSP recurring donation behavior — such as "NPSP creates 12 installment Opportunities per year," "edit installments using the legacy recurring donation scheduler," or "use npe03__Installments__c to count future pledges":

```text
-- Wrong (legacy-model guidance):
"NPSP automatically creates one Opportunity per installment period for
the next 12 months. You can view and edit all of them on the Recurring
Donation record."
```

**Why it happens:** A large portion of NPSP documentation and community content predates March 2021 when ERD was released. Legacy behavior is extensively documented and LLMs weight it heavily. ERD guidance is newer and may be underrepresented.

**Correct pattern:**

```text
Verify which model the org is using before giving any guidance:
- ERD (default since March 2021): 1 future Opportunity, schedule-driven projections
- Legacy (pre-2021 default, still possible in older orgs): up to 12 future Opportunities

In ERD:
- npe03__RecurringDonationSchedule__c drives all installment generation
- One open pledged Opportunity per active Recurring Donation
- Upcoming Installments UI = schedule projection (not Opportunity records)
- Status transitions are batch-driven with configurable day thresholds

Never apply legacy model assumptions to an ERD org.
```

**Detection hint:** Any mention of "12 installments," "all upcoming Opportunities," or the legacy scheduler in the context of a post-March 2021 NPSP org. Ask which mode the org uses before generating advice.

---

## Anti-Pattern 6: Ignoring the Nightly Batch as a Dependency

**What the LLM generates:** Advice that implies status changes, rollup recalculations, and new Opportunity creation happen immediately or synchronously after a Recurring Donation is saved:

```text
-- Wrong assumption:
"After you close the April Opportunity as Closed-Won, the May
Opportunity will be created and the Total Paid Amount will update."
```

**Why it happens:** Most Salesforce trigger and automation behavior is synchronous or near-real-time. LLMs default to synchronous assumptions for record changes. The NPSP nightly batch architecture is an exception that is easy to overlook.

**Correct pattern:**

```text
In NPSP ERD, the following operations are batch-driven (NOT real-time):
- Creation of the next installment Opportunity after the current one is closed
- Recalculation of Total Paid Amount on the Recurring Donation
- Recalculation of Number of Paid Installments on the Recurring Donation
- Status transitions (Active → Lapsed → Closed) based on days-unpaid thresholds

These changes happen when the NPSP recurring donations batch runs,
which is typically scheduled nightly.

If immediate recalculation is needed:
- Navigate to NPSP Settings > Recurring Donations > Recalculate
- Or trigger the batch class programmatically: Database.executeBatch(new RD2_OpportunityEvaluationService.Batch())
```

**Detection hint:** Any response that says "the next Opportunity will be created" or "the total will update" without mentioning the nightly batch.
