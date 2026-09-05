# Code Examples — Invocable Methods

A complete, deployable Apex action for Flow: one `@InvocableMethod` boundary class, a bulk-safe
service behind it (one SOQL and one DML for N interviews), per-input results returned **in input
order**, a `callout=true` variant, the test class that drives 200 inputs, and the `actionCalls`
fragment that wires it into a flow with a fault path.

Every platform claim below carries a line reference into the Apex Developer Guide v67.0
(`apexdev.txt`, Summer '26 — L1–2), the Apex Reference Guide v67.0 (`apexrefguide.txt`), the
Metadata API Developer Guide v67.0 (`api_meta.txt`), or the REST API Developer Guide v67.0
(`api_rest.txt`).

Canonical building blocks reused rather than re-invented:

| Path | Used for |
|---|---|
| `templates/apex/tests/TestDataFactory.cls` | `createAccounts(count, overrides)` and `createCases(count, accountId, overrides)` for the 200-record volume test |
| `templates/apex/tests/BulkTestPattern.cls` | the `Test.startTest()` + `Limits` headroom assertion shape this test class follows |
| `templates/apex/ApplicationLogger.cls` | `warn` / `error(source, Exception)` / `flush()` — a durable row when one input fails while the other 199 succeed |
| `templates/apex/SecurityUtils.cls` | `requireUpdatable(Schema.SObjectType)` when the action must fail closed rather than silently strip fields |
| `templates/apex/HttpClient.cls` | the `callout=true` variant in §5 — Named Credential, timeout, transient retry |
| `templates/apex/tests/MockHttpResponseGenerator.cls` | `Test.setMock` for the callout variant's test |

Not used here: `templates/apex/TriggerHandler.cls` and `TriggerControl.cls` are the trigger
boundary, not the Flow boundary. If the same service must be reachable from both, put the logic in
the service and give each entry point its own thin adapter.

---

## 1. Contract

| Item | Value | Source |
|---|---|---|
| Entry point | `CaseEscalationAction.escalate(List<Request>)` | — |
| Method visibility | `public static`, on an outer class | "The invocable method must be static and public or global, and its class must be an outer class." (apexdev L5421) |
| Methods per class | exactly one annotated | "Only one method in a class can have the InvocableMethod annotation." (apexdev L5422) |
| Parameters | exactly one, a `List<Request>` | "There can be at most one input parameter" (apexdev L5432) |
| Return | `List<Result>`, size N, index-aligned | "the Inputs and Outputs must match on both the size and the order… the i-th Output entry must correspond to the i-th Input entry" (apexdev L5456–5457) |
| Failure of one input | reported in that input's `Result`, never thrown | "To handle exceptions within an invocable method, wrap the results in an Apex object that reports failures. The execution of the invocable method must run and return the same number of results as inputs received even if errors occur." (apexdev L5318–5319) |
| Failure of the whole invocation | uncaught exception → the flow's `faultConnector` path | `faultConnector` "Specifies which node to execute if the action call results in an error." (api_meta L68479) |
| Governor budget for N=200 | 1 SOQL of 100, 1 DML of 150 | apexdev L19544, L19554 |

`Request` and `Result` are inner classes of the boundary class. The guide's own samples nest the
wrapper types this way (apexdev L5271–5287, L5630–5640), and the outer-class rule applies to the
class carrying the annotation, not to the wrapper types.

---

## 2. Boundary class — `CaseEscalationAction.cls`

```apex
/**
 * CaseEscalationAction — the Flow-facing adapter for case escalation.
 *
 * Transport only: it declares the contract, hands the whole list to the service,
 * and hands the whole list of results back. No SOQL and no DML live in this file.
 *
 * Grounding:
 *  - "The invocable method must be static and public or global, and its class must be
 *     an outer class."                                                  (apexdev L5421)
 *  - "Only one method in a class can have the InvocableMethod annotation."
 *                                                                       (apexdev L5422)
 *  - "There can be at most one input parameter"                         (apexdev L5432)
 *  - label / description / category are optional modifiers; with no category the
 *    action appears under Uncategorized in Flow Builder.        (apexdev L5404–5417)
 *  - "If a flow invokes Apex, the running user must have the corresponding Apex class
 *     security set in their user profile or permission set."             (apexdev L5172)
 */
public with sharing class CaseEscalationAction {

    /**
     * Input wrapper. Only global and public member variables can be invocable
     * variables (apexdev L5718); a static, final, protected or private field, or a
     * property, is rejected (apexdev L5719–5723).
     *
     * Starting in API version 66.0 an invocable-parameter class must have a visible
     * no-argument constructor (apexdev L5737–5739). This class declares no constructor
     * at all, so it keeps the implicit public default one.
     */
    public class Request {

        @InvocableVariable(
            label='Case Id'
            description='The Case to escalate. Must be a Case Id the running user can edit.'
            required=true
        )
        public Id caseId;

        @InvocableVariable(
            label='Escalation Reason'
            description='Free text stored on the Case and written to the escalation log.'
            placeholderText='Customer breached SLA twice this quarter'
            required=true
        )
        public String reason;

        // defaultValue and required cannot be combined: "The defaultValue modifier
        // throws an error when used with required." (apexdev L5693)
        @InvocableVariable(
            label='Target Priority'
            description='Priority to set. Defaults to High when the flow leaves it empty.'
            defaultValue='High'
        )
        public String targetPriority;
    }

    /**
     * Output wrapper. `required` is accepted on output variables but ignored:
     * "The value is ignored for output variables." (apexdev L5691) — so this class
     * does not use it, to avoid implying an obligation the platform never enforces.
     */
    public class Result {

        @InvocableVariable(label='Success' description='True when this Case was escalated.')
        public Boolean success;

        @InvocableVariable(label='Case Id' description='Echo of the input Case Id, so the flow can correlate.')
        public Id caseId;

        @InvocableVariable(label='Error Message' description='Null on success. A user-readable reason on failure.')
        public String errorMessage;

        @InvocableVariable(label='Previous Priority' description='The Priority the Case held before escalation.')
        public String previousPriority;
    }

    @InvocableMethod(
        label='Escalate Cases'
        description='Raises Case priority, stamps the escalation reason, and returns one result per input in the same order.'
        category='Case Management'
    )
    public static List<Result> escalate(List<Request> requests) {
        // The whole list crosses the boundary in one call. Never loop here and never
        // slice the list: the service owns the single query and the single DML.
        return CaseEscalationService.escalate(requests);
    }
}
```

`CaseEscalationAction.cls-meta.xml` — `apiVersion` is the class's own API version, pinned at
creation (`ApexClass.apiVersion`, api_meta L22242):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

### How to read the annotation

- **`label`** is what an admin sees as the action name on the Flow canvas; the default is the
  method name (apexdev L5404–5405). `escalate` is a bad canvas label; `Escalate Cases` is not.
- **`description`** defaults to Null (apexdev L5406). Leave it null and the admin has nothing but
  the label to reason from — and for an Agentforce action the reasoning engine uses exactly these
  two strings to decide whether to call the action (apexdev L43664–43666).
- **`category`** decides which Flow Builder group the action lands in; with no category "actions
  appear under Uncategorized" (apexdev L5411–5412).
- **`callout`** is absent here because this method touches no external system; the default is
  `false` (apexdev L5407–5408). §5 shows the variant that needs it.
- **`iconName`** and **`configurationEditor`** are the two remaining modifiers (apexdev L5413–5417).
  A custom property editor is an LWC — see `lwc/custom-property-editor-for-flow`.

---

## 3. Service — `CaseEscalationService.cls`

One SOQL and one DML for N interviews, and a result list built by walking the **input** list so the
order can never drift.

```apex
/**
 * CaseEscalationService — the bulk-safe body behind CaseEscalationAction.
 *
 * Shape: collect ids -> one query -> build the DML list -> one partial-success DML ->
 * map the save results back onto the input positions.
 *
 * Governor budget for a 200-interview batch: 1 of the 100 SOQL queries and 1 of the
 * 150 DML statements a synchronous transaction gets (apexdev L19544, L19554).
 */
public inherited sharing class CaseEscalationService {

    private static final String SOURCE = 'CaseEscalationService';
    private static final String DEFAULT_PRIORITY = 'High';

    public static List<CaseEscalationAction.Result> escalate(List<CaseEscalationAction.Request> requests) {

        // 1. Seed one result per input, in input order, before anything can fail.
        //    "The execution of the invocable method must run and return the same number
        //     of results as inputs received even if errors occur." (apexdev L5318–5319)
        List<CaseEscalationAction.Result> results = new List<CaseEscalationAction.Result>();
        for (CaseEscalationAction.Request req : requests) {
            CaseEscalationAction.Result r = new CaseEscalationAction.Result();
            r.caseId = req == null ? null : req.caseId;
            r.success = false;
            results.add(r);
        }
        if (requests.isEmpty()) {
            return results;
        }

        // 2. Collect the ids. A Set de-duplicates, so two interviews escalating the
        //    same Case still cost one row in the query and one row in the DML.
        Set<Id> caseIds = new Set<Id>();
        for (CaseEscalationAction.Request req : requests) {
            if (req != null && req.caseId != null) {
                caseIds.add(req.caseId);
            }
        }

        // 3. One query. WITH USER_MODE enforces FLS, CRUD and sharing for the running
        //    user, matching the guide's own invocable sample (apexdev L5194–5197).
        Map<Id, Case> casesById = new Map<Id, Case>([
            SELECT Id, Priority, Status, IsClosed
            FROM Case
            WHERE Id IN :caseIds
            WITH USER_MODE
        ]);

        // 4. Build the DML list. positionsByCaseId remembers every input index that
        //    asked for a given Case, so one save result can settle several inputs.
        List<Case> toUpdate = new List<Case>();
        Map<Id, List<Integer>> positionsByCaseId = new Map<Id, List<Integer>>();
        Map<Id, Integer> dmlIndexByCaseId = new Map<Id, Integer>();

        for (Integer i = 0; i < requests.size(); i++) {
            CaseEscalationAction.Request req = requests[i];
            CaseEscalationAction.Result r = results[i];

            if (req == null || req.caseId == null) {
                r.errorMessage = 'Case Id was not supplied.';
                continue;
            }
            Case existing = casesById.get(req.caseId);
            if (existing == null) {
                // Invisible to this user or deleted. Not an exception: this input fails,
                // the other 199 must still be processed.
                r.errorMessage = 'Case ' + req.caseId + ' was not found or is not visible to you.';
                continue;
            }
            if (existing.IsClosed) {
                r.errorMessage = 'Case ' + req.caseId + ' is closed and cannot be escalated.';
                continue;
            }
            if (String.isBlank(req.reason)) {
                r.errorMessage = 'Escalation Reason is required.';
                continue;
            }

            r.previousPriority = existing.Priority;

            if (!dmlIndexByCaseId.containsKey(req.caseId)) {
                Case toSave = new Case(
                    Id = req.caseId,
                    Priority = String.isBlank(req.targetPriority) ? DEFAULT_PRIORITY : req.targetPriority,
                    Escalation_Reason__c = req.reason,
                    IsEscalated = true
                );
                dmlIndexByCaseId.put(req.caseId, toUpdate.size());
                toUpdate.add(toSave);
                positionsByCaseId.put(req.caseId, new List<Integer>());
            }
            positionsByCaseId.get(req.caseId).add(i);
        }

        if (toUpdate.isEmpty()) {
            return results;
        }

        // 5. One DML, allOrNone = false so a single row-level failure does not roll the
        //    other 199 back, and USER_MODE so the update honours the running user's FLS.
        List<Database.SaveResult> saveResults =
            Database.update(toUpdate, false, AccessLevel.USER_MODE);

        // 6. Fold the save results back onto the input positions.
        for (Id caseId : positionsByCaseId.keySet()) {
            Database.SaveResult sr = saveResults[dmlIndexByCaseId.get(caseId)];
            String failure = null;
            if (!sr.isSuccess()) {
                List<String> messages = new List<String>();
                for (Database.Error err : sr.getErrors()) {
                    messages.add(err.getStatusCode() + ': ' + err.getMessage());
                }
                failure = String.join(messages, ' | ');
                ApplicationLogger.warn(SOURCE, 'Escalation failed for ' + caseId + ' — ' + failure);
            }
            for (Integer position : positionsByCaseId.get(caseId)) {
                results[position].success = sr.isSuccess();
                results[position].errorMessage = failure;
            }
        }
        ApplicationLogger.flush();
        return results;
    }
}
```

### How to read the service

- **The result list is seeded first.** Building results only on the success path is how an action
  ends up returning 197 entries for 200 inputs, which breaks the index alignment the platform
  requires (apexdev L5456–5457).
- **`Database.update(records, false, AccessLevel.USER_MODE)`** gives per-row outcomes instead of an
  all-or-nothing failure. The guide's own `AccountInsertAction` sample uses exactly this shape —
  `Database.insert(accounts, false, AccessLevel.USER_MODE)` and then walks `SaveResult`s to build a
  correspondingly-sized output list (apexdev L5220–5236).
- **De-duplication is deliberate.** Two interviews can carry the same record. Updating the same Id
  twice in one DML list raises a duplicate-Id error; `dmlIndexByCaseId` collapses them and
  `positionsByCaseId` fans the one outcome back out to both inputs.
- **`IsEscalated` is writable.** The Object Reference lists its properties as "Create, Defaulted on
  create, Filter, Group, Sort, Update" and states "You can set this flag via the API"
  (object_reference L62470–62477) — so the DML above is legal, and setting it does not itself
  start an escalation rule.
- **`Escalation_Reason__c`** is a custom Text field on Case that the package.xml in §7 does not
  create. Add it, or drop the assignment.

---

## 4. Test class — `CaseEscalationActionTest.cls`

200 inputs, order asserted explicitly, governor headroom asserted.

```apex
/**
 * CaseEscalationActionTest — drives the action at flow-batch volume.
 *
 * The guide's own invocable test calls the annotated method directly and asserts
 * per-input results positionally (apexdev L5363–5395); this class does the same at
 * 200 inputs, the volume a record-triggered flow reaches.
 *
 * Uses templates/apex/tests/TestDataFactory.cls for seed data, and follows the
 * headroom-assertion shape in templates/apex/tests/BulkTestPattern.cls.
 */
@IsTest
private class CaseEscalationActionTest {

    private static final Integer BULK = 200;

    @TestSetup
    static void setup() {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;
        insert TestDataFactory.createCases(BULK, accounts[0].Id, new Map<String, Object>{
            'Priority' => 'Low',
            'Status' => 'New'
        });
    }

    @IsTest
    static void returnsOneResultPerInputInInputOrder() {
        List<Case> cases = [SELECT Id FROM Case ORDER BY CaseNumber LIMIT :BULK];
        Assert.areEqual(BULK, cases.size(), 'Setup must create ' + BULK + ' cases');

        List<CaseEscalationAction.Request> requests = new List<CaseEscalationAction.Request>();
        for (Integer i = 0; i < BULK; i++) {
            CaseEscalationAction.Request req = new CaseEscalationAction.Request();
            req.caseId = cases[i].Id;
            req.reason = 'SLA breach ' + i;
            req.targetPriority = 'High';
            requests.add(req);
        }

        Test.startTest();
        List<CaseEscalationAction.Result> results = CaseEscalationAction.escalate(requests);
        Test.stopTest();

        // (1) Size must match. This is the contract, not a nicety (apexdev L5456–5457).
        Assert.areEqual(BULK, results.size(), 'Output list must be the same size as the input list');

        // (2) Order must match: result[i] must belong to request[i].
        for (Integer i = 0; i < BULK; i++) {
            Assert.areEqual(
                requests[i].caseId,
                results[i].caseId,
                'Result ' + i + ' must correspond to input ' + i
            );
            Assert.isTrue(results[i].success, 'Result ' + i + ' should have succeeded: ' + results[i].errorMessage);
            Assert.areEqual('Low', results[i].previousPriority, 'Result ' + i + ' should echo the pre-escalation priority');
        }

        // (3) The records really changed.
        Assert.areEqual(
            BULK,
            [SELECT COUNT() FROM Case WHERE Priority = 'High' AND IsEscalated = true],
            'Every case should be escalated'
        );
    }

    @IsTest
    static void staysWithinGovernorLimitsAt200Inputs() {
        List<Case> cases = [SELECT Id FROM Case LIMIT :BULK];
        List<CaseEscalationAction.Request> requests = new List<CaseEscalationAction.Request>();
        for (Case c : cases) {
            CaseEscalationAction.Request req = new CaseEscalationAction.Request();
            req.caseId = c.Id;
            req.reason = 'Volume probe';
            requests.add(req);
        }

        Test.startTest();
        Integer queriesBefore = Limits.getQueries();
        Integer dmlBefore = Limits.getDmlStatements();
        CaseEscalationAction.escalate(requests);
        Integer queriesUsed = Limits.getQueries() - queriesBefore;
        Integer dmlUsed = Limits.getDmlStatements() - dmlBefore;
        Test.stopTest();

        // The action is one of several things a flow does in a transaction, so it must
        // consume a constant, not a per-input, share of the 100 SOQL / 150 DML budget
        // (apexdev L19544, L19554).
        Assert.areEqual(1, queriesUsed, 'Action must issue exactly one SOQL query for N inputs');
        Assert.areEqual(1, dmlUsed, 'Action must issue exactly one DML statement for N inputs');
    }

    @IsTest
    static void reportsPerInputFailuresWithoutThrowing() {
        List<Case> cases = [SELECT Id FROM Case LIMIT 2];

        CaseEscalationAction.Request good = new CaseEscalationAction.Request();
        good.caseId = cases[0].Id;
        good.reason = 'Valid';

        CaseEscalationAction.Request missingReason = new CaseEscalationAction.Request();
        missingReason.caseId = cases[1].Id;
        missingReason.reason = '';

        CaseEscalationAction.Request unknownCase = new CaseEscalationAction.Request();
        unknownCase.caseId = null;
        unknownCase.reason = 'Orphan';

        Test.startTest();
        List<CaseEscalationAction.Result> results = CaseEscalationAction.escalate(
            new List<CaseEscalationAction.Request>{ good, missingReason, unknownCase }
        );
        Test.stopTest();

        // Three inputs in, three results out — the failures are data, not exceptions.
        Assert.areEqual(3, results.size(), 'Failures must not shrink the output list');
        Assert.isTrue(results[0].success, 'Input 0 should succeed');
        Assert.isFalse(results[1].success, 'Input 1 should fail on the blank reason');
        Assert.isFalse(results[2].success, 'Input 2 should fail on the null Case Id');
        Assert.areEqual('Escalation Reason is required.', results[1].errorMessage);
    }

    @IsTest
    static void handlesTheEmptyList() {
        Test.startTest();
        List<CaseEscalationAction.Result> results =
            CaseEscalationAction.escalate(new List<CaseEscalationAction.Request>());
        Test.stopTest();
        Assert.areEqual(0, results.size(), 'An empty input list must produce an empty output list, not a null');
    }
}
```

Why `Assert.areEqual(1, queriesUsed, …)` rather than a "well under the limit" assertion: an action
whose SOQL count grows with input count still passes a headroom check at 200 and fails at the
moment a second automation shares the transaction. Asserting the constant is the only version of
this test that catches a query moved into the loop.

---

## 5. The `callout=true` variant

An action that calls an external system must declare it. The guide's `BookingAction` sample is the
reference shape (apexdev L26912–26950):

```apex
/**
 * CaseEscalationNotifyAction — pages the on-call rota when a case is escalated.
 *
 * `callout=true` "identifies whether the method calls to an external system"; the
 * default is false (apexdev L5407–5408). It is not decoration — see the note below.
 *
 * The callout itself goes through templates/apex/HttpClient.cls (Named Credential,
 * timeout, transient retry). Outbound callout design belongs to
 * apex/callouts-and-http-integrations, not to this skill.
 */
public with sharing class CaseEscalationNotifyAction {

    public class Request {
        @InvocableVariable(label='Case Id' required=true)
        public Id caseId;

        @InvocableVariable(label='Rota Name' description='Named on-call rota to page.' required=true)
        public String rotaName;
    }

    public class Result {
        @InvocableVariable(label='Paged') public Boolean paged;
        @InvocableVariable(label='Error Message') public String errorMessage;
    }

    @InvocableMethod(
        label='Notify On-Call Rota'
        description='Sends one paging request per escalated case to the on-call system.'
        category='Case Management'
        callout=true
    )
    public static List<Result> notify(List<Request> requests) {
        List<Result> results = new List<Result>();
        // One callout per input. A synchronous transaction allows 100 callouts
        // (apexdev L19563) with a 120-second cumulative timeout (apexdev L19565), so
        // this action is only safe for small batches — see the ceiling note below.
        for (Request req : requests) {
            Result r = new Result();
            try {
                HttpClient.Response response = new HttpClient()
                    .namedCredential('OnCall_API')
                    .path('/v1/pages')
                    .method('POST')
                    .header('Content-Type', 'application/json')
                    .body(JSON.serialize(new Map<String, Object>{
                        'caseId' => req.caseId,
                        'rota' => req.rotaName
                    }))
                    .timeoutMs(10000)
                    .retryOnTransient(true)
                    .send();
                r.paged = response.isSuccess();
                r.errorMessage = response.isSuccess() ? null : 'HTTP ' + response.statusCode;
            } catch (Exception e) {
                // Catch per input: one unreachable endpoint must not fault the other 199.
                r.paged = false;
                r.errorMessage = e.getTypeName() + ': ' + e.getMessage();
                ApplicationLogger.error('CaseEscalationNotifyAction', e);
            }
            results.add(r);
        }
        ApplicationLogger.flush();
        return results;
    }
}
```

**What `callout=true` actually buys you.** In a *screen* flow, the modifier is one of three
conditions the platform checks. When all three hold — "The method's callout modifier is true", "The
action's Transaction Control setting in a screen flow is configured to let the flow decide", and
"The current transaction has uncommitted work" — "the flow commits the current transaction, starts
a new transaction, and makes the call to an external system safely" (apexdev L26866–26876). If any
of "The callout modifier is false", "The action is executed by a non-screen flow", or "The current
transaction doesn't have uncommitted work" holds, "the flow executes the action in the current
transaction" (apexdev L26877–26880).

Read the second list carefully: **in a record-triggered or autolaunched flow, `callout=true` does
not move the action into a new transaction.** If that flow has already done DML, the callout hits
`System.CalloutException: You have uncommitted work pending. Please commit or rollback before
calling out.` — the guide asserts that exact message text (apexdev L8768–8769), and describes the
same mechanism for asynchronous Apex: "asynchronous Apex operations result in pending uncommitted
work that prevents callouts from being performed later in the same transaction"
(apexdev L35183–35188, in the mock-callout testing section). The fixes there are the fixes here: make the callout
first, or move it to a separate asynchronous transaction. Transaction boundaries in flows are owned
by `flow/flow-transactional-boundaries`.

**The 100-callout ceiling.** With one callout per input, a 200-interview batch needs 200 callouts
against a limit of 100 per transaction (apexdev L19563), and 200 × 10 s of timeout against a
cumulative ceiling of 120 s (apexdev L19565). A per-input callout action is therefore a screen-flow
and small-batch design. For record-triggered volume, have the invocable enqueue work — see
`apex/apex-queueable-patterns` — and let the flow's fault path handle the enqueue failure, not the callout
failure.

---

## 6. Wiring it into a flow — `actionCalls`

Excerpt from a record-triggered flow; the `<Flow>` root is included so the fragment parses.
`actionType` `apex` "Invokes an Apex method that has the @invocableMethod annotation"
(api_meta L68604) and `actionName` is the **class** name.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: the actionCalls node and its fault target, inside a minimal Flow root. -->
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <actionCalls>
        <name>Escalate_Cases</name>
        <label>Escalate Cases</label>
        <locationX>380</locationX>
        <locationY>242</locationY>
        <actionName>CaseEscalationAction</actionName>
        <actionType>apex</actionType>
        <connector>
            <targetReference>Check_Escalation_Result</targetReference>
        </connector>
        <faultConnector>
            <targetReference>Log_Escalation_Fault</targetReference>
        </faultConnector>
        <flowTransactionModel>CurrentTransaction</flowTransactionModel>
        <inputParameters>
            <name>caseId</name>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </inputParameters>
        <inputParameters>
            <name>reason</name>
            <value>
                <elementReference>varEscalationReason</elementReference>
            </value>
        </inputParameters>
        <storeOutputAutomatically>true</storeOutputAutomatically>
    </actionCalls>
    <recordCreates>
        <name>Log_Escalation_Fault</name>
        <label>Log Escalation Fault</label>
        <locationX>640</locationX>
        <locationY>242</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>$Flow.FaultMessage</elementReference>
            </value>
        </inputAssignments>
        <object>Application_Log__c</object>
        <storeOutputAutomatically>false</storeOutputAutomatically>
    </recordCreates>
</Flow>
```

### How to read the fragment

| Element | Why it is there |
|---|---|
| `actionName` | "Required. Name for the action. Must be unique across actions with the same actionType." (api_meta L68462–68463) — for `apex`, this is the Apex class name, not the method name. |
| `actionType` | `apex` (api_meta L68604). Enumerated in `InvocableActionType` (api_meta L68551+). |
| `faultConnector` | "Specifies which node to execute if the action call results in an error." (api_meta L68479) Without it, an uncaught exception in the invocable ends the interview with the platform's own error. Fault-path design is `flow/fault-handling`. |
| `flowTransactionModel` | "Required." Values: `Automatic` — "Creates a transaction if the invocable action supports it and there's pending DML"; `CurrentTransaction` — "Keeps the invocable action running in the same transaction"; `NewTransaction` — "Creates a transaction before the invocable action is executed". API 51.0 and later. (api_meta L68479–68487) |
| `storeOutputAutomatically` | `true` lets the flow reference outputs as `{!Escalate_Cases}` with no manually-created variables; the default is `false` (api_meta L68522–68530). Available in API 48.0 and later. |
| `inputParameters` | The `<name>` must be the **Apex member variable name**: "The invocable variable name in Apex must match the name in the flow. The name is case-sensitive." (apexdev L5731) |

**Generic `sObject` inputs need `dataTypeMappings`.** If the wrapper declares
`public List<SObject> inputCollection`, the flow must bind the concrete type with
`FlowDataTypeMapping`, where "The `T__` prefix is required for input variables. The `U__` prefix is
required for output variables" and `typeValue` is the "API name of the specific sObject data type"
(api_meta L70192–70203). The guide's flow sample shows both (api_meta L73221–73228):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Excerpt: the two dataTypeMappings that bind a generic-sObject action to Account. -->
<actionCalls xmlns="http://soap.sforce.com/2006/04/metadata">
    <dataTypeMappings>
        <typeName>T__inputCollection</typeName>
        <typeValue>Account</typeValue>
    </dataTypeMappings>
    <dataTypeMappings>
        <typeName>U__outputMember</typeName>
        <typeValue>Account</typeValue>
    </dataTypeMappings>
</actionCalls>
```

---

## 7. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CaseEscalationAction</members>
        <members>CaseEscalationService</members>
        <members>CaseEscalationNotifyAction</members>
        <members>CaseEscalationActionTest</members>
        <members>ApplicationLogger</members>
        <members>HttpClient</members>
        <members>SecurityUtils</members>
        <members>TestDataFactory</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>Case.Escalation_Reason__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Case_Escalation</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Case_Escalation_Handler</members>
        <name>PermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

The `PermissionSet` is not optional. "If a flow invokes Apex, the running user must have the
corresponding Apex class security set in their user profile or permission set" (apexdev L5172), and
the REST guide repeats it for the API path: "Describe and invoke for an Apex action respect the
profile access for the Apex class. If you don't have access, an error is issued"
(api_rest L13780). Its `classAccesses` entry must name `CaseEscalationAction`.

---

## 8. Deploy order

Deploy bottom-up; each layer must exist before the layer that references it compiles or activates.

| # | What | Why this order |
|---|---|---|
| 1 | `Case.Escalation_Reason__c` | `CaseEscalationService` does not compile without it |
| 2 | `Application_Log__c` + `Logger_Setting__mdt` and a `Default` record | Prerequisites of `templates/apex/ApplicationLogger.cls` — see `templates/apex/README.md` |
| 3 | `ApplicationLogger`, `SecurityUtils`, `HttpClient`, `TestDataFactory` | Shared templates the classes below reference |
| 4 | `CaseEscalationService` | Referenced by the boundary class |
| 5 | `CaseEscalationAction`, `CaseEscalationNotifyAction`, `CaseEscalationActionTest` | The invocable surface |
| 6 | `Case_Escalation_Handler` permission set (`classAccesses`) | Grant before anyone runs the flow |
| 7 | `Case_Escalation` flow | Activating a flow whose `actionName` does not resolve fails the deploy |

Reverse the order to retire it — and note that removing the annotation is not a safe rollback:
"If you add an Apex action to a flow, and then remove the Invocable Method annotation from the Apex
class, a runtime error in the flow occurs" (api_rest L13781–13782). Deactivate the flow first.

```bash
# 1. Static check before deploying — flags the invocable-specific defects the compiler cannot see
python3 skills/apex/invocable-methods/scripts/check_invocable_methods.py \
    --manifest-dir force-app

# 2. Deploy the manifest
sf project deploy start -x manifest/package.xml -o myOrg -w 30

# 3. Run only this suite, with coverage
sf apex run test -o myOrg -n CaseEscalationActionTest -r human -w 20 -c -y

# 4. Retrieve back to confirm what landed, including the apiVersion pin
sf project retrieve start -x manifest/package.xml -o myOrg
```

---

## 9. Verification

**(a) The action is registered.** Custom invocable actions are enumerable over REST at
`/services/data/vXX.X/actions/custom` (api_rest L13807–13808), with the Apex actions under the
`apex` key: `"apex" : "/services/data/v67.0/actions/custom/apex"` (api_rest L13837).

```bash
sf org list metadata -m ApexClass -o myOrg | grep CaseEscalationAction

# The action's own describe — inputs, outputs, labels, exactly as Flow Builder sees them
sf api request rest \
  '/services/data/v67.0/actions/custom/apex/CaseEscalationAction' \
  -o myOrg
```

**(b) Invoke it without a flow.** The custom-action REST resource takes an `inputs` array; passing
two entries is the cheapest proof the output list is index-aligned. Note the platform constraint
on this path: "When invoking an Apex action using the POST method and supplying the inputs in the
request, only the following primitive types are supported as inputs" — `Blob, Boolean, Date,
Datetime, Decimal, Double, ID, Integer, Long, String, Time` (api_rest L13767–13779).

```bash
sf api request rest \
  '/services/data/v67.0/actions/custom/apex/CaseEscalationAction' \
  --method POST \
  --body '{"inputs":[
      {"caseId":"5003000000D8cuIAAR","reason":"SLA breach","targetPriority":"High"},
      {"caseId":"000000000000000AAA","reason":"Should fail"}
  ]}' \
  -o myOrg
```

Expect two entries back, the first with `"success": true` and the second with a populated
`errorMessage` — not one entry, and not an error response.

**(c) Calling it from Apex.** `Invocable.Action` "Contains methods to create, update, and retrieve
information about invocable actions" (apexrefguide L160640–160641). `createCustomAction(type, name)`
returns an `Invocable.Action` (apexrefguide L160856–160869), `invoke()` returns
`List<Invocable.Action.Result>` (apexrefguide L160993–160997), and each `Result` answers
`isSuccess()`, `getErrors()` (returning `List<Invocable.Action.Error>`) and `getOutputParameters()`
(apexrefguide L162561–162573).

```apex
// Anonymous Apex — proves the action is reachable and that results carry errors, not exceptions.
Invocable.Action action = Invocable.Action.createCustomAction('apex', 'CaseEscalationAction');
action.setInvocationParameter('caseId', '5003000000D8cuIAAR');
action.setInvocationParameter('reason', 'Escalated from anonymous Apex');
List<Invocable.Action.Result> results = action.invoke();
for (Invocable.Action.Result r : results) {
    System.debug('success=' + r.isSuccess());
    System.debug('outputs=' + r.getOutputParameters());
    for (Invocable.Action.Error e : r.getErrors()) {
        System.debug('error=' + e.getMessage());
    }
}
```

`getDescribe()` returns full metadata about an action's inputs and outputs, and the reference guide
warns it "can have performance implications. Use `getDescribe()` judiciously, especially in
performance-sensitive contexts such as loops or frequently executed code paths"
(apexrefguide L160648–160652) — describe once outside the loop, or not at all in a transaction that
also does work.

**(d) The bulk claim holds in the org, not just in the test.** Escalate 200 cases through the flow,
then read the debug log's `LIMIT_USAGE_FOR_NS` block. `Number of SOQL queries` and `Number of DML
statements` attributable to the action must be `1` each; anything proportional to 200 means a query
or a DML moved into a loop.

```soql
SELECT Id, Priority, IsEscalated, Escalation_Reason__c, LastModifiedDate
FROM Case
WHERE IsEscalated = true AND LastModifiedDate = TODAY
ORDER BY LastModifiedDate DESC
LIMIT 200
```

**(e) Setup check.** Setup → Apex Classes shows `CaseEscalationAction` with its API version. Setup →
Permission Sets → *Case Escalation Handler* → Apex Class Access must list it; remove it and every
flow interview that reaches the action fails for that user (apexdev L5172).
