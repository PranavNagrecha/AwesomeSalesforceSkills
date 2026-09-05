# Examples: Data Import and Management

---

## Example: Choosing the Right Tool for a 2.5 Million Row Cutover

**Scenario:** A legacy CRM is being retired. The project must load 400,000 Accounts, 1.2 million Contacts, and 900,000 historical Cases over a weekend.

**Decision:**
- `Data Import Wizard` -> rejected: too much volume, no serious retry control
- `Data Loader` -> acceptable for rehearsal and smaller admin fixes, not ideal for the full cutover
- `Bulk API 2.0` -> selected for production cutover

**Load order:**
1. Accounts upserted by `Legacy_Account_Id__c`
2. Contacts upserted by `Legacy_Contact_Id__c`, matching Account via `Legacy_Account_Id__c`
3. Cases inserted last, matching both Contact and Account using exported Salesforce IDs

**Why this works:** Parent objects exist before child rows arrive, every file can be rerun idempotently, and reconciliation can be done by External ID instead of by row count alone.

**Allocation budget, worked before the window is booked.** Bulk API 2.0 creates one batch per 10,000
records, and the 15,000-batch / 150,000,000-record allocations are per rolling 24 hours and shared
between Bulk API and Bulk API 2.0 (App Limits Cheat Sheet):

```text
Accounts    400,000 rows / 10,000 =    40 batches
Contacts  1,200,000 rows / 10,000 =   120 batches
Cases       900,000 rows / 10,000 =    90 batches
Rehearsal + one full re-run       = x 3
                                    -------------
                                      750 batches   of 15,000 allowed  -> 5% used
Records moved 2,500,000 x 3       = 7,500,000       of 150,000,000     -> 5% used

File sizing (Bulk API 2.0): 150 MB per job after base64, which inflates the upload
by roughly 50%, so keep each uploaded CSV under 100 MB.
  Contacts 1.2M rows x ~180 bytes = ~216 MB  ->  split into 3 jobs of 400,000
```

The allocation is not the constraint here; **file size is**, and it is what dictates that the Contact
load is three jobs rather than one. Confirm the split before the runbook is signed off, because
discovering it mid-window turns one job into three unplanned ones.

---

## Example: Upsert File with Safe Match Key

**Goal:** Update Contacts from a source system without creating duplicates.

```csv
Legacy_Contact_Id__c,FirstName,LastName,Email,Account_Legacy_Id__c
SRC-1001,Ana,Lopez,ana.lopez@example.org,ACCT-22
SRC-1002,Devon,Price,devon.price@example.org,ACCT-31
SRC-1003,Kim,Tran,kim.tran@example.org,ACCT-31
```

**Upsert key:** `Legacy_Contact_Id__c`

**Anti-pattern:** matching on Email alone when email can be blank, shared, or changed by users.

**Pre-load checks:**
- No blank `Legacy_Contact_Id__c` values
- No duplicates in the source file for `Legacy_Contact_Id__c`
- Parent Accounts already loaded or resolvable by External ID

---

## Example: Post-Load Reconciliation Query

**Objective:** Confirm the cutover loaded the expected records and did not silently skip data.

```soql
-- Compare source-system IDs to Salesforce after the load
SELECT COUNT()
FROM Contact
WHERE Legacy_Contact_Id__c != null

-- Spot-check failed rows by source key
SELECT Id, Legacy_Contact_Id__c, Email, AccountId
FROM Contact
WHERE Legacy_Contact_Id__c IN ('SRC-1001', 'SRC-1002', 'SRC-1003')
ORDER BY Legacy_Contact_Id__c
```

**Use this with:**
- source row count
- success file count
- error file count
- target-org `COUNT()` result

If those four numbers do not reconcile cleanly, the load is not done.
