# Code Examples — Error Handling Framework

A complete, deployable error-handling package for a **contract amendment
service**: a custom exception tree, a service that runs partial-success DML and
captures one failure row per rejected record, an all-or-nothing posting path
guarded by a `Savepoint`, a Queueable whose Finalizer writes the log even when
the job dies on a governor limit, a test class that drives the negative paths,
and the metadata to deploy the lot.

Every platform claim carries an `apexdev L<n>` citation into the Apex Developer
Guide text captured for this package. Claims with no corpus support are marked
`UNVERIFIED (2026-09-12):` inline and are written as questions to answer in a
scratch org, not as facts.

Scope split against the rest of this skill: `SKILL.md` owns the **Platform
Event** log publisher (`ErrorLog__e` → `Error_Log__c`) and the
`BatchApexErrorEvent` subscriber. This file owns the **DML + Finalizer** path,
which needs no Platform Event definition and no subscriber trigger. Pick one
per org; running both doubles the log store.

Canonical building blocks are referenced, not re-invented:

| Building block | Path | Used for |
|---|---|---|
| `ApplicationLogger` | `templates/apex/ApplicationLogger.cls` | The only class that writes log rows. The Finalizer calls `ApplicationLogger.error(...)`; nothing else in the package does DML against a log object |
| `Application_Log__c` | `templates/apex/custom_objects/Application_Log__c.object-meta.xml` | The log object `ApplicationLogger` writes to, plus its eight fields under `templates/apex/custom_objects/fields/` |
| `Logger_Setting__mdt` | `templates/apex/cmdt/Logger_Setting__mdt` | `Minimum_Severity__c`, read by `ApplicationLogger.getMinimumSeverity()` — without it every org logs at `INFOL` |

Ship `ApplicationLogger.cls` as a byte-identical copy of the template plus its
`-meta.xml`. A class that calls it and is not shipped with it fails deploy with
`Variable does not exist: ApplicationLogger`.

Cross-references rather than copies:

- The Finalizer contract itself — `attachFinalizer` placement, the five-retry
  re-enqueue budget, `FinalizerContext`'s four methods, the one-finalizer-per-job
  rule — belongs to `apex/apex-queueable-patterns` and is not restated here.
  This file uses the interface; that skill explains it.

---

## 1. The object model

Three custom objects. None of them is a standard object, and none of them is
the log object — `Application_Log__c` stays the operational log, while
`Amendment_Failure__c` is a *business* artifact the amendment owner reads.

| Object | Role | Key fields |
|---|---|---|
| `Contract_Amendment__c` | The amendment request being posted | `Status__c`, `Effective_Date__c`, `Correlation_Id__c` |
| `Amendment_Line__c` | One line of the amendment; master-detail to the amendment | `Product_Code__c`, `New_Annual_Value__c`, `Posting_Status__c` |
| `Amendment_Failure__c` | One row per record the platform rejected | `Row_Index__c`, `Failed_Record_Id__c`, `Status_Code__c`, `Field_Names__c`, `Message__c`, `Phase__c`, `Correlation_Id__c` |

`Contract_Amendment__c.object-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <deploymentStatus>Deployed</deploymentStatus>
    <description>A requested change to an existing service agreement, posted as a unit.</description>
    <enableActivities>false</enableActivities>
    <enableReports>true</enableReports>
    <label>Contract Amendment</label>
    <pluralLabel>Contract Amendments</pluralLabel>
    <nameField>
        <displayFormat>AMD-{0000000000}</displayFormat>
        <label>Amendment Number</label>
        <type>AutoNumber</type>
    </nameField>
    <sharingModel>ReadWrite</sharingModel>
</CustomObject>
```

`Amendment_Failure__c/fields/Status_Code__c.field-meta.xml` — the field that
makes failures aggregable without parsing message text:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Status_Code__c</fullName>
    <description>Database.Error.getStatusCode() as a string, e.g. FIELD_CUSTOM_VALIDATION_EXCEPTION. Group by this, never by Message__c.</description>
    <externalId>false</externalId>
    <label>Status Code</label>
    <length>80</length>
    <required>false</required>
    <trackTrending>false</trackTrending>
    <type>Text</type>
    <unique>false</unique>
</CustomField>
```

---

## 2. The exception tree

Two rules from the guide shape this file. A custom exception class must extend
`Exception` and its name must end in `Exception` (`apexdev L40143-40145`), and
user-defined exception types form an inheritance tree that a single `catch`
on the base type collects (`apexdev L40151-40157`) — the guide's own example
declares the base `virtual` and the leaf plain.

`AmendmentException.cls` — the base:

```apex
/**
 * Base of the amendment exception tree.
 *
 * Declared virtual because the guide's inheritance-tree example does exactly
 * that: "public virtual class BaseException extends Exception {}" with
 * "public class OtherException extends BaseException {}" beneath it, and a
 * catch on the base collecting the leaf (apexdev L40151-40157).
 *
 * The code is a public field, not a constructor argument. Apex hands every
 * exception class four constructors: no-arg, String message, Exception cause,
 * and (String, Exception) (apexdev L40167-40180). Those are the documented
 * ways to construct one.
 *
 * UNVERIFIED (2026-09-12): whether a custom (Code, String) constructor that
 * chains with this(message) into the generated String constructor compiles.
 * The guide documents the four forms above and says nothing about chaining
 * into them. Question for a scratch org before adopting the constructor form
 * shown in SKILL.md Pattern 2: does it compile at API 67.0? Until that is
 * answered, assign the field after construction as below - that form is
 * unambiguous.
 */
public virtual class AmendmentException extends Exception {

    public enum Code {
        AMENDMENT_LINE_INVALID,
        PRICING_SERVICE_UNAVAILABLE,
        POSTING_CONFLICT,
        CONFIGURATION_MISSING,
        UNEXPECTED
    }

    public Code errorCode = Code.UNEXPECTED;
    public String correlationId;

    public String describe() {
        return String.valueOf(this.errorCode) + '|' + String.valueOf(this.correlationId);
    }
}
```

`AmendmentValidationException.cls`, `AmendmentPricingException.cls` and
`AmendmentPostingException.cls` are one line each — separate files, because
Apex allows one top-level class per file:

```apex
public class AmendmentValidationException extends AmendmentException {}
```

```apex
public class AmendmentPricingException extends AmendmentException {}
```

```apex
public class AmendmentPostingException extends AmendmentException {}
```

Throwing one — this method belongs to `ContractAmendmentService` (section 3);
it is shown here so the construct-then-assign form sits next to the class it
applies to:

```apex
// ContractAmendmentService, continued.
public static void rejectLine(Amendment_Line__c line, String correlationId) {
    AmendmentValidationException ex = new AmendmentValidationException(
        'Amendment line ' + line.Product_Code__c + ' has no active price book entry.'
    );
    ex.errorCode = AmendmentException.Code.AMENDMENT_LINE_INVALID;
    ex.correlationId = correlationId;
    throw ex;
}
```

Do not put the exception object into a log payload with `JSON.serialize`. From
API 63.0 onward, "JSON serialization of custom exceptions and most built-in
exceptions isn't supported" and the attempt throws `Type unsupported in JSON:
MyException` (`apexdev L36804-36806`) — a serializer call inside a catch block
replaces the original failure with a JSON one.

---

## 3. Partial-success DML with per-row capture

`Database.update(lines, false)` is the allOrNone=false form: "if a record
fails, the remainder of the DML operation can still succeed. Your application
can then inspect the rejected records and possibly retry the operation"
(`apexdev L7583-7586`). In that mode the call does not throw — "Database class
methods don't throw exceptions. Instead, they return a list of errors for any
errors that occurred on failed records" (`apexdev L8428-8433`) — so the only
way a rejection is ever seen is that somebody walks the results.

`ContractAmendmentService.cls`:

```apex
/**
 * Posts amendment lines in partial-success mode and turns every rejected row
 * into an Amendment_Failure__c record.
 *
 * The index of a SaveResult matches the index of the input record: the
 * DmlException accessors are all documented as taking the "index of the failed
 * record" (apexdev L40018-40023), and the result array follows the same
 * positional contract. Keep the input list immutable across the call.
 */
public with sharing class ContractAmendmentService {

    private static final String SOURCE = 'ContractAmendmentService';

    public class PostingOutcome {
        public Integer succeeded = 0;
        public List<Amendment_Failure__c> failures = new List<Amendment_Failure__c>();
    }

    public static PostingOutcome postLines(List<Amendment_Line__c> lines, String correlationId) {
        PostingOutcome outcome = new PostingOutcome();
        if (lines == null || lines.isEmpty()) {
            return outcome;
        }

        // allOrNone = false. Nothing below this line throws DmlException;
        // every rejection arrives as data in results (apexdev L8428-8433).
        List<Database.SaveResult> results = Database.update(lines, false);

        for (Integer i = 0; i < results.size(); i++) {
            Database.SaveResult sr = results[i];
            if (sr.isSuccess()) {
                outcome.succeeded++;
                continue;
            }
            // getErrors() returns a list of Database.Error (apexdev L8440-8443).
            // One rejected row can carry more than one error; keep the first as
            // the status code and fold the rest into the message.
            List<String> messages = new List<String>();
            String statusCode = null;
            List<String> fieldNames = new List<String>();
            for (Database.Error err : sr.getErrors()) {
                if (statusCode == null) {
                    statusCode = String.valueOf(err.getStatusCode());
                }
                messages.add(err.getMessage());
                fieldNames.addAll(err.getFields());
            }
            outcome.failures.add(new Amendment_Failure__c(
                Row_Index__c      = i,
                Failed_Record_Id__c = lines[i].Id,
                Status_Code__c    = statusCode,
                Field_Names__c    = String.join(fieldNames, ','),
                Message__c        = String.join(messages, ' / ').left(32768),
                Phase__c          = 'POST_LINES',
                Correlation_Id__c = correlationId
            ));
        }

        if (!outcome.failures.isEmpty()) {
            // One DML for the whole batch of failures, never one per row.
            // Partial-success again: a failure row that is itself rejected must
            // not take the other failure rows down with it.
            Database.insert(outcome.failures, false);
            ApplicationLogger.warn(
                SOURCE,
                outcome.failures.size() + ' of ' + lines.size()
                    + ' amendment lines rejected. correlationId=' + correlationId
            );
        }
        return outcome;
    }
}
```

Why `Database.update(lines, false)` rather than `update lines;`: the DML
statement form throws and "any error that occurs during bulk DML processing
[is] thrown as an Apex exception that immediately interrupts control flow"
(`apexdev L7580-7582`), which collapses 200 distinct rejections into one
message and one stack trace. Pick the statement form only when a single bad row
genuinely must abort the whole amendment — and then read section 4, because
that abort has rollback semantics you have to design around.

---

## 4. The all-or-nothing path: Savepoint and rollback

When an amendment must post as a unit, the service still wants a failure record
to survive. It cannot simply insert one after the rollback: "Any DML operations
that were processed before the exception are rolled back and aren't committed to
the database" (`apexdev L39587-39588`), and a `Database.rollback(sp)` undoes
everything back to the savepoint by definition (`apexdev L8679-8684`).

The shape that works: take the savepoint, do the work, and on failure roll back
*first*, then insert the failure record in the surviving part of the same
transaction.

```apex
public with sharing class AmendmentPostingUnit {

    private static final String SOURCE = 'AmendmentPostingUnit';

    public static Boolean postAtomically(
        Contract_Amendment__c amendment,
        List<Amendment_Line__c> lines,
        String correlationId
    ) {
        // Each savepoint counts against the DML statement governor limit
        // (apexdev L8691). One per transaction, never one per record.
        Savepoint sp = Database.setSavepoint();
        try {
            update lines;
            amendment.Status__c = 'Posted';
            update amendment;
            return true;

        } catch (DmlException e) {
            // Roll back the partial write BEFORE writing the failure record, so
            // the failure record is not inside the range being discarded.
            Database.rollback(sp);

            // getNumDml is the count of failed records; the three accessors are
            // indexed by the same position (apexdev L40018-40023).
            List<Amendment_Failure__c> failures = new List<Amendment_Failure__c>();
            for (Integer i = 0; i < e.getNumDml(); i++) {
                failures.add(new Amendment_Failure__c(
                    Row_Index__c        = i,
                    Failed_Record_Id__c = e.getDmlId(i),
                    Status_Code__c      = e.getDmlStatusCode(i),
                    Field_Names__c      = String.join(e.getDmlFieldNames(i), ','),
                    Message__c          = e.getDmlMessage(i),
                    Phase__c            = 'POST_ATOMIC',
                    Correlation_Id__c   = correlationId
                ));
            }
            insert failures;

            // getStackTraceString and getTypeName are the two accessors worth
            // storing; getMessage alone loses where it happened
            // (apexdev L39973-39981).
            ApplicationLogger.error(SOURCE, e);
            return false;
        }
    }
}
```

Two traps this code is shaped around:

- **Re-inserting a rolled-back sObject.** "The ID on an sObject inserted after
  setting a savepoint isn't cleared after a rollback" (`apexdev L8697`). A
  retry that re-inserts the same in-memory `Amendment_Line__c` list after the
  rollback fails, because the instances still carry Ids. Re-query, or null the
  Id, before any retry.
- **Callouts after uncommitted DML.** A callout in the same transaction as
  pending DML raises `CalloutException`; the documented fix is to roll back the
  uncommitted DML with a savepoint and then call
  `Database.releaseSavepoint` (`apexdev L8726-8731`). A pricing callout placed
  between `update lines;` and the catch block would break for that reason, not
  because of anything in the error framework.

---

## 5. Queueable with a Finalizer that logs through the limit

The Apex Developer Guide's own Logging Finalizer example is the grounding for
this whole section: it "demonstrates the use of Transaction Finalizers in
logging messages from a Queueable job, regardless of whether the job succeeds
or fails", and states that "the finalizer state is preserved even if the
Queueable job fails, and can be accessed for use in DML in finalizer
implementation" (`apexdev L16364-16382`). The example's Queueable body is
literally `while (true) { // Results in limit error }` and the finalizer still
reaches its `Database.insert(logRecords, false)` (`apexdev L16397-16430`).

That is the property no `try/catch` has. A `LimitException` cannot be caught,
and "when exceptions are uncatchable, catch blocks, as well as finally blocks
if any, aren't executed" (`apexdev L39721-39728`). A logger in a `finally`
block is not a safety net; the Finalizer is.

```apex
/**
 * Posts one amendment asynchronously. The Finalizer is an inner class, and the
 * only thing in this package that logs on the failure path.
 *
 * Placement matters: attachFinalizer is the first statement of execute(), so
 * code that fails on the next line is already covered.
 */
public with sharing class AmendmentPostingQueueable implements Queueable {

    private final Id amendmentId;
    private final String correlationId;

    public AmendmentPostingQueueable(Id amendmentId, String correlationId) {
        this.amendmentId = amendmentId;
        this.correlationId = correlationId;
    }

    public void execute(QueueableContext ctx) {
        System.attachFinalizer(new PostingFinalizer(amendmentId, correlationId));

        List<Amendment_Line__c> lines = [
            SELECT Id, Product_Code__c, New_Annual_Value__c, Posting_Status__c
            FROM Amendment_Line__c
            WHERE Contract_Amendment__c = :amendmentId
            WITH USER_MODE
        ];
        for (Amendment_Line__c line : lines) {
            line.Posting_Status__c = 'Posted';
        }
        ContractAmendmentService.postLines(lines, correlationId);
    }

    /**
     * Runs in its own Apex and Database transaction after the Queueable ends,
     * on SUCCESS and on UNHANDLED_EXCEPTION alike. Because it is a separate
     * transaction, its DML is not inside the range a rollback of the parent
     * discards - that, not any Platform Event, is what makes this rollback-safe.
     *
     * getResult returns SUCCESS or UNHANDLED_EXCEPTION, and getException
     * returns the failing exception in the second case and null in the first
     * (apexdev L16336-16344).
     */
    private class PostingFinalizer implements Finalizer {

        private final Id amendmentId;
        private final String correlationId;

        private PostingFinalizer(Id amendmentId, String correlationId) {
            this.amendmentId = amendmentId;
            this.correlationId = correlationId;
        }

        public void execute(FinalizerContext ctx) {
            String jobId = String.valueOf(ctx.getAsyncApexJobId());

            if (ctx.getResult() == ParentJobResult.SUCCESS) {
                ApplicationLogger.info(
                    'AmendmentPostingQueueable',
                    'Amendment ' + amendmentId + ' posted. job=' + jobId
                        + ' correlationId=' + correlationId
                );
                ApplicationLogger.flush();
                return;
            }

            Exception cause = ctx.getException();
            ApplicationLogger.error('AmendmentPostingQueueable', cause);

            // The business-visible failure record, written in this transaction
            // so it outlives the parent job's rollback.
            insert new Amendment_Failure__c(
                Contract_Amendment__c = amendmentId,
                Status_Code__c        = cause == null ? 'UNKNOWN' : cause.getTypeName(),
                Message__c            = cause == null ? 'Job failed with no exception' : cause.getMessage(),
                Phase__c              = 'ASYNC_POST',
                Correlation_Id__c     = correlationId
            );
        }
    }
}
```

Three constraints on that Finalizer, each from the guide:

- Only one finalizer instance can be attached to any Queueable job
  (`apexdev L16354`) — a second `attachFinalizer` call is an error, so the
  Finalizer has to be the single failure seam for the whole job.
- Synchronous governor limits apply to the Finalizer transaction, except heap
  size, `System.enqueueJob` count, and `@future` count, which use the async
  limits (`apexdev L16297-16303`). A Finalizer that queries per record can
  exhaust its own limits and lose the record it exists to write.
- It is not a guarantee: "If a job request is terminated unexpectedly, such as
  a database shutdown during system upgrade, the transaction finalizer can fail
  to execute" (`apexdev L16533-16534`).

Deliberately not enqueued from the failure path here: the retry. Re-enqueueing
from the Finalizer, and the five-consecutive-failure ceiling that bounds it
(`apexdev L16292-16295`), belong to `apex/apex-queueable-patterns`.

---

## 6. The controller boundary

The one file in the package allowed to construct an `AuraHandledException`, and
the reason the checker keys its rule on the file name:

```apex
public with sharing class ContractAmendmentController {

    @AuraEnabled
    public static String submitAmendment(Id amendmentId) {
        String correlationId = UserInfo.getUserId() + ':' + String.valueOf(Datetime.now().getTime());
        try {
            System.enqueueJob(new AmendmentPostingQueueable(amendmentId, correlationId));
            return correlationId;

        } catch (AmendmentValidationException ve) {
            ApplicationLogger.warn('ContractAmendmentController', ve.describe());
            throw new AuraHandledException(
                'This amendment has a line we cannot post yet. Reference: ' + correlationId
            );

        } catch (AmendmentException ae) {
            // One catch collects every leaf of the tree (apexdev L40151-40157).
            ApplicationLogger.error('ContractAmendmentController', ae);
            throw new AuraHandledException(
                'We could not submit this amendment. Reference: ' + correlationId
            );
        }
    }
}
```

`getMessage()` is never the argument. What a `DmlException` message carries —
"Required fields are missing: [Price, Total Inventory]" is the guide's own
sample output (`apexdev L40058-40062`) — is the org's field names, sent to the
browser.

Note what `System.enqueueJob` does *not* protect against: "If an Apex
transaction rolls back, any queueable jobs queued for execution by the
transaction aren't processed" (`apexdev L15961`), and the same holds for
`@future` (`apexdev L18081`). Enqueueing a logging job from a failing
transaction logs nothing.

---

## 7. Test class — the negative paths

```apex
@IsTest
private class ContractAmendmentServiceTest {

    @TestSetup
    static void seed() {
        Contract_Amendment__c amendment = new Contract_Amendment__c(
            Status__c = 'Draft',
            Effective_Date__c = Date.today().addDays(30)
        );
        insert amendment;

        List<Amendment_Line__c> lines = new List<Amendment_Line__c>();
        for (Integer i = 0; i < 5; i++) {
            lines.add(new Amendment_Line__c(
                Contract_Amendment__c = amendment.Id,
                Product_Code__c = 'SKU-' + i,
                New_Annual_Value__c = 1000 * (i + 1)
            ));
        }
        insert lines;
    }

    @IsTest
    static void rejectedRowBecomesOneFailureRecord() {
        List<Amendment_Line__c> lines = [SELECT Id, New_Annual_Value__c FROM Amendment_Line__c ORDER BY Product_Code__c];
        // Row 2 violates the "amount must be positive" validation rule.
        lines[2].New_Annual_Value__c = -1;

        Test.startTest();
        ContractAmendmentService.PostingOutcome outcome =
            ContractAmendmentService.postLines(lines, 'corr-neg-1');
        Test.stopTest();

        Assert.areEqual(4, outcome.succeeded, 'The four valid rows must still post');
        Assert.areEqual(1, outcome.failures.size(), 'Exactly one failure row');
        Assert.areEqual(2, outcome.failures[0].Row_Index__c,
            'Row index must match the position in the input list');
        Assert.areEqual('corr-neg-1', outcome.failures[0].Correlation_Id__c);
        Assert.isNotNull(outcome.failures[0].Status_Code__c,
            'Status code comes from Database.Error.getStatusCode, never from message text');

        Assert.areEqual(1, [SELECT COUNT() FROM Amendment_Failure__c WHERE Phase__c = 'POST_LINES']);
    }

    @IsTest
    static void emptyInputIsNotAnError() {
        Test.startTest();
        ContractAmendmentService.PostingOutcome outcome =
            ContractAmendmentService.postLines(new List<Amendment_Line__c>(), 'corr-empty');
        Test.stopTest();

        Assert.areEqual(0, outcome.succeeded);
        Assert.areEqual(0, outcome.failures.size());
        Assert.areEqual(0, [SELECT COUNT() FROM Amendment_Failure__c]);
    }

    @IsTest
    static void atomicPathRollsBackAndStillRecordsTheFailure() {
        Contract_Amendment__c amendment = [SELECT Id, Status__c FROM Contract_Amendment__c LIMIT 1];
        List<Amendment_Line__c> lines = [SELECT Id, New_Annual_Value__c FROM Amendment_Line__c];
        lines[0].New_Annual_Value__c = -1;

        Test.startTest();
        Boolean posted = AmendmentPostingUnit.postAtomically(amendment, lines, 'corr-atomic');
        Test.stopTest();

        Assert.isFalse(posted, 'A rejected line must fail the unit');
        Assert.areEqual('Draft',
            [SELECT Status__c FROM Contract_Amendment__c WHERE Id = :amendment.Id].Status__c,
            'The rollback must undo the Posted status');
        Assert.areEqual(1, [SELECT COUNT() FROM Amendment_Failure__c WHERE Phase__c = 'POST_ATOMIC'],
            'The failure record is written after the rollback, so it survives it');
    }

    @IsTest
    static void validationExceptionCarriesCodeAndCorrelationId() {
        Amendment_Line__c line = [SELECT Id, Product_Code__c FROM Amendment_Line__c LIMIT 1];
        try {
            ContractAmendmentService.rejectLine(line, 'corr-throw');
            Assert.fail('Expected AmendmentValidationException');
        } catch (AmendmentException ae) {
            Assert.isInstanceOfType(ae, AmendmentValidationException.class,
                'The base catch must still collect the leaf type');
            Assert.areEqual(AmendmentException.Code.AMENDMENT_LINE_INVALID, ae.errorCode);
            Assert.areEqual('corr-throw', ae.correlationId);
        }
    }
}
```

What this test class deliberately does not assert:

UNVERIFIED (2026-09-12): whether a Finalizer attached inside `Test.startTest()`
/ `Test.stopTest()` executes within the test transaction. The guide documents
`Test.getEventBus().deliver()` for delivering `BatchApexErrorEvent` messages
from failed batch jobs (`apexdev L17911-17930`) but names no equivalent hook
for Finalizers. Question to settle in a scratch org before writing an assertion
over `Amendment_Failure__c` rows with `Phase__c = 'ASYNC_POST'`: does
`PostingFinalizer.execute` run under `stopTest`? Until then, test the
Finalizer's branch logic by calling `execute(FinalizerContext)` with a stub, and
verify the real path in a sandbox run.

---

## 8. Metadata

`AmendmentPostingQueueable.cls-meta.xml` — the same shape for every class in
the package:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

`package.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Application_Log__c</members>
        <members>Contract_Amendment__c</members>
        <members>Amendment_Line__c</members>
        <members>Amendment_Failure__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Logger_Setting__mdt.Default</members>
        <name>CustomMetadata</name>
    </types>
    <types>
        <members>ApplicationLogger</members>
        <members>AmendmentException</members>
        <members>AmendmentValidationException</members>
        <members>AmendmentPricingException</members>
        <members>AmendmentPostingException</members>
        <members>ContractAmendmentService</members>
        <members>AmendmentPostingUnit</members>
        <members>AmendmentPostingQueueable</members>
        <members>ContractAmendmentController</members>
        <members>ContractAmendmentServiceTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 9. Deploy order

Deploy in this order; each step depends only on the ones above it.

| # | What | Why it is here |
|---|---|---|
| 1 | `Application_Log__c` object and its eight fields, from `templates/apex/custom_objects/` | `ApplicationLogger` will not compile without the object and every field it sets |
| 2 | `Logger_Setting__mdt` type from `templates/apex/cmdt/`, plus the `Default` record | `ApplicationLogger.getMinimumSeverity()` reads `Logger_Setting__mdt.getInstance('Default')`; a missing type is a compile error, a missing record only defaults to `INFOL` |
| 3 | `ApplicationLogger.cls` + `-meta.xml`, byte-identical to `templates/apex/ApplicationLogger.cls` | Every class in steps 6-9 calls it. Shipping a caller without it fails deploy with `Variable does not exist: ApplicationLogger` |
| 4 | `Contract_Amendment__c`, `Amendment_Line__c`, `Amendment_Failure__c` and their fields | The service classes reference the fields by name |
| 5 | Validation rule on `Amendment_Line__c` requiring `New_Annual_Value__c > 0` | The negative tests need a rejection the platform produces; without it `rejectedRowBecomesOneFailureRecord` passes vacuously |
| 6 | `AmendmentException`, then the three leaf exception classes | The leaves extend the base, so the base compiles first |
| 7 | `ContractAmendmentService`, `AmendmentPostingUnit` | Depend on the exception tree and the objects |
| 8 | `AmendmentPostingQueueable` | Calls `ContractAmendmentService.postLines` |
| 9 | `ContractAmendmentController` | Calls the Queueable and the exception tree |
| 10 | `ContractAmendmentServiceTest` | Last; it references everything above |

Steps 1-3 are the template-provenance requirement, not optional scaffolding:
this package cites `templates/apex/ApplicationLogger.cls`, so the deploy set has
to carry it.

---

## 10. Verification

Run the package checker against the source directory before deploying. It reads
`.cls` and `.trigger` files only — point `--manifest-dir` at the root that
contains them:

```bash
python3 skills/apex/error-handling-framework/scripts/check_error_handling_framework.py \
    --manifest-dir force-app/main/default
```

| Exit code | Output | Meaning |
|---|---|---|
| 0 | `No issues found.` | Every `.cls` / `.trigger` under the directory passed all six rules |
| 1 | one `ISSUE:` line per finding | At least one finding, or the directory does not exist, or it holds no Apex at all |

The three cases worth knowing before wiring this into a pipeline:

- A path that does not exist prints `ISSUE: Manifest directory not found: <dir>`
  and exits 1.
- An existing but Apex-free directory prints `ISSUE: No .cls or .trigger files
  found under <dir>` and exits 1. An empty directory is a failure, not a pass —
  a pipeline that points at the wrong folder gets told so instead of getting a
  green tick.
- Findings are ERROR-only. There is no WARN tier and no `--strict` flag; any
  finding exits 1.

What the six rules catch on the package above, and where each one is designed
not to fire:

| Rule | Fires on | Why this package is clean |
|---|---|---|
| AuraHandledException outside a controller | `throw new AuraHandledException(` in a file whose stem does not end `controller` / `ctrl` | The only two throws are in `ContractAmendmentController.cls` |
| Direct DML insert of a log record | `insert new Error_Log__c(` or `insert <name containing errorlog>` | Log writes go through `ApplicationLogger`; the only direct insert is `Amendment_Failure__c`, a business record |
| `getMessage()` into `AuraHandledException` | `new AuraHandledException(x.getMessage())` | Both controller throws pass a hand-written string plus the correlation id |
| `BatchApexErrorEvent` trigger without the `DoesExceedJobScopeMaxLength` guard | A `.trigger` on `BatchApexErrorEvent` that reads `evt.JobScope` | This package ships no trigger; the guarded version is in `SKILL.md` Pattern 3 |
| `EventBus.publish()` inside a for-loop | Any publish at a brace depth opened by a `for (` | This package publishes no events at all |
| Swallowed generic catch | `catch (Exception e)` with no rethrow, no `ErrorLogger` / `EventBus` in the following 8 lines, and a `System.debug` or `return null/false/0` | Every catch names a specific type and either logs through `ApplicationLogger` or rethrows |

A finding is a question, not a verdict — the swallowed-catch rule in particular
is a heuristic over an 8-line window and will miss a swallow that recovers on
line 10. Read the flagged line before changing it.
