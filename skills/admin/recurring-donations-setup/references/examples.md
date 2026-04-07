# Examples — Recurring Donations Setup

## Example 1: Confirming ERD Is Active and Verifying Single-Installment Behavior

**Context:** A nonprofit migrated to NPSP several years before March 2021, then upgraded NPSP but never explicitly ran the ERD migration. Their recurring donations batch has been running, but reports show each active recurring donation has 12 open pledged Opportunities — a sign they are still on the legacy model.

**Problem:** Without confirming ERD status, any configuration guidance given will be wrong. Legacy model behavior (12 future Opportunities) is fundamentally different from ERD (1 future Opportunity). Automations, reports, and schedule-change logic built for one model will break on the other.

**Solution:**

```text
Navigation path to verify:
Setup > NPSP Settings > Recurring Donations

Look for:
- "Enhanced Recurring Donations" toggle or status indicator
- If legacy: a "Migrate to Enhanced Recurring Donations" button will be present
- If ERD: the settings page will show installment configuration options specific to ERD

After confirming ERD, verify a test Recurring Donation:
1. Create a new Recurring Donation (Amount=100, Period=Monthly)
2. Run the NPSP RD batch or wait for the nightly run
3. Navigate to the Recurring Donation > Related > Opportunities
4. Confirm exactly ONE open pledged Opportunity exists (not 12)
5. Navigate to the Upcoming Installments related list — confirm it shows
   projected future dates (e.g., 12 months ahead) NOT backed by actual records
```

**Why it works:** ERD by design limits open pledged Opportunities to one at a time. The single record represents the next scheduled payment. Projected future dates are calculated from the active `npe03__RecurringDonationSchedule__c` record and displayed in the UI without creating Opportunity records for each date.

---

## Example 2: Applying a Future-Dated Amount Increase

**Context:** A major donor calls in to increase their monthly recurring gift from $100 to $150 starting next month. The current month's installment Opportunity is already open and should remain at $100.

**Problem:** A practitioner unfamiliar with ERD opens the Recurring Donation and edits the Amount field directly to $150. NPSP immediately updates the active schedule record but the existing open Opportunity may also be recalculated by the nightly batch — or the practitioner manually edits the Opportunity amount, which will be overwritten. Neither approach is reliable.

**Solution:**

```text
Correct approach using Effective Date:

1. Open the Recurring Donation record
2. Click "Edit" or the schedule change button (varies by NPSP version/UI)
3. Set New Amount = 150
4. Set Effective Date = first day of next month
   (Example: if today is April 15, set Effective Date = May 1)
5. Save the change

What NPSP does automatically:
- Creates a new npe03__RecurringDonationSchedule__c record:
    Amount: 150, Effective Date: May 1, Status: Active
- Sets the old schedule record to Inactive:
    Amount: 100, Status: Inactive
- The current open Opportunity (for April) retains Amount = 100
- The next Opportunity created after May 1 will have Amount = 150

Verification:
- Query: SELECT Id, npe03__Amount__c, Status__c, StartDate__c
         FROM npe03__RecurringDonationSchedule__c
         WHERE npe03__RecurringDonation__c = '[RD_ID]'
  Expect: 2 records — one Active at 150, one Inactive at 100
- Confirm current open Opportunity still shows Amount = 100
```

**Why it works:** The Effective Date mechanism ensures the schedule change is applied prospectively without touching the current open Opportunity. NPSP's batch respects the Effective Date and uses the appropriate schedule record when creating each new installment Opportunity.

---

## Example 3: Diagnosing Why the Upcoming Installments UI Does Not Reflect a Manual Edit

**Context:** A data entry staff member manually changed the Close Date on a future pledged Opportunity from April 30 to May 15 to accommodate a donor's request. When they open the Recurring Donation and look at the Upcoming Installments UI, the projected dates still show April 30.

**Problem:** The Upcoming Installments related list is a schedule-driven projection, not a live list of Opportunity records. The manual edit is invisible to the UI because the underlying `npe03__RecurringDonationSchedule__c` record was not changed.

**Solution:**

```text
Explanation to give the practitioner:

The Upcoming Installments UI calculates projected dates from the active
npe03__RecurringDonationSchedule__c record. It does NOT read Close Dates
from existing Opportunity records.

To change what the UI shows, the schedule must be updated:
- If the intent is to shift ALL future installments by 15 days,
  update the Day of Month on the schedule record.
- If the intent is to shift ONLY one installment, the platform does not
  provide a native single-installment date override via the UI.

Important: The manual edit to the Opportunity Close Date IS saved on the
record — it is just not reflected in the Upcoming Installments projection.
The nightly batch will also recalculate based on the schedule, and may
overwrite the manually edited Close Date on the next run.

For a reliable one-time deferral:
1. Close the current open Opportunity as Closed-Lost (or delete it)
2. Manually create a new Opportunity linked to the Recurring Donation
   with the desired Close Date
   Note: This Opportunity is "orphaned" from the schedule — the batch will
   create the NEXT installment based on the schedule after this one is closed.
   Communicate this to the practitioner so they understand the tradeoff.
```

**Why it works:** Understanding the projection-vs-record distinction prevents practitioners from spending time trying to make the UI reflect manual Opportunity edits. It also prevents surprise overwrites by the nightly batch.

---

## Anti-Pattern: Querying All Future Installments via SOQL and Expecting 12 Records

**What practitioners do:** Write a SOQL query to fetch all future pledged Opportunities for a Recurring Donation and expect to find 11 or 12 records (one per upcoming month):

```sql
-- WRONG assumption in ERD orgs:
SELECT Id, CloseDate, Amount
FROM Opportunity
WHERE npe03__Recurring_Donation__c = :rdId
AND IsClosed = false
AND StageName = 'Pledged'
```

**What goes wrong:** In an ERD org, this query returns exactly ONE record. Any code, report, or integration that iterates over "all future installments" expecting 12 records will silently process only one, produce wrong totals, or fail logic branches that depend on list length.

**Correct approach:** Acknowledge the ERD constraint and redesign the logic:

```text
In ERD, future installment projections live in npe03__RecurringDonationSchedule__c,
not in Opportunity records. To work with future installment dates:

- For the NEXT installment: query the one open pledged Opportunity
- For ALL projected future dates: read from the Upcoming Installments
  UI data or calculate from the active schedule record directly
- For historical paid installments: query Closed-Won Opportunities
  linked to the Recurring Donation

Never assume 12 open pledged Opportunities per active Recurring Donation in ERD.
```
