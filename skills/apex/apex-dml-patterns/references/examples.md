# Examples — Apex DML Patterns

## Example 1: Bulk insert with partial success and error logging

**Context:** A nightly integration job reads records from an external feed and inserts them as Contacts in Salesforce. Some rows may have validation errors (e.g., missing required fields). The job must insert all valid rows and log failures without stopping.

**Problem:** Using the DML statement `insert contacts` throws `DmlException` on the first invalid row and rolls back all successfully prepared rows, including valid ones.

**Solution:**

```apex
public class ContactImportJob {
    public static void importContacts(List<FeedRow> feedRows) {
        List<Contact> contacts = new List<Contact>();
        for (FeedRow row : feedRows) {
            contacts.add(new Contact(
                LastName = row.lastName,
                Email    = row.email,
                Phone    = row.phone
            ));
        }

        List<Database.SaveResult> results = Database.insert(contacts, false);

        List<ImportError__c> errors = new List<ImportError__c>();
        for (Integer i = 0; i < results.size(); i++) {
            if (!results[i].isSuccess()) {
                String msgs = '';
                for (Database.Error err : results[i].getErrors()) {
                    msgs += err.getMessage() + ' [' + err.getStatusCode() + ']; ';
                }
                errors.add(new ImportError__c(
                    ExternalId__c = feedRows[i].externalId,
                    ErrorMessage__c = msgs
                ));
            }
        }
        if (!errors.isEmpty()) {
            Database.insert(errors, false); // log errors — partial success here too
        }
    }
}
```

**Why it works:** `Database.insert(contacts, false)` commits each valid row independently. Failed rows are captured in `SaveResult.getErrors()` and written to an error log object without blocking the successful rows.

---

## Example 2: DML with assignment rule and duplicate suppression via DMLOptions

**Context:** A lead capture integration inserts Leads that must be assigned via the active default assignment rule, and must skip duplicate checking to avoid blocking the integration user.

**Problem:** A plain `insert leads` call does not fire assignment rules, and without duplicate suppression the insert may fail on a `DUPLICATES_DETECTED` error.

**Solution:**

```apex
Database.DMLOptions opts = new Database.DMLOptions();
opts.assignmentRuleHeader.useDefaultRule = true;
opts.duplicateRuleHeader.allowSave = true;
opts.optAllOrNone = false;

List<Lead> leads = buildLeadsFromWebhook(inboundData);
List<Database.SaveResult> results = Database.insert(leads, opts);

for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) {
        logLeadError(leads[i], results[i].getErrors());
    }
}
```

**Why it works:** `DMLOptions.assignmentRuleHeader.useDefaultRule = true` fires the default lead assignment rule on insert. `duplicateRuleHeader.allowSave = true` bypasses duplicate rules that would block the integration, without permanently disabling org-wide duplicate rules.

---

## Anti-Pattern: Calling insert inside a loop

**What practitioners do:**
```apex
for (Account acc : accountList) {
    insert acc; // DML inside loop
}
```

**What goes wrong:** Each loop iteration consumes 1 DML operation. With 151 accounts, this exceeds the 150-operation limit and throws `LimitException: Too many DML statements: 151`. The exception is uncatchable and terminates the transaction.

**Correct approach:**
```apex
insert accountList; // single DML operation for entire list
```

Bulk all DML into a single statement outside the loop. If partial success is needed, use `Database.insert(accountList, false)`.
