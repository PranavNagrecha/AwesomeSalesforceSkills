# Gotchas — Standard Object Quirks

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Event EndDateTime Is Required via API but Not in the UI

**What happens:** Creating an Event record via Apex or the REST API without setting `EndDateTime` throws the error *"Required fields are missing: [EndDateTime]"*. The UI does not require this field because it calculates EndDateTime from StartDateTime plus DurationInMinutes.

**When it occurs:** Any programmatic Event creation — Apex triggers, REST API calls, Data Loader imports, or Flow-created Events. The UI silently handles the calculation, but the API does not.

**How to avoid:** Always set `EndDateTime` explicitly when creating Events in code. Calculate it as `StartDateTime` plus the desired duration. Do not rely on `DurationInMinutes` alone — the API requires the explicit datetime value.

```apex
Event e = new Event();
e.Subject = 'Client Call';
e.StartDateTime = DateTime.now();
e.EndDateTime = DateTime.now().addMinutes(30); // Required via API
e.WhoId = contactId;
insert e;
```

---

## Gotcha 2: Lead Conversion Silently Drops Unmapped Custom Fields

**What happens:** When a Lead is converted using the standard `Database.convertLead()` method or the UI, any custom field on the Lead that is not explicitly mapped in Lead Field Mapping (Setup > Lead > Map Lead Fields) is lost. The data is not copied to the Contact, Account, or Opportunity. There is no warning, no error, and no audit log entry.

**When it occurs:** Every Lead conversion where custom fields exist without corresponding mappings. This is especially dangerous when a developer adds a new custom field to Lead after the initial field mapping was configured — the new field is unmapped by default.

**How to avoid:** Maintain a checklist or automated test that compares Lead custom fields against Lead Field Mapping entries. After adding any custom field to the Lead object, immediately update the field mapping. Alternatively, use a before-conversion Apex trigger to copy values to a staging object or directly to the target records.

---

## Gotcha 3: PersonAccount Triggers Fire on Both Account and Contact

**What happens:** When a PersonAccount record is inserted or updated, Apex triggers fire on both the Account object and the Contact object. This happens because a PersonAccount is internally represented as both an Account and an implicit Contact. Trigger logic on Contact that does not check `Account.IsPersonAccount` will process PersonAccount-related Contact records alongside regular Contacts.

**When it occurs:** Any org with PersonAccounts enabled. The double-firing occurs on every PersonAccount DML operation — insert, update, delete, and undelete.

**How to avoid:** In Contact triggers, add a guard clause that checks whether the Contact is the implicit Contact of a PersonAccount. Query the related Account's `IsPersonAccount` field, or check if the Contact's `AccountId` corresponds to a PersonAccount. Filter these records out of processing if your logic is intended only for standalone Contacts.

```apex
trigger ContactTrigger on Contact (before update) {
    Set<Id> accountIds = new Set<Id>();
    for (Contact c : Trigger.new) {
        if (c.AccountId != null) accountIds.add(c.AccountId);
    }
    Map<Id, Account> accts = new Map<Id, Account>(
        [SELECT Id, IsPersonAccount FROM Account WHERE Id IN :accountIds]
    );
    for (Contact c : Trigger.new) {
        if (c.AccountId != null && accts.get(c.AccountId)?.IsPersonAccount == true) {
            continue; // Skip PersonAccount-related Contacts
        }
        // Normal Contact logic here
    }
}
```

---

## Gotcha 4: Task CompletedDateTime Is Only Populated When Status = Completed

**What happens:** Developers query `CompletedDateTime` on Task expecting it to contain the date the task was finished. For Tasks that are not in "Completed" status, this field is null — even if the Task was previously completed and then reopened. The field `ActivityDate` is the due date, not the completion date, but its name misleads developers into using it as a completion indicator.

**When it occurs:** Any reporting or automation that relies on knowing when a Task was actually completed. Reopening a completed Task clears `CompletedDateTime`, so the historical completion date is lost.

**How to avoid:** If you need to track completion history, create a custom datetime field (e.g., `First_Completed_Date__c`) and populate it via a trigger that fires when Status changes to "Completed." Only write the value if the field is currently null, preserving the first completion date even if the Task is reopened and re-completed.

---

## Gotcha 5: Account Deletion Unlinks Contacts Instead of Deleting Them

**What happens:** Deleting an Account record does not cascade-delete its child Contacts. Instead, the `AccountId` field on each child Contact is set to null, creating orphaned Contact records. This behavior differs from master-detail relationships, where child deletion is automatic.

**When it occurs:** Any Account deletion — via UI, Apex, API, or Data Loader. The Account-Contact relationship is a special lookup (not master-detail), so the platform's default behavior is to preserve the Contact.

**How to avoid:** Before deleting Accounts in bulk or via automation, query for child Contacts and explicitly handle them — either delete them, reassign them to another Account, or accept the orphaning. Add a before-delete trigger on Account to enforce the desired cascade policy if your business rules require it.
