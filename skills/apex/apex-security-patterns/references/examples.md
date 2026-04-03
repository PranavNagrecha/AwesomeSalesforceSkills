# Examples — Apex Security Patterns

## Example 1: `inherited sharing` Service With Secure Read And Write

**Context:** An Aura-enabled controller lets users update `Case` records they can see, but only on fields they are allowed to edit.

**Problem:** A simple `with sharing` controller still does not protect field updates, and the service layer’s sharing intent is unclear.

**Solution:**

```apex
public inherited sharing class CaseUpdateService {

    public static void updateCaseSubject(Id caseId, String newSubject) {
        Case existingCase = [
            SELECT Id, Subject
            FROM Case
            WHERE Id = :caseId
            WITH USER_MODE
        ];

        existingCase.Subject = newSubject;

        SObjectAccessDecision decision = Security.stripInaccessible(
            AccessType.UPDATABLE,
            new List<Case>{existingCase}
        );

        update (Case) decision.getRecords()[0];
    }
}

public with sharing class CaseUpdateController {
    @AuraEnabled
    public static void renameCase(Id caseId, String newSubject) {
        CaseUpdateService.updateCaseSubject(caseId, newSubject);
    }
}
```

**Why it works:** The controller is explicit about record sharing, the service inherits the caller’s sharing context, the read uses user-mode enforcement, and the write sanitizes fields before DML.

---

## Example 2: Allowlisted Dynamic Field Access

**Context:** A reusable export service lets callers request a subset of fields.

**Problem:** Accepting arbitrary field names from callers creates both security and stability risk.

**Solution:**

```apex
public inherited sharing class AccountExportService {
    private static final Set<String> ALLOWED_FIELDS =
        new Set<String>{'Id', 'Name', 'Industry', 'AnnualRevenue'};

    public static List<Account> exportAccounts(List<String> requestedFields) {
        List<String> selected = new List<String>();
        for (String fieldName : requestedFields) {
            if (ALLOWED_FIELDS.contains(fieldName)) {
                selected.add(fieldName);
            }
        }

        if (selected.isEmpty()) {
            throw new IllegalArgumentException('No permitted fields requested.');
        }

        String soql =
            'SELECT ' + String.join(selected, ',') +
            ' FROM Account WITH USER_MODE';
        return Database.query(soql);
    }
}
```

**Why it works:** The dynamic query surface is constrained to an allowlist and the read path stays in explicit user context.

---

## Anti-Pattern: `without sharing` Controller With Direct DML

**What practitioners do:** They declare a top-level controller `without sharing` to "fix" an access problem and then perform direct updates.

```apex
public without sharing class AccountAdminController {
    @AuraEnabled
    public static void closeAccount(Id accountId) {
        Account accountRecord = [SELECT Id, Status__c FROM Account WHERE Id = :accountId];
        accountRecord.Status__c = 'Closed';
        update accountRecord;
    }
}
```

**What goes wrong:** The class widens record visibility for all callers and performs no CRUD/FLS sanitization on the write.

**Correct approach:** Keep elevation narrow and documented, and secure both the query and DML paths explicitly.
