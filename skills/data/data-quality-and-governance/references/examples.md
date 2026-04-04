# Examples — Data Quality and Governance

## Example 1: Financial Services Org — Field-Level Audit Trail for Regulatory Compliance

**Context:** A financial services firm uses Salesforce to manage client portfolios. Regulatory requirements (internal compliance + SEC Rule 17a-4) mandate that all changes to `AUM_Amount__c`, `Risk_Profile__c`, `KYC_Status__c`, and the Account Owner field on all Client Account records be retained for 7 years and be queryable on demand.

**Problem:** Standard field history only retains 18 months. After a compliance audit, the firm discovered that field change history older than 18 months had been automatically purged by Salesforce, leaving no audit trail for a period under regulatory review.

**Solution:**

Step 1 — Enable Shield Field Audit Trail on the org (requires Salesforce Shield license).

Step 2 — Configure field history tracking for `AUM_Amount__c`, `Risk_Profile__c`, `KYC_Status__c`, and `OwnerId` on the `Client_Account__c` object (4 of the 20-field limit used).

Step 3 — Query historical changes via `FieldHistoryArchive` for long-range audit pulls:

```soql
SELECT ParentId, FieldHistoryType, Field, OldValue, NewValue,
       CreatedById, CreatedDate
FROM FieldHistoryArchive
WHERE ParentId = '001...'
  AND Field IN ('AUM_Amount__c', 'Risk_Profile__c', 'KYC_Status__c', 'OwnerId')
ORDER BY CreatedDate ASC
```

Step 4 — For the initial value gap (field history does not record the value set at record creation), implement an Apex trigger on `Client_Account__c` insert that writes a `Field_Audit_Entry__c` record capturing the initial values:

```apex
trigger ClientAccountAudit on Client_Account__c (after insert) {
    List<Field_Audit_Entry__c> entries = new List<Field_Audit_Entry__c>();
    for (Client_Account__c rec : Trigger.new) {
        entries.add(new Field_Audit_Entry__c(
            Parent_Record_Id__c = rec.Id,
            Field_Name__c       = 'AUM_Amount__c',
            New_Value__c        = String.valueOf(rec.AUM_Amount__c),
            Change_Type__c      = 'Initial Value',
            Changed_By__c       = UserInfo.getUserId(),
            Change_Timestamp__c = System.now()
        ));
        // Repeat for other tracked fields
    }
    insert entries;
}
```

**Why it works:** Shield Field Audit Trail extends retention beyond the 18-month standard limit and stores data in `FieldHistoryArchive` which is queryable via SOQL. The trigger pattern fills the platform gap where initial creation values are not recorded in the standard history mechanism.

---

## Example 2: GDPR Right-to-Erasure Request Workflow

**Context:** A European B2C company uses Salesforce Service Cloud. A customer submits a formal GDPR right-to-erasure request. The Contact record has 3 open Cases, 12 closed Activities, and is referenced on 2 Opportunity records. Hard-deleting the Contact would orphan Cases and Activities or fail with a referential integrity error.

**Problem:** The team initially attempted to hard-delete the Contact, which failed because of related records. A developer then proposed deleting all related records first — which would have destroyed legitimate business records.

**Solution:**

Step 1 — Validate the request and confirm identity in the `Data_Erasure_Log__c` custom object.

Step 2 — Anonymize PII fields on the Contact record (do not delete):

```apex
public static void anonymizeContact(Id contactId) {
    String token = 'ERASED-' + contactId;
    Contact c = [
        SELECT Id FROM Contact WHERE Id = :contactId LIMIT 1
    ];
    c.FirstName         = 'ERASED';
    c.LastName          = token;
    c.Email             = token + '@erasure.invalid';
    c.Phone             = '0000000000';
    c.MobilePhone       = null;
    c.MailingStreet     = null;
    c.MailingCity       = null;
    c.MailingState      = null;
    c.MailingPostalCode = null;
    c.MailingCountry    = null;
    c.Birthdate         = null;
    c.Description       = 'Record anonymized per GDPR erasure request.';
    update c;
}
```

Step 3 — Anonymize PII in related records where legally required (e.g., Case `Subject` if it contains PII, email message bodies if accessible).

Step 4 — Log the completion in `Data_Erasure_Log__c`:

```apex
insert new Data_Erasure_Log__c(
    Contact_Id__c    = contactId,
    Erasure_Date__c  = Date.today(),
    Requested_By__c  = requesterId,
    Completed_By__c  = UserInfo.getUserId(),
    Status__c        = 'Completed'
);
```

Step 5 — If the Contact has no legally required related records (open Cases, Opportunities), soft-delete the anonymized Contact record to move it to the Recycle Bin. After 15 days it is permanently purged. If related records exist, leave the anonymized record in place.

**Why it works:** Anonymization preserves referential integrity while rendering the personal data non-identifiable. The erasure log provides a compliance-auditable record of every erasure action. The `@erasure.invalid` email domain is in an IANA-reserved namespace, ensuring the token cannot be a real email address.

---

## Example 3: Migration Load with Validation Rule Bypass

**Context:** A Salesforce org has 15 active validation rules on the `Opportunity` object. An ETL team is loading 500,000 historical Opportunity records from a legacy CRM. The source data is clean but does not always satisfy the conditional validation rules designed for new user-entered records (e.g., `Close_Reason__c` required when `Stage = Closed Won`, but historical records predate this field).

**Problem:** The initial load attempt fails with validation errors on roughly 40% of records, halting the migration.

**Solution:**

Step 1 — Create a Custom Permission: `Bypass_Validation_Rules`.

Step 2 — Update each validation rule formula to wrap the existing logic:

```
// Before:
AND(ISPICKVAL(StageName, 'Closed Won'), ISBLANK(Close_Reason__c))

// After:
AND(
    NOT($Permission.Bypass_Validation_Rules),
    ISPICKVAL(StageName, 'Closed Won'),
    ISBLANK(Close_Reason__c)
)
```

Step 3 — Create a Permission Set `Migration_Integration_PS`, add `Bypass_Validation_Rules` Custom Permission, assign to the integration/migration user only.

Step 4 — Run the migration load using the migration user. All 15 validation rules are bypassed because `$Permission.Bypass_Validation_Rules` evaluates to `true` for that user.

Step 5 — After migration, revoke the Permission Set from the migration user. Validation rules resume normal enforcement.

**Why it works:** Custom Permission bypasses are auditable (who has the permission, when it was assigned/revoked), granular (only specific users), and reversible without touching the validation rule metadata itself. Profile-based bypasses (`$Profile.Name = 'System Administrator'`) are too broad and remain permanently active.

---

## Anti-Pattern: Using Field History on Formula Fields

**What practitioners do:** Enable field history tracking on a formula field (e.g., a `Calculated_Revenue__c` formula field) expecting to see when the calculated value changes.

**What goes wrong:** The platform silently ignores history tracking on formula fields — no error is thrown, but no history is ever recorded. The practitioner sees zero rows in `XxxHistory` for that field and spends time debugging triggers and workflow rules before discovering the root cause.

**Correct approach:** Track history on the source fields that the formula references (e.g., `Amount`, `Discount__c`). Calculate the formula result from the historical source values if a point-in-time formula value is needed for audit purposes. Alternatively, use a separate stored field (not a formula) populated by a trigger or Flow, and track history on that stored field.

---

## Anti-Pattern: Duplicate Rules in Alert Mode for Critical Objects

**What practitioners do:** Configure Duplicate Rules in Alert mode (not Block) for Account and Contact to avoid "disrupting users."

**What goes wrong:** Users click through the duplicate warning without reviewing the flagged record. Within months the org accumulates thousands of duplicate Accounts and Contacts. Marketing campaign sends go to duplicated contacts. Sales reps work from different Account records for the same customer. A data deduplication project to clean the backlog requires a third-party tool and weeks of effort.

**Correct approach:** Use Block mode for Account and Contact from the start. Use Alert mode only on low-stakes objects, or during a short validation period (1–2 weeks) before switching to Block. Communicate the change to users with training on how to search before creating new records.
