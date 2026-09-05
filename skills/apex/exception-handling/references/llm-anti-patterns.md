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

**Why it happens:** LLMs use `catch (Exception e)` as a universal safety net. It catches `QueryException`, `DmlException`, `CalloutException` and `NullPointerException` identically, losing the ability to handle each failure mode appropriately (retry callouts, report DML field errors, and so on). It is also a false safety net for the failure most likely to end the transaction: `System.LimitException` is uncatchable, and "when exceptions are uncatchable, catch blocks, as well as finally blocks if any, aren’t executed" (Apex Developer Guide, `apexdev` L39722–39728). The generic catch buys nothing there and hides everything else.

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

**Why it happens:** LLMs pass the raw exception message to `AuraHandledException`. A `DmlException` message is built for operators, not users — the guide's own sample reads `System.DmlException: Insert failed. First exception on row 0; first error: REQUIRED_FIELD_MISSING, Required fields are missing: [Description, Price, Total Inventory]` (`apexdev` L39754–39757) — so the status code, the validation-rule text and the field API names all reach the browser. The stack trace does not: the client error "doesn’t include the `body.stackTrace` property" for an `AuraHandledException` (Lightning Web Components Developer Guide, page `apex-error-handling`, `lwc_guide` L7522). The leak is schema and rule text, not the trace.

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

---

## Anti-Pattern 7: A negative test with no `Assert.fail()` after the call that should throw

**What the LLM generates:**

```apex
@IsTest
static void testInvalidInputThrows() {
    try {
        IntakeService.submit(null);
    } catch (IntakeException e) {
        Assert.areEqual('Input required', e.getMessage());
    }
}
```

**Why it happens:** The shape looks complete — there is a `try`, a `catch`, and an assertion. But if the
method stops throwing, the `catch` block never runs, no assertion executes, and the test still passes.
The regression it exists to catch is exactly the one it cannot see.

**Correct pattern:**

```apex
@IsTest
static void testInvalidInputThrows() {
    try {
        IntakeService.submit(null);
        Assert.fail('Expected IntakeException for a null payload.');
    } catch (IntakeException e) {
        Assert.areEqual('Input required', e.getMessage());
        Assert.isInstanceOfType(e.getCause(), NullPointerException.class);
    }
}
```

`Assert.fail(msg)` is documented for exactly this shape and is safe inside the `try`, because the
assertion failure it raises cannot be caught by the surrounding `catch`: "You can’t, however, catch the
assertion failure in the try/catch block even though it’s logged as an exception" (Apex Reference Guide,
`apexrefguide` L200594–200595).

**Detection hint:** a `try` block inside an `@IsTest` method whose last statement is a method call, with
a `catch` that contains assertions and no `Assert.fail` / `System.assert(false, ...)` above it.

---

## Anti-Pattern 8: Wrapping an entire Queueable `execute` in `try/catch` to "stop the job failing"

**What the LLM generates:**

```apex
public void execute(QueueableContext ctx) {
    try {
        doAllTheWork();
    } catch (Exception e) {
        System.debug('Job failed: ' + e.getMessage());
    }
}
```

**Why it happens:** The assistant reasons that a caught exception means a job that does not fail. On the
platform the two failures that actually kill async jobs — governor limits and assertion failures — are
uncatchable, so neither this `catch` nor a `finally` beside it executes (Apex Developer Guide,
`apexdev` L39722–39728). The job still shows `Failed`, and the swallow has removed the only signal for
the failures that *were* catchable.

**Correct pattern:**

```apex
public void execute(QueueableContext ctx) {
    System.attachFinalizer(new IntakeFinalizer());
    doAllTheWork();   // let it throw
}

public class IntakeFinalizer implements Finalizer {
    public void execute(FinalizerContext ctx) {
        if (ctx.getResult() == ParentJobResult.UNHANDLED_EXCEPTION) {
            ApplicationLogger.error('IntakeQueueable', ctx.getException());
            ApplicationLogger.flush();
        }
    }
}
```

`FinalizerContext.getResult()` returns `SUCCESS` or `UNHANDLED_EXCEPTION`, and `getException()` "returns
the exception with which the Queueable job failed when `getResult` is `UNHANDLED_EXCEPTION`"
(`apexdev` L16330–16336). The finalizer runs in its own transaction, so its log write survives the
job's rollback.

**Detection hint:** a class implementing `Queueable` or `Batchable` whose `execute` body is one
`try { ... } catch (Exception e) { ... }` with no `System.attachFinalizer` and no
`Database.RaisesPlatformEvents` on the class declaration.

---

## Anti-Pattern 9: Calling out from a catch block that still holds an open savepoint

**What the LLM generates:**

```apex
Savepoint sp = Database.setSavepoint();
try {
    insert records;
} catch (DmlException e) {
    Database.rollback(sp);
    notifyOpsTeam(e.getMessage());   // HTTP callout
}
```

**Why it happens:** The rollback reads as "the transaction is clean now", so the callout looks safe. It
is not: the savepoint is rolled back but still *active*, and the callout raises a
`System.CalloutException` carrying "All active Savepoints must be released before making callouts."
(`apexdev` L8742–8750). The compensating notification never goes out, and the new exception replaces the
`DmlException` the caller was meant to receive.

**Correct pattern:**

```apex
Savepoint sp = Database.setSavepoint();
try {
    insert records;
} catch (DmlException e) {
    Database.rollback(sp);
    Database.releaseSavepoint(sp);   // required before any callout
    notifyOpsTeam(summarize(e));
    throw CaseIntakeException.of(CaseIntakeException.Code.ROW_REJECTED, 'Intake failed.', e);
}
```

The order — roll back, release, then call out — is the guide's own worked example (`apexdev`
L8730–8741). Note that `releaseSavepoint` also releases every savepoint created after it, and that a
later `Database.rollback` on a released savepoint raises `System.InvalidOperationException`
(`apexdev` L8776–8781).

**Detection hint:** `Database.setSavepoint` in a method that also contains `Http().send`, `callout:`, or
a `@future(callout=true)` invocation, with no `Database.releaseSavepoint` between them.
