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
