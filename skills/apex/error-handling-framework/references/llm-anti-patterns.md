# LLM Anti-Patterns — Error Handling Framework

Common mistakes AI coding assistants make when generating or advising on Apex error handling framework design. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Inserting the Log Record Directly in the Catch Block

**What the LLM generates:**

```apex
try {
    update accounts;
} catch (DmlException e) {
    insert new Error_Log__c(
        Message__c = e.getMessage(),
        Stack_Trace__c = e.getStackTraceString()
    );
}
```

**Why it happens:** LLMs trained on Java and general OOP patterns treat "log the error in the catch block" as universally correct. The Salesforce-specific constraint — that DML inside a failing transaction rolls back — is not present in most training examples. The pattern looks correct and compiles cleanly.

**Correct pattern:**

```apex
try {
    update accounts;
} catch (DmlException e) {
    ErrorLogger.logException('ERROR', 'MyClass.myMethod', e, correlationId, null);
    // ErrorLogger publishes ErrorLog__e via EventBus.publish() — survives rollback
}
```

**Detection hint:** Any `insert new Error_Log__c(` or `insert errorLog` statement appearing inside a `catch` block.

---

## Anti-Pattern 2: Throwing AuraHandledException Deep in a Service Class

**What the LLM generates:**

```apex
// Service class — WRONG
public class ClaimService {
    public void validateClaim(Claim__c claim) {
        if (String.isBlank(claim.Policy_Number__c)) {
            throw new AuraHandledException('Policy number is required.');
        }
    }
}
```

**Why it happens:** LLMs see `AuraHandledException` used in controller examples and infer it is the standard way to pass a message to the UI. They generalize this to service classes without understanding that it is a transport boundary class, not a domain exception class. The pattern is common in low-quality training samples where service-layer concerns are mixed with controller concerns.

**Correct pattern:**

```apex
// Service class throws domain exception
public class ClaimService {
    public void validateClaim(Claim__c claim) {
        if (String.isBlank(claim.Policy_Number__c)) {
            throw new ValidationException(
                AppException.ErrorCode.REQUIRED_FIELD_MISSING,
                'Policy number is required.'
            );
        }
    }
}

// Controller wraps at boundary only
@AuraEnabled
public static void submitClaim(Id claimId) {
    try {
        ClaimService.validateClaim(claim);
    } catch (ValidationException ve) {
        throw new AuraHandledException(ve.getMessage());
    }
}
```

**Detection hint:** `throw new AuraHandledException` appearing in any class that is not annotated `@AuraEnabled` or is not named `*Controller`.

---

## Anti-Pattern 3: Using Generic catch(Exception e) and Returning null or False

**What the LLM generates:**

```apex
public Boolean processRecord(Account acct) {
    try {
        // ... complex logic ...
        return true;
    } catch (Exception e) {
        System.debug('Error: ' + e.getMessage());
        return false;
    }
}
```

**Why it happens:** LLMs default to "safe" patterns that prevent exceptions from propagating. Returning `false` or `null` on any exception looks defensive. The mistake is that it converts every exception — including `NullPointerException`, `LimitException`, and design bugs — into a silent false result that the caller treats as a business outcome rather than a system failure.

**Correct pattern:**

```apex
public Boolean processRecord(Account acct) {
    try {
        // ... complex logic ...
        return true;
    } catch (ValidationException ve) {
        // Expected, recoverable — handle specifically
        ErrorLogger.logException('WARN', 'MyService.processRecord', ve, correlationId, null);
        return false;
    }
    // Let unexpected exceptions propagate — they represent bugs, not expected outcomes
}
```

**Detection hint:** `catch (Exception e)` followed by `return false`, `return null`, or only `System.debug(` with no rethrow.

---

## Anti-Pattern 4: Calling ErrorLogger Inside a Loop With Individual Publishes

**What the LLM generates:**

```apex
for (Account acct : accounts) {
    try {
        ERPService.syncAccount(acct);
    } catch (IntegrationException ie) {
        ErrorLogger.logException('ERROR', 'Batch.execute', ie, correlationId,
            JSON.serialize(acct.Id));
        // Each call publishes one ErrorLog__e — 200 records = 200 DML statements
    }
}
```

**Why it happens:** LLMs reason about error handling at the individual record level, which is correct for the catch block scope, but do not reason about the aggregate DML statement count. Each `EventBus.publish()` call (even to Platform Events) consumes a DML statement. 200 individual publishes in a 200-record batch scope exhausts Apex's 150-DML-statement limit.

**Correct pattern:**

```apex
List<ErrorLog__e> errorsToPublish = new List<ErrorLog__e>();
for (Account acct : accounts) {
    try {
        ERPService.syncAccount(acct);
    } catch (IntegrationException ie) {
        errorsToPublish.add(new ErrorLog__e(
            Level__c          = 'ERROR',
            Context__c        = 'Batch.execute',
            Message__c        = ie.getMessage(),
            Stack_Trace__c    = ie.getStackTraceString(),
            Correlation_Id__c = correlationId,
            Payload__c        = JSON.serialize(acct.Id)
        ));
    }
}
if (!errorsToPublish.isEmpty()) {
    EventBus.publish(errorsToPublish); // One DML statement
}
```

**Detection hint:** `EventBus.publish(` or `ErrorLogger.logException(` called inside a `for` loop that iterates over a collection of records.

---

## Anti-Pattern 5: Passing e.getMessage() Directly to AuraHandledException

**What the LLM generates:**

```apex
} catch (DmlException e) {
    throw new AuraHandledException(e.getMessage());
}
```

**Why it happens:** LLMs see that `AuraHandledException` accepts a message string and that `e.getMessage()` provides the exception message. The composition looks correct. The LLM does not reason about what Salesforce DML exception messages contain: field names from the org data model, SOQL query fragments, record IDs, and sometimes internal Salesforce error codes that reveal internal system structure.

**Correct pattern:**

```apex
} catch (DmlException e) {
    ErrorLogger.logException('ERROR', 'MyController.doWork', e, correlationId, null);
    throw new AuraHandledException(
        'We could not save your changes. Please try again. Reference: ' + correlationId
    );
}
```

**Detection hint:** `new AuraHandledException(e.getMessage())` or `new AuraHandledException(ex.getMessage())` anywhere in the codebase.

---

## Anti-Pattern 6: Omitting DoesExceedJobScopeMaxLength Check When Processing BatchApexErrorEvent

**What the LLM generates:**

```apex
trigger BatchApexErrorEventTrigger on BatchApexErrorEvent (after insert) {
    for (BatchApexErrorEvent evt : Trigger.new) {
        List<Id> failedIds = (List<Id>) evt.JobScope.split(',');
        // Process failedIds — WRONG: JobScope may be truncated
    }
}
```

**Why it happens:** LLMs generate code that uses `evt.JobScope` as if it always contains the complete list of record IDs. The `DoesExceedJobScopeMaxLength` field and the truncation behavior are documented in the Platform Events Developer Guide but are not surfaced prominently in most code examples. LLMs trained on partial examples omit this check.

**Correct pattern:**

```apex
trigger BatchApexErrorEventTrigger on BatchApexErrorEvent (after insert) {
    for (BatchApexErrorEvent evt : Trigger.new) {
        String scopeDescription;
        if (evt.DoesExceedJobScopeMaxLength) {
            scopeDescription = '[truncated — query AsyncApexJob Id=' + evt.AsyncApexJobId + ']';
        } else {
            scopeDescription = evt.JobScope;
        }
        // Use scopeDescription in log payload; do not parse truncated IDs as complete
    }
}
```

**Detection hint:** Any use of `evt.JobScope` in a `BatchApexErrorEvent` trigger without a preceding `if (evt.DoesExceedJobScopeMaxLength)` guard.
