# LLM Anti-Patterns — Invocable Methods

Common mistakes AI coding assistants make when generating or advising on @InvocableMethod and @InvocableVariable for Flow Apex actions.
These patterns help the consuming agent self-check its own output. Line references are into the Apex
Developer Guide v67.0 (`apexdev`) and the Metadata API Developer Guide v67.0 (`api_meta`), Summer '26.

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

**Why it happens:** LLMs treat invocable methods as single-record operations. Flow calls invocable methods in bulk: the guide's own bulkification rule exists because an action runs "in bulkified execution, such as when an apex action is used in a record trigger flow" (apexdev L5457–5458), where one list carries the interviews the flow batched together. Processing only index `[0]` silently drops every other element, and — because the returned list is then the wrong size — breaks the size-and-order contract at apexdev L5456–5457. UNVERIFIED (2026-09-05): the exact batch size Flow uses for invocable actions (commonly quoted as 200, matching the trigger chunk size) is not stated in the Apex Developer Guide; write code that handles any size rather than relying on a number.

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

**Why it happens:** LLMs return one result thinking it applies to all. The platform requires otherwise: "For a correct bulkification implementation, the Inputs and Outputs must match on both the size and the order. For example, the i-th Output entry must correspond to the i-th Input entry. Matching entries are required for data correctness" (apexdev L5456–5457). A one-element return for N inputs therefore leaves N−1 interviews with no result of their own. UNVERIFIED (2026-09-05): the guide states the requirement and calls the consequence a data-correctness problem; it does not name the runtime error the flow raises, so do not promise callers a specific error message.

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

**Why it happens:** LLMs generate per-request processing with individual DML. When the flow passes 200 interviews, this is 200 insert statements against a synchronous ceiling of 150 DML statements per transaction (apexdev L19554) — and the action is rarely the only thing in that transaction. The same shape in the query position spends the 100-SOQL budget (apexdev L19544).

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

**Why it happens:** LLMs omit `required=true` on `@InvocableVariable`. The modifier "Specifies whether the variable is required. If not specified, the default is false" (apexdev L5691), so an omitted `required` leaves the field optional and the action takes a null it never expected. Two rules bound the fix: `required` "is ignored for output variables" (apexdev L5691), so putting it on a result field buys nothing, and "The defaultValue modifier throws an error when used with required" (apexdev L5693), so a field cannot be both mandatory and pre-filled. UNVERIFIED (2026-09-05): whether Flow Builder blocks *saving* a flow that leaves a required input unbound is a Flow Builder behaviour the Apex Developer Guide does not state — the annotation reference only defines the modifier. Validate the input in Apex regardless.

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

**Why it happens:** LLMs throw exceptions for error conditions. The guide prescribes the opposite for invocables: "To handle exceptions within an invocable method, wrap the results in an Apex object that reports failures. The execution of the invocable method must run and return the same number of results as inputs received even if errors occur" (apexdev L5318–5319), and demonstrates it with `AdjustPositiveValuesAction`, which catches per value and sets a success flag instead of propagating (apexdev L5322–5359). An exception that does escape sends the action element down its `faultConnector`, which "Specifies which node to execute if the action call results in an error" (api_meta L68479) — and it does so for the whole batch of interviews, not for the one input that failed.

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


---

## Anti-Pattern 7: Adding a second `@InvocableMethod` to the same class

**What the LLM generates:**

```apex
public with sharing class CaseEscalationAction {

    @InvocableMethod(label='Escalate Cases')
    public static List<Result> escalate(List<Request> requests) { return doWork(requests); }

    // "convenience overload for screen flows"
    @InvocableMethod(label='Escalate One Case')
    public static List<Result> escalateOne(List<Request> requests) { return doWork(requests); }
}
```

**Why it happens:** The assistant generalises from `@AuraEnabled`, which may decorate many methods
on one class, and from ordinary Apex overloading. The platform does not allow it: "Only one method
in a class can have the InvocableMethod annotation" (apexdev L5422), and for packaged agent actions
the guide spells out the workaround — "Create a separate global Apex class for each agent action in
your managed package" (apexdev L43669–43670). The related trap is stacking annotations: "The only
annotation that can be used with the InvocableMethod annotation is Deprecated" (apexdev L5430), so
an `@TestVisible` or `@AuraEnabled` alongside it is rejected too.

**Correct pattern:**

```apex
// One outer class per action. Both delegate to the same service.
public with sharing class CaseEscalationAction {
    @InvocableMethod(label='Escalate Cases' category='Case Management')
    public static List<CaseEscalationService.Result> escalate(List<CaseEscalationService.Request> requests) {
        return CaseEscalationService.escalate(requests);
    }
}

public with sharing class CaseDeescalationAction {
    @InvocableMethod(label='De-escalate Cases' category='Case Management')
    public static List<CaseEscalationService.Result> deescalate(List<CaseEscalationService.Request> requests) {
        return CaseEscalationService.deescalate(requests);
    }
}
```

**Detection hint:** more than one `@InvocableMethod` token in a single `.cls` file — the first rule
in `scripts/check_invocable_methods.py`.

---

## Anti-Pattern 8: Marking a method `callout=true` and assuming the transaction moves

**What the LLM generates:**

```apex
@InvocableMethod(label='Sync To ERP' callout=true)
public static List<Result> sync(List<Request> requests) {
    // called from a record-triggered flow that has already updated records
    HttpResponse res = new Http().send(buildRequest(requests));
    return parse(res);
}
```

**Why it happens:** The assistant reads `callout=true` as the invocable equivalent of
`@Future(callout=true)` — a permission to call out. It is not. The modifier only participates in a
three-condition gate that is explicitly **screen-flow** scoped: a new transaction is created when
"The method's callout modifier is true", "The action's Transaction Control setting in a screen flow
is configured to let the flow decide", and "The current transaction has uncommitted work"
(apexdev L26872–26876). Otherwise — including for any non-screen flow — "the flow executes the
action in the current transaction" (apexdev L26877–26880), and a callout after DML fails with
`System.CalloutException: You have uncommitted work pending. Please commit or rollback before
calling out.` (apexdev L8768–8769).

**Correct pattern:** declare `callout=true` because it is true, then choose the transaction
deliberately on the flow side with `flowTransactionModel` — `NewTransaction` "Creates a transaction
before the invocable action is executed" (api_meta L68485–68486) — or move the callout into an
asynchronous transaction the invocable enqueues. See `references/code-examples.md` §5 and
`flow/flow-transactional-boundaries`.

**Detection hint:** `Http().send(`, `HttpRequest`, or a `HttpClient` call inside a class whose
`@InvocableMethod` does not carry `callout=true` — or one that does, in a class whose comments or
tests assume a record-triggered caller.
