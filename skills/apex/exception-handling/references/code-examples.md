# Code Examples — Exception Handling

A deployable exception slice for one service: a base custom exception carrying a typed error code and
a chained cause, a partial-success DML handler that maps every `Database.Error` back to the input row
that produced it, a savepoint/rollback path that obeys the callout constraint, an `@AuraEnabled`
wrapper that converts to `AuraHandledException` while `templates/apex/ApplicationLogger.cls` keeps the
real one, and a test class that asserts exception **type**, **message**, and `DmlException.getDmlIndex`
on a 200-row bulk failure.

## What This Builds

| Artifact | File | Why it exists |
|---|---|---|
| Canonical logger | `templates/apex/ApplicationLogger.cls` (deploy as-is — do not copy or rival it) | The durable sink. This skill decides *what* to catch; `apex/debug-and-logging` owns *where the record goes* |
| Canonical service base | `templates/apex/BaseService.cls` | Already supplies `beginTransaction`/`rollbackTransaction`/`logAndRethrow` and its own `ServiceException` inner class |
| Base custom exception | `CaseIntakeException.cls` | One level, a typed `Code` enum, and cause chaining — the alternative to a five-deep hierarchy |
| Service | `CaseIntakeService.cls` | Partial-success DML, per-row error mapping, the savepoint/callout rule |
| Controller | `CaseIntakeController.cls` | The only place `AuraHandledException` is constructed |
| Test | `CaseIntakeServiceTest.cls` | 200-row bulk failure; asserts type, message, `getNumDml`, `getDmlIndex` |
| Test data | `templates/apex/tests/TestDataFactory.cls` | `createCases(count, accountId, overrides)` — do not hand-roll a loop of `new Case()` |
| Manifest | `manifest/package.xml` | `ApexClass` members plus the `Intake_Error__c` field this slice writes |

## How To Read It

- **The hierarchy is two levels, not five.** `CaseIntakeException extends Exception` and nothing extends
  it. Granularity lives in the `Code` enum and the chained cause, not in class names. The guide's own
  example of an exception inheritance tree is two levels deep (`BaseException` / `OtherException`,
  Apex Developer Guide `apexdev` L40133–40148).
- **The class name has to end in `Exception`.** "To create your custom exception class, extend the
  built-in `Exception` class and make sure your class name ends with the word Exception"
  (`apexdev` L40143–40145). `CaseIntakeError` does not compile.
- **The typed code is set through a static factory, not a declared constructor.** The four documented
  ways to construct are no-arg, `String`, `Exception`, and `String` + `Exception` (`apexdev`
  L40151–40170). The factory uses the two-argument form and then assigns the public field, so the
  cause chain that `getCause()` returns is the platform's, not a copy.
  **UNVERIFIED (2026-09-05):** whether an Apex class extending `Exception` may *declare* its own
  constructor. `apexdev` L40128–40130 says exceptions "can have member variables, methods and
  constructors", but the compiler's treatment of a user-declared constructor on an `Exception`
  subclass is not stated anywhere in `apexdev.txt` or `apexrefguide.txt`. The static factory sidesteps
  the question — if you do declare a constructor, compile it in a scratch org before relying on it.
- **`Database.insert(records, false)` never throws for a row failure.** With `allOrNone` false, "the
  remainder of the DML operation can still succeed. You must iterate through the returned results to
  identify which records succeeded or failed" (`apexdev` L9060–9063). The mapping back to the input row
  is positional and documented: "the first element in the SaveResult array matches the first element
  passed in the sObject array, the second element corresponds with the second element, and so on"
  (`apexrefguide` L149984–149987).
- **`Database.Error` carries three things and only three**: `getFields()`, `getMessage()`,
  `getStatusCode()` returning a `StatusCode` enum value (`apexrefguide` L148674–148720). There is no
  row index on the error — the index is the position you were iterating.
- **The savepoint is not free and the callout is not allowed.** "Each savepoint you set counts against
  the governor limit for DML statements" (`apexdev` L8691), and a callout with an unreleased savepoint
  raises `System.CalloutException` with "All active Savepoints must be released before making callouts."
  (`apexdev` L8742–8750). Roll back, `Database.releaseSavepoint(sp)`, *then* call out (`apexdev`
  L8725–8741).
- **The controller logs the real exception and throws a different one.** The LWC guide's rule is
  "Handle only the errors you expect to see in the catch block. The rest should be propagated further"
  (Lightning Web Components Developer Guide, page `apex-error-handling`, `lwc_guide` L7535).

---

## `force-app/main/default/classes/CaseIntakeException.cls`

```apex
/**
 * CaseIntakeException — the ONE custom exception for the case-intake service.
 *
 * Naming is not stylistic: a custom exception class must extend Exception and its
 * name must end in "Exception" (Apex Developer Guide, Create Custom Exceptions,
 * apexdev L40143-40145).
 *
 * Granularity lives in Code + getCause(), not in a class hierarchy. Callers switch
 * on the code; operators read the chained cause.
 *
 * Constructed through of(...) rather than a declared constructor so that only the
 * four documented Exception constructor forms are used (apexdev L40151-40170):
 *     new CaseIntakeException()
 *     new CaseIntakeException(String)
 *     new CaseIntakeException(Exception)
 *     new CaseIntakeException(String, Exception)
 */
public virtual class CaseIntakeException extends Exception {

    public enum Code {
        VALIDATION_FAILED,     // a business precondition the user can fix
        ROW_REJECTED,          // one or more rows failed a partial-success DML
        DOWNSTREAM_UNAVAILABLE,// the scoring service did not answer
        CONFIGURATION_MISSING  // a Custom Metadata row or Named Credential is absent
    }

    /**
     * Public field, not a constructor argument. Never put personal data here or in
     * the message: "make sure that test error messages and exception details do not
     * contain any personal data ... create an Exception subclass with new properties
     * that hold the personal data. Then, do not include subclass property information
     * in the exception message string." (apexdev L40308-40313)
     */
    public Code errorCode = Code.VALIDATION_FAILED;

    /** Correlation id so a support ticket can be joined to Application_Log__c. */
    public String correlationId;

    /** Row positions in the caller list that failed, when errorCode is ROW_REJECTED. */
    public List<Integer> failedRowIndexes = new List<Integer>();

    public static CaseIntakeException of(Code errorCode, String message, Exception cause) {
        CaseIntakeException e = (cause == null)
            ? new CaseIntakeException(message)
            : new CaseIntakeException(message, cause);
        e.errorCode = errorCode;
        e.correlationId = System.Request.getCurrent().getRequestId();
        return e;
    }

    public static CaseIntakeException of(Code errorCode, String message) {
        return of(errorCode, message, null);
    }
}
```

### `force-app/main/default/classes/CaseIntakeException.cls-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

Every `.cls` in this slice takes the same `-meta.xml`. `67.0` is the Summer '26 Metadata API version
(Metadata API Developer Guide, `api_meta` L2).

---

## `force-app/main/default/classes/CaseIntakeService.cls`

```apex
/**
 * CaseIntakeService — the partial-success + savepoint + rollback reference.
 *
 * Extends templates/apex/BaseService.cls, which already provides
 * beginTransaction() / rollbackTransaction() / logAndRethrow(). Do not re-declare
 * those helpers here.
 *
 * Logging goes through templates/apex/ApplicationLogger.cls. This class does not
 * define a logger; apex/debug-and-logging owns that decision.
 */
public with sharing class CaseIntakeService extends BaseService {

    private static final String SRC = 'CaseIntakeService';

    /** One row of feedback, positionally aligned to the caller list. */
    public class RowOutcome {
        @AuraEnabled public Integer rowIndex;
        @AuraEnabled public Id recordId;
        @AuraEnabled public Boolean success;
        @AuraEnabled public String statusCode;
        @AuraEnabled public String message;
        @AuraEnabled public List<String> fields = new List<String>();
    }

    /**
     * Partial-success insert. Returns one RowOutcome per input row.
     *
     * allOrNone = false means NO DmlException is thrown for a row failure: "If the
     * allOrNone parameter of a Database DML method is set to false and a record
     * fails, the remainder of the DML operation can still succeed. You must iterate
     * through the returned results to identify which records succeeded or failed."
     * (apexdev L9060-9063)
     *
     * The mapping back to the input row is positional, not by Id: "the first element
     * in the SaveResult array matches the first element passed in the sObject array"
     * (apexrefguide L149984-149987). Failed rows have no Id, so index is the only key.
     */
    public List<RowOutcome> insertAllowingPartialFailure(List<Case> cases) {
        List<RowOutcome> outcomes = new List<RowOutcome>();
        if (cases == null || cases.isEmpty()) {
            return outcomes;
        }

        List<Database.SaveResult> results = Database.insert(cases, false);
        List<Integer> failedRows = new List<Integer>();

        for (Integer i = 0; i < results.size(); i++) {
            Database.SaveResult sr = results[i];
            RowOutcome row = new RowOutcome();
            row.rowIndex = i;
            row.success = sr.isSuccess();

            if (sr.isSuccess()) {
                row.recordId = sr.getId();
                outcomes.add(row);
                continue;
            }

            failedRows.add(i);
            // Database.Error exposes exactly getFields(), getMessage(), getStatusCode()
            // (apexrefguide L148674-148720). getStatusCode() returns a StatusCode enum.
            List<String> parts = new List<String>();
            for (Database.Error err : sr.getErrors()) {
                parts.add(String.valueOf(err.getStatusCode()) + ': ' + err.getMessage());
                row.fields.addAll(err.getFields());
                if (row.statusCode == null) {
                    row.statusCode = String.valueOf(err.getStatusCode());
                }
            }
            row.message = String.join(parts, ' | ');
            outcomes.add(row);
        }

        if (!failedRows.isEmpty()) {
            // One log line for the whole operation, at the service boundary.
            ApplicationLogger.warn(
                SRC + '.insertAllowingPartialFailure',
                failedRows.size() + ' of ' + cases.size() + ' rows rejected; indexes ' + failedRows
            );
            ApplicationLogger.flush();
        }
        return outcomes;
    }

    /**
     * All-or-none intake with a compensating callout.
     *
     * Order is forced by the platform, not by taste:
     *   1. setSavepoint()          - counts against the DML STATEMENT limit (apexdev L8691)
     *   2. DML
     *   3. on failure: rollback(sp) then releaseSavepoint(sp)
     *   4. only then the callout
     *
     * Calling out while a savepoint is still active raises System.CalloutException
     * carrying "All active Savepoints must be released before making callouts."
     * (apexdev L8742-8750). Calling out with uncommitted DML raises the same type
     * carrying "You have uncommitted work pending. Please commit or rollback before
     * calling out." (apexdev L8752-8770).
     */
    public void intakeOrCompensate(List<Case> cases, String correlationId) {
        Savepoint sp = beginTransaction();
        try {
            insert cases;
        } catch (DmlException e) {
            rollbackTransaction(sp);
            Database.releaseSavepoint(sp);   // must precede the callout
            notifyIntakeFailed(correlationId, summarize(e));
            ApplicationLogger.error(SRC + '.intakeOrCompensate', e);
            ApplicationLogger.flush();
            CaseIntakeException wrapped = CaseIntakeException.of(
                CaseIntakeException.Code.ROW_REJECTED,
                'Case intake could not be saved.',
                e
            );
            for (Integer i = 0; i < e.getNumDml(); i++) {
                wrapped.failedRowIndexes.add(e.getDmlIndex(i));
            }
            throw wrapped;
        }
    }

    /**
     * Turns a DmlException into an operator-readable, PII-free summary.
     *
     * getNumDml() is the number of FAILED rows, not the list size, and getDmlIndex(i)
     * is "the original row position of the ith failed row" (apexrefguide L215140,
     * L215160). i and getDmlIndex(i) are different numbers - never index the input
     * list with i.
     */
    @TestVisible
    private static String summarize(DmlException e) {
        List<String> lines = new List<String>();
        for (Integer i = 0; i < e.getNumDml(); i++) {
            lines.add(
                'row ' + e.getDmlIndex(i)
                + ' [' + e.getDmlType(i) + '] '
                + String.join(e.getDmlFieldNames(i), ',')
            );
        }
        return String.join(lines, '; ');
    }

    /** Replace with templates/apex/HttpClient.cls in a real build. */
    private void notifyIntakeFailed(String correlationId, String summary) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:Intake_Ops/v1/failures');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');
        req.setBody(JSON.serialize(new Map<String, Object>{
            'correlationId' => correlationId,
            'summary' => summary
        }));
        try {
            new Http().send(req);
        } catch (System.CalloutException ce) {
            // The compensating notification is best-effort. It must never replace
            // the exception the caller is about to receive.
            ApplicationLogger.warn(SRC + '.notifyIntakeFailed', ce.getMessage());
        }
    }
}
```

---

## `force-app/main/default/classes/CaseIntakeController.cls`

```apex
/**
 * CaseIntakeController — the ONLY place AuraHandledException is constructed.
 *
 * AuraHandledException "returns a custom error message to a JavaScript controller"
 * (apexrefguide L214924). The LWC guide's own rule for this boundary is: "Handle
 * only the errors you expect to see in the catch block. The rest should be
 * propagated further." (lwc_guide, page apex-error-handling, L7535)
 *
 * Unhandled exceptions from an @AuraEnabled method do NOT produce an exception
 * email: "Emails are not sent for exceptions encountered with anonymous Apex
 * executions or with Apex methods accessed by Aura components and Lightning web
 * components via the @AuraEnabled annotation." (apexdev L39609-39610)
 * That is why the log write below is not optional - it is the only record.
 */
public with sharing class CaseIntakeController {

    private static final String SRC = 'CaseIntakeController';

    @AuraEnabled
    public static List<CaseIntakeService.RowOutcome> submitIntake(List<Case> cases) {
        try {
            return new CaseIntakeService().insertAllowingPartialFailure(cases);
        } catch (CaseIntakeException e) {
            throw toAura(e, userMessageFor(e.errorCode), e.correlationId);
        } catch (QueryException e) {
            throw toAura(e, 'The record you asked for is no longer available.', null);
        } catch (DmlException e) {
            // Deliberately NOT e.getMessage(): a DmlException message carries the
            // failing field API names and the validation rule text.
            throw toAura(e, 'The case could not be saved. Check the highlighted fields.', null);
        }
        // Anything else - NullPointerException, a defect - is left to propagate.
        // LimitException cannot be caught here anyway (apexdev L39722-39728).
    }

    /**
     * Logs the real exception, returns a scrubbed one.
     *
     * setMessage is on the common Exception method table (apexrefguide L215122) and
     * is used here so the message the client reads is set explicitly rather than
     * inherited from whatever the constructor chose.
     */
    private static AuraHandledException toAura(Exception cause, String safeMessage, String correlationId) {
        String reference = String.isBlank(correlationId)
            ? System.Request.getCurrent().getRequestId()
            : correlationId;
        ApplicationLogger.error(SRC, cause);
        ApplicationLogger.flush();

        AuraHandledException ahe = new AuraHandledException(safeMessage + ' Reference: ' + reference);
        ahe.setMessage(safeMessage + ' Reference: ' + reference);
        return ahe;
    }

    private static String userMessageFor(CaseIntakeException.Code errorCode) {
        switch on errorCode {
            when VALIDATION_FAILED       { return 'Some details are missing. Review the form and try again.'; }
            when ROW_REJECTED            { return 'Some rows could not be saved. Download the results file for detail.'; }
            when DOWNSTREAM_UNAVAILABLE  { return 'Case scoring is temporarily unavailable. Your case was saved.'; }
            when else                    { return 'Something went wrong. Support has the detail.'; }
        }
    }
}
```

---

## `force-app/main/default/classes/CaseIntakeServiceTest.cls`

```apex
/**
 * CaseIntakeServiceTest — asserts exception TYPE, MESSAGE and getDmlIndex on a
 * 200-row bulk failure, plus the partial-success mapping.
 *
 * Records come from templates/apex/tests/TestDataFactory.cls
 * (createCases(count, accountId, overrides)) - do not hand-roll the list.
 *
 * Assert.fail() marks the "this line must not be reached" boundary. Note that the
 * assertion failure itself is NOT catchable by the surrounding catch: "You cannot,
 * however, catch the assertion failure in the try/catch block even though it is
 * logged as an exception." (apexrefguide L200594-200595). That is what makes the
 * try { call; Assert.fail(); } catch (X e) { } shape safe.
 */
@IsTest
private class CaseIntakeServiceTest {

    private static final Integer BULK = 200;

    @TestSetup
    static void setup() {
        insert TestDataFactory.createAccounts(1, null);
    }

    private static Id accountId() {
        return [SELECT Id FROM Account LIMIT 1].Id;
    }

    @IsTest
    static void partialFailureMapsEveryRejectedRowToItsIndex() {
        List<Case> cases = TestDataFactory.createCases(BULK, accountId(), null);
        // Poison three known positions with an over-length Subject.
        Set<Integer> poisoned = new Set<Integer>{ 0, 99, 199 };
        for (Integer i : poisoned) {
            cases[i].Subject = 'x'.repeat(300);
        }

        Test.startTest();
        List<CaseIntakeService.RowOutcome> outcomes =
            new CaseIntakeService().insertAllowingPartialFailure(cases);
        Test.stopTest();

        Assert.areEqual(BULK, outcomes.size(), 'One outcome per input row, successes included.');
        Set<Integer> reported = new Set<Integer>();
        for (CaseIntakeService.RowOutcome row : outcomes) {
            if (!row.success) {
                reported.add(row.rowIndex);
                Assert.isNotNull(row.statusCode, 'A rejected row must carry a StatusCode.');
                Assert.isNull(row.recordId, 'A rejected row has no Id to report.');
            }
        }
        Assert.areEqual(poisoned, reported, 'Rejected indexes must match the poisoned positions.');
    }

    @IsTest
    static void allOrNoneFailureThrowsTypedExceptionCarryingOriginalRowPositions() {
        List<Case> cases = TestDataFactory.createCases(BULK, accountId(), null);
        cases[137].Subject = 'x'.repeat(300);

        Test.startTest();
        try {
            new CaseIntakeService().intakeOrCompensate(cases, 'CORR-1');
            Assert.fail('Expected CaseIntakeException for the over-length Subject on row 137.');
        } catch (CaseIntakeException e) {
            // 1. TYPE
            Assert.areEqual(
                'CaseIntakeException', e.getTypeName(),
                'getTypeName reports the thrown type (apexdev L40001-40006).'
            );
            // 2. MESSAGE - the safe one, not the platform one
            Assert.areEqual('Case intake could not be saved.', e.getMessage());
            // 3. CAUSE CHAIN - the DmlException must survive the wrap
            Assert.isInstanceOfType(
                e.getCause(), DmlException.class,
                'The two-argument constructor keeps the inner exception (apexdev L40270-40277).'
            );
            // 4. ORIGINAL ROW POSITION - getDmlIndex, not the loop counter
            DmlException dml = (DmlException) e.getCause();
            Assert.areEqual(1, dml.getNumDml(), 'getNumDml counts FAILED rows, not list size.');
            Assert.areEqual(
                137, dml.getDmlIndex(0),
                'getDmlIndex(i) is the original row position of the ith failed row (apexrefguide L215140).'
            );
            Assert.areEqual(new List<Integer>{ 137 }, e.failedRowIndexes);
        }
        Test.stopTest();

        Assert.areEqual(0, [SELECT COUNT() FROM Case], 'All-or-none means nothing committed.');
    }

    @IsTest
    static void controllerReturnsAuraHandledExceptionAndNeverTheRawDmlMessage() {
        List<Case> cases = TestDataFactory.createCases(2, accountId(), null);
        cases[1].Subject = 'x'.repeat(300);

        Test.startTest();
        List<CaseIntakeService.RowOutcome> outcomes = CaseIntakeController.submitIntake(cases);
        Test.stopTest();

        Assert.isTrue(outcomes[0].success);
        Assert.isFalse(outcomes[1].success);
        Assert.isTrue(
            outcomes[1].message.contains('STRING_TOO_LONG')
                || outcomes[1].message.contains('FIELD_INTEGRITY_EXCEPTION'),
            'The per-row message keeps the StatusCode for the operator: ' + outcomes[1].message
        );
    }
}
```

> The `Subject` length ceiling and the exact `StatusCode` a 300-character `Subject` produces are org- and
> object-specific. UNVERIFIED (2026-09-05): `Case.Subject` field length is in the Object Reference but the
> resulting `StatusCode` value for an over-length text field is not stated in `object_reference.txt`,
> `apexdev.txt` or `apexrefguide.txt`. Run the test once and pin the assertion to what the org returns
> before relying on it in CI.

---

## `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ApplicationLogger</members>
        <members>CaseIntakeException</members>
        <members>CaseIntakeService</members>
        <members>CaseIntakeController</members>
        <members>CaseIntakeServiceTest</members>
        <members>BaseService</members>
        <members>TestDataFactory</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Intake_Ops</members>
        <name>NamedCredential</name>
    </types>
    <version>67.0</version>
</Package>
```

## Deploy Order

1. `templates/apex/custom_objects/Application_Log__c` and `Logger_Setting__mdt` with a `Default` record,
   then `ApplicationLogger`. Without the `Default` custom metadata row the logger falls back to `INFOL`
   and writes more than you expect (`templates/apex/ApplicationLogger.cls`, `getMinimumSeverity`).
2. `BaseService` — `CaseIntakeService` will not compile without it.
3. `CaseIntakeException`, then `CaseIntakeService`, then `CaseIntakeController`.
4. `Intake_Ops` Named Credential — `intakeOrCompensate` fails at runtime, not compile time, without it.
5. `TestDataFactory`, then `CaseIntakeServiceTest`.

A single `sf project deploy start` resolves this ordering itself; the list matters when the change is
split across releases.

```bash
# Validate without saving anything
sf project deploy start --dry-run -d "force-app/main/default" --target-org <alias>

sf project deploy start -d "force-app/main/default" --target-org <alias>
```

## Verification

```bash
# UNVERIFIED (2026-09-05): the `sf apex` command group is documented in the Salesforce CLI Command
# Reference, which is not in the grounding corpus (only `sf project deploy start` appears, api_meta
# L3985). Confirm the flags with `sf apex run test --help` before wiring this into CI.
sf apex run test --tests CaseIntakeServiceTest --result-format human --code-coverage --wait 10 --target-org <alias>
```

Org-side checks that do not depend on the CLI:

```sql
-- 1. The service logged once per failed operation, not once per failed row.
SELECT Source__c, Severity__c, Exception_Type__c, Request_Id__c, Message__c, CreatedDate
FROM Application_Log__c
WHERE Source__c LIKE 'CaseIntake%' AND CreatedDate = TODAY
ORDER BY CreatedDate DESC
LIMIT 50

-- 2. Nobody is still relying on the unhandled-exception email. It is capped at 10 per hour per
--    application server, suppresses duplicates, and is never sent for @AuraEnabled calls
--    (apexdev L39606-39613). Confirm a monitored address is configured before you rely on it.
SELECT Id, Email, UserId FROM ApexEmailNotification
```

Then run the package checker over the source tree before deploying:

```bash
python3 skills/apex/exception-handling/scripts/check_exception_handling.py \
    --manifest-dir force-app/main/default
```
