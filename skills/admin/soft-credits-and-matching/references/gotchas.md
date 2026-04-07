# Gotchas — Soft Credits and Matching Gifts (NPSP)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Soft Credit Rollup Fields Are Never Real-Time

**What happens:** After creating or modifying an `OpportunityContactRole` or `npsp__Partial_Soft_Credit__c` record, the soft credit rollup fields on the Contact and Account (`npsp__Soft_Credit_This_Year__c`, `npsp__Soft_Credit_Last_Year__c`, `npsp__Soft_Credit_Two_Years_Ago__c`, `npsp__Soft_Credit_Total__c`) remain unchanged. An admin checks the Contact immediately after saving and sees $0 or a stale value, concluding the configuration is broken.

**When it occurs:** Every time an OCR or Partial Soft Credit record is created, modified, or deleted — whether through the UI, data loader, or Apex. Even orgs configured for "Real-Time" NPSP rollups experience this lag for soft credit fields, because NPSP's real-time rollup triggers cover hard credit (primary OCR) calculations but soft credit rollups run through the batch path.

**How to avoid:** After configuring soft credit records, always trigger recalculation explicitly: NPSP Settings > Batch Processing > Recalculate Rollups, or use the Contact-level Recalculate Rollups button. Communicate this expectation to end users so they do not report false data issues. For automated integrations, schedule a rollup recalculation job to run after bulk OCR imports.

---

## Gotcha 2: Find Matched Gifts Creates Duplicate OCR and Partial_Soft_Credit__c Records

**What happens:** Running Find Matched Gifts for a Contact who has two or more donation Opportunities, each of which is linked to the same Matching Gift opportunity on the employer, results in duplicate `OpportunityContactRole` records and duplicate `npsp__Partial_Soft_Credit__c` records on the Matching Gift opportunity. Each duplicate OCR represents a separate soft credit attribution, so the employer contact's rollup total is multiplied by the number of duplicates, inflating giving history.

**When it occurs:** Specifically when: (a) one employee has given multiple times, (b) each donation is individually run through Find Matched Gifts, and (c) all donations match to the same Matching Gift opportunity. NPSP does not check whether a Matched Donor OCR already exists for that contact before creating a new one.

**How to avoid:** Before running Find Matched Gifts on multiple donations, check whether a Matched Donor OCR already exists for the employer contact on the Matching Gift opportunity. If it does, either update the existing Partial_Soft_Credit__c amount manually or delete and recreate the OCR and partial credit record to reflect the cumulative matched amount. After running Find Matched Gifts in bulk, always query for duplicate OCRs on the Matching Gift opportunity and remove extras before triggering rollup recalculation.

```sql
-- Detect duplicate Matched Donor OCRs on a Matching Gift opportunity
SELECT ContactId, Count(Id) cnt
FROM OpportunityContactRole
WHERE OpportunityId = '[matching_gift_opp_id]'
  AND Role = 'Matched Donor'
GROUP BY ContactId
HAVING Count(Id) > 1
```

---

## Gotcha 3: A Partial_Soft_Credit__c Record Missing npsp__Contact_Role_ID__c Is Silently Ignored

**What happens:** If an `npsp__Partial_Soft_Credit__c` record is created without populating `npsp__Contact_Role_ID__c` (the lookup to the corresponding OCR), NPSP does not throw a validation error. The record saves successfully. However, during rollup calculation, NPSP cannot match the partial credit record to an OCR and falls back to using the full opportunity amount for that contact's soft credit rollup. The intended partial amount is never applied.

**When it occurs:** Common in data migrations and bulk imports where OCR records and Partial_Soft_Credit__c records are inserted separately (e.g., two separate data loader operations) and the OCR IDs are not captured and written back into the partial credit records. Also occurs when Apex code creates partial credit records in the wrong order — inserting partial credits before OCRs exist.

**How to avoid:** Always create OCR records first, capture their IDs, then create `npsp__Partial_Soft_Credit__c` records with `npsp__Contact_Role_ID__c` populated. After any bulk import, run a post-load query to confirm zero partial credit records have a null `npsp__Contact_Role_ID__c`.

```sql
SELECT Id, npsp__Contact__c, npsp__Amount__c
FROM npsp__Partial_Soft_Credit__c
WHERE npsp__Contact_Role_ID__c = null
```

---

## Gotcha 4: Household Auto-Soft-Credits and Manual Soft Credit OCRs Stack

**What happens:** NPSP automatically creates soft credit OCRs for household members when a donation is made by one member of the household. If an admin then manually adds a second OCR with a soft credit role for the same household member (perhaps not realizing the auto-credit exists), that contact ends up with two OCRs for the same gift. Without a Partial_Soft_Credit__c record, both OCRs contribute the full opportunity amount to the rollup — doubling the soft credit total for that contact.

**When it occurs:** When an admin is configuring relationship-based soft credits and does not first check whether NPSP household auto-credits are already generating OCRs for household members. Also occurs after NPSP upgrades where the auto-soft-credit setting is turned on for the first time in an org that previously managed soft credits manually.

**How to avoid:** Before manually creating soft credit OCRs for a Contact, query the Opportunity's existing OCRs to check whether a household auto-credit OCR already exists for that contact. If NPSP household auto-credits are enabled and accurate, do not duplicate them manually.

---

## Gotcha 5: Matching Gift Opportunity Must Exist Before Find Matched Gifts — Button Has No Effect Otherwise

**What happens:** The Find Matched Gifts button appears on all Opportunity records regardless of whether a Matching Gift opportunity exists for the donor's employer. If no matching gift opportunity exists, clicking Find Matched Gifts returns an empty results screen or "No Matching Gifts Found" — with no error message explaining that the prerequisite opportunity is missing. Admins sometimes interpret this as a permissions issue or a bug.

**When it occurs:** Any time Find Matched Gifts is used for a donor whose employer Account does not have an open Matching Gift opportunity record. Common in orgs where the corporate giving team manages Matching Gift opportunities separately from individual gift entry staff.

**How to avoid:** Establish a process for corporate giving staff to create Matching Gift opportunities proactively for each employer matching program. Gift entry staff should check whether a Matching Gift opportunity exists on the employer Account before attempting to use Find Matched Gifts. Consider adding a quick action or list view on Account to surface open Matching Gift opportunities.
