# LLM Anti-Patterns — Exception Handling

Common mistakes AI coding assistants make when generating or advising on Apex exception handling.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Swallowing exceptions with an empty catch block

**What the LLM generates:**

```apex
try {
    update accounts;
} catch (DmlException e) {
    System.debug('Error: ' + e.getMessage());
    // Execution continues as if nothing happened
}
```

**Why it happens:** LLMs wrap code in try/catch to prevent unhandled exceptions, but the catch block only logs to `System.debug`. The caller never knows the update failed, records are silently not saved, and the debug log may not even be monitored.

**Correct pattern:**

```apex
try {
    update accounts;
} catch (DmlException e) {
    // Log for operational visibility
    LogService.logError('AccountService.save', e);
    // Re-throw or return a meaningful error to the caller
    throw new AccountService.SaveException(
        'Failed to save accounts: ' + e.getDmlMessage(0), e
    );
}
```

**Detection hint:** `catch\s*\(.*Exception` blocks that contain only `System.debug` and no `throw`, no error return, and no logging to a durable store.

---

## Anti-Pattern 2: Catching generic Exception instead of specific exception types

**What the LLM generates:**

```apex
try {
    Account a = [SELECT Id FROM Account WHERE Id = :accountId];
    update a;
    HttpResponse res = new Http().send(req);
} catch (Exception e) {
    System.debug('Something went wrong: ' + e.getMessage());
}
```

**Why it happens:** LLMs use `catch (Exception e)` as a universal safety net. This catches `QueryException`, `DmlException`, `CalloutException`, `NullPointerException`, and `LimitException` identically — losing the ability to handle each failure mode appropriately (retry callouts, report DML field errors, etc.).

**Correct pattern:**

```apex
try {
    Account a = [SELECT Id FROM Account WHERE Id = :accountId];
    update a;
} catch (QueryException qe) {
    throw new AuraHandledException('Account not found');
} catch (DmlException de) {
    throw new AuraHandledException('Save failed: ' + de.getDmlMessage(0));
}

try {
    HttpResponse res = new Http().send(req);
} catch (CalloutException ce) {
    LogService.logError('ExternalApi', ce);
    throw new AuraHandledException('External service unavailable');
}
```

**Detection hint:** `catch\s*\(\s*Exception\s+` — catching the base `Exception` class instead of specific subtypes.

---

## Anti-Pattern 3: Throwing AuraHandledException with the raw system exception message

**What the LLM generates:**

```apex
@AuraEnabled
public static void saveRecord(Account a) {
    try {
        update a;
    } catch (DmlException e) {
        throw new AuraHandledException(e.getMessage());
        // Exposes: "FIELD_CUSTOM_VALIDATION_EXCEPTION, [...], [Status__c]"
    }
}
```

**Why it happens:** LLMs pass the raw exception message to `AuraHandledException`. This exposes internal field names, validation rule messages, and stack traces to the UI — potentially leaking sensitive schema details to end users.

**Correct pattern:**

```apex
@AuraEnabled
public static void saveRecord(Account a) {
    try {
        update a;
    } catch (DmlException e) {
        // Log the full exception internally
        LogService.logError('AccountController.saveRecord', e);
        // Return a user-friendly message
        AuraHandledException ahe = new AuraHandledException('Unable to save the account. Please check your input.');
        ahe.setMessage('Unable to save the account. Please check your input.');
        throw ahe;
    }
}
```

**Detection hint:** `throw new AuraHandledException\(e\.getMessage\(\)\)` — raw exception messages exposed to the UI.

---

## Anti-Pattern 4: Not using Database.SaveResult for partial DML success in bulk operations

**What the LLM generates:**

```apex
public void processAccounts(List<Account> accounts) {
    try {
        update accounts; // All or nothing — one bad record fails all 200
    } catch (DmlException e) {
        // Cannot tell which records succeeded
        throw new AuraHandledException('Update failed');
    }
}
```

**Why it happens:** LLMs use standard `update` which is all-or-nothing. In bulk operations (triggers, batch), one bad record rolls back the entire set. The catch block cannot report which records failed.

**Correct pattern:**

```apex
public void processAccounts(List<Account> accounts) {
    List<Database.SaveResult> results = Database.update(accounts, false);
    List<String> errors = new List<String>();
    for (Integer i = 0; i < results.size(); i++) {
        if (!results[i].isSuccess()) {
            for (Database.Error err : results[i].getErrors()) {
                errors.add(accounts[i].Id + ': ' + err.getMessage());
            }
        }
    }
    if (!errors.isEmpty()) {
        LogService.logBulkErrors('AccountService', errors);
    }
}
```

**Detection hint:** `update ` or `insert ` (standard DML) in methods that process lists from triggers or batch — should be `Database.update(records, false)`.

---

## Anti-Pattern 5: Using try/catch around the entire trigger handler instead of per-record error handling

**What the LLM generates:**

```apex
public void afterInsert(List<Account> newAccounts) {
    try {
        // All logic for all records in one try block
        enrichAccounts(newAccounts);
        createChildRecords(newAccounts);
        notifyExternalSystem(newAccounts);
    } catch (Exception e) {
        // One failure in any step rolls back everything
        System.debug('Handler failed: ' + e.getMessage());
    }
}
```

**Why it happens:** LLMs wrap the entire handler in one try/catch. If `createChildRecords` fails for one record, `enrichAccounts` results are also rolled back, and `notifyExternalSystem` never runs. Each independent operation should handle its own errors.

**Correct pattern:**

```apex
public void afterInsert(List<Account> newAccounts) {
    // Independent operations with their own error handling
    enrichAccounts(newAccounts); // Let DML errors propagate if critical

    try {
        createChildRecords(newAccounts);
    } catch (DmlException e) {
        LogService.logError('createChildRecords', e);
        // Decide: should this fail the whole transaction or just log?
    }

    // Non-critical async notification — never blocks the transaction
    if (!newAccounts.isEmpty()) {
        System.enqueueJob(new ExternalNotifyJob(newAccounts));
    }
}
```

**Detection hint:** A single `try/catch` block wrapping an entire trigger handler method with multiple independent operations inside.

---

## Anti-Pattern 6: Creating deeply nested custom exception hierarchies that add no value

**What the LLM generates:**

```apex
public class AppException extends Exception {}
public class ServiceException extends AppException {}
public class AccountServiceException extends ServiceException {}
public class AccountSaveException extends AccountServiceException {}
public class AccountSaveValidationException extends AccountSaveException {}
```

**Why it happens:** LLMs apply Java/C# exception hierarchy patterns to Apex. Deep hierarchies add boilerplate without benefit — Apex catch blocks rarely need 5 levels of exception granularity, and each class consumes metadata.

**Correct pattern:**

```apex
// One or two levels is sufficient for most Apex projects
public class ServiceException extends Exception {}
// Use the message and cause chain for specifics, not class hierarchy

throw new ServiceException('Account save failed: validation error on Status__c');
```

**Detection hint:** More than 3 levels of exception class inheritance in a single project.
