# LLM Anti-Patterns — Invocable Methods

Common mistakes AI coding assistants make when generating or advising on @InvocableMethod and @InvocableVariable for Flow Apex actions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Processing only the first element of the input list

**What the LLM generates:**

```apex
@InvocableMethod(label='Create Task' description='Creates a follow-up task')
public static List<String> createTask(List<TaskRequest> requests) {
    TaskRequest req = requests[0]; // Only processes the first element
    Task t = new Task(Subject = req.subject, WhoId = req.contactId);
    insert t;
    return new List<String>{ t.Id };
}
```

**Why it happens:** LLMs treat invocable methods as single-record operations. Flow calls invocable methods in bulk — if a Record-Triggered Flow fires for 200 records, the `requests` list contains 200 elements. Processing only index `[0]` silently drops 199 records.

**Correct pattern:**

```apex
@InvocableMethod(label='Create Task' description='Creates a follow-up task')
public static List<String> createTask(List<TaskRequest> requests) {
    List<Task> tasks = new List<Task>();
    List<String> results = new List<String>();
    for (TaskRequest req : requests) {
        tasks.add(new Task(Subject = req.subject, WhoId = req.contactId));
    }
    insert tasks;
    for (Task t : tasks) {
        results.add(t.Id);
    }
    return results;
}
```

**Detection hint:** `requests\[0\]` or `requests\.get\(0\)` in an `@InvocableMethod` without iterating the full list.

---

## Anti-Pattern 2: Returning a single-element list when the output must match input size

**What the LLM generates:**

```apex
@InvocableMethod
public static List<String> processRecords(List<Id> recordIds) {
    // Process all records...
    return new List<String>{ 'Success' }; // One result for N inputs
}
```

**Why it happens:** LLMs return one result thinking it applies to all. Flow expects the output list to have the same number of elements as the input list — each output element maps to the corresponding input element. Returning a single element causes index-out-of-bounds errors in the Flow.

**Correct pattern:**

```apex
@InvocableMethod
public static List<String> processRecords(List<Id> recordIds) {
    List<String> results = new List<String>();
    for (Id recordId : recordIds) {
        // Process each record
        results.add('Success');
    }
    return results; // Same size as input list
}
```

**Detection hint:** `@InvocableMethod` that returns a list with a hardcoded size (e.g., `new List<String>{'Success'}`) instead of building results per input element.

---

## Anti-Pattern 3: Using primitive parameters instead of a wrapper class with @InvocableVariable

**What the LLM generates:**

```apex
@InvocableMethod(label='Send Email')
public static void sendEmail(List<String> emailAddresses) {
    // Only accepts one field — no way to pass subject, body, etc.
}
```

**Why it happens:** LLMs use a simple `List<String>` for the input because it compiles. But Flow often needs to pass multiple inputs per invocation (email address, subject, body, template ID). Without a wrapper class with `@InvocableVariable` fields, the action is limited to a single input value.

**Correct pattern:**

```apex
public class EmailRequest {
    @InvocableVariable(required=true label='Recipient Email')
    public String emailAddress;

    @InvocableVariable(required=true label='Subject')
    public String subject;

    @InvocableVariable(label='Body')
    public String body;
}

@InvocableMethod(label='Send Email' description='Sends a templated email')
public static List<EmailResult> sendEmail(List<EmailRequest> requests) {
    List<EmailResult> results = new List<EmailResult>();
    for (EmailRequest req : requests) {
        // Send email with all fields
        results.add(new EmailResult(true, 'Sent'));
    }
    return results;
}
```

**Detection hint:** `@InvocableMethod` with `List<String>` or `List<Id>` parameter when the use case clearly requires multiple input fields.

---

## Anti-Pattern 4: Performing DML inside a loop within the invocable method

**What the LLM generates:**

```apex
@InvocableMethod
public static List<String> cloneRecords(List<CloneRequest> requests) {
    List<String> results = new List<String>();
    for (CloneRequest req : requests) {
        SObject original = Database.query('SELECT Id FROM ' + req.objectType + ' WHERE Id = :req.recordId');
        SObject cloned = original.clone(false, true, false, false);
        insert cloned; // DML in loop
        results.add(cloned.Id);
    }
    return results;
}
```

**Why it happens:** LLMs generate per-request processing with individual DML. When Flow passes 200 records, this is 200 insert statements — exceeding the 150 DML statement limit.

**Correct pattern:**

```apex
@InvocableMethod
public static List<String> cloneRecords(List<CloneRequest> requests) {
    // Collect all records first
    Set<Id> recordIds = new Set<Id>();
    for (CloneRequest req : requests) {
        recordIds.add(req.recordId);
    }
    Map<Id, SObject> originals = new Map<Id, SObject>(
        [SELECT Id, Name FROM Account WHERE Id IN :recordIds]
    );

    List<SObject> clones = new List<SObject>();
    for (CloneRequest req : requests) {
        SObject original = originals.get(req.recordId);
        if (original != null) {
            clones.add(original.clone(false, true, false, false));
        }
    }
    insert clones; // Single DML

    List<String> results = new List<String>();
    for (SObject c : clones) {
        results.add(c.Id);
    }
    return results;
}
```

**Detection hint:** `insert ` or `update ` or `delete ` inside a `for` loop within an `@InvocableMethod`.

---

## Anti-Pattern 5: Not marking required wrapper fields with required=true

**What the LLM generates:**

```apex
public class ProcessRequest {
    @InvocableVariable
    public Id recordId; // Should be required — NPE if missing

    @InvocableVariable
    public String action;
}
```

**Why it happens:** LLMs omit `required=true` on `@InvocableVariable`. Flow builders can then wire the action without providing mandatory values, causing `NullPointerException` at runtime. Marking fields as required makes Flow enforce the input at design time.

**Correct pattern:**

```apex
public class ProcessRequest {
    @InvocableVariable(required=true label='Record ID' description='The record to process')
    public Id recordId;

    @InvocableVariable(required=true label='Action' description='Action to perform: Approve or Reject')
    public String action;

    @InvocableVariable(label='Comment' description='Optional comment')
    public String comment;
}
```

**Detection hint:** `@InvocableVariable` without `required=true` on fields that would cause NPE if null.

---

## Anti-Pattern 6: Throwing unhandled exceptions that crash the entire Flow

**What the LLM generates:**

```apex
@InvocableMethod
public static List<String> validateRecords(List<Id> recordIds) {
    List<Account> accounts = [SELECT Id, Name FROM Account WHERE Id IN :recordIds];
    if (accounts.isEmpty()) {
        throw new IllegalArgumentException('No records found'); // Crashes the Flow
    }
    return new List<String>{ 'Valid' };
}
```

**Why it happens:** LLMs throw exceptions for error conditions. An unhandled exception in an invocable method causes the entire Flow interview to fail with a cryptic error. Flow builders expect the action to return error information they can handle in the Flow.

**Correct pattern:**

```apex
public class ValidationResult {
    @InvocableVariable public Boolean isSuccess;
    @InvocableVariable public String errorMessage;
}

@InvocableMethod
public static List<ValidationResult> validateRecords(List<Id> recordIds) {
    List<ValidationResult> results = new List<ValidationResult>();
    List<Account> accounts = [SELECT Id FROM Account WHERE Id IN :recordIds];
    Set<Id> foundIds = new Map<Id, Account>(accounts).keySet();

    for (Id recordId : recordIds) {
        ValidationResult r = new ValidationResult();
        r.isSuccess = foundIds.contains(recordId);
        r.errorMessage = r.isSuccess ? null : 'Record not found: ' + recordId;
        results.add(r);
    }
    return results;
}
```

**Detection hint:** `throw new` inside an `@InvocableMethod` for non-critical error conditions that should be returned as output.
