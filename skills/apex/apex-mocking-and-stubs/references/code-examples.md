# Code Examples — Apex Mocking and Stubs

A complete, deployable seam-and-stub set: an interface-backed selector, a service that
takes its collaborators by constructor injection, a **reusable recording `StubProvider`**,
the test that asserts on recorded arguments, and a negative example showing the elements
the Stub API refuses to mock.

Canonical building blocks are referenced by path rather than duplicated:

| Building block | Path | Used here for |
|---|---|---|
| Selector base class | `templates/apex/BaseSelector.cls` | `WITH USER_MODE` default, `SelectorException` |
| Service base class | `templates/apex/BaseService.cls` | savepoint + `logAndRethrow` hooks |
| Reusable `HttpCalloutMock` | `templates/apex/tests/MockHttpResponseGenerator.cls` | transport mocks (do **not** rebuild it here) |
| Test data | `templates/apex/tests/TestDataFactory.cls` | `createAccounts` / `createOpportunities` |
| Bulk assertions | `templates/apex/tests/BulkTestPattern.cls` | the 200-record path |
| Test users | `templates/apex/tests/TestUserFactory.cls` | `System.runAs` blocks |

---

## How to read it

- **The interface is the artifact, not the stub.** `IOpportunitySelector` exists only so the
  service has a replaceable boundary; `Test.createStub` cannot manufacture one.
- **Two constructors.** The no-arg constructor wires the real collaborators for production;
  the injecting constructor is what tests call. Neither branches on `Test.isRunningTest()`.
- **`RenewalService` is bulk-safe.** One selector call and one DML for the whole `Set<Id>` —
  no SOQL or DML inside the loop, so the same class survives a 200-record trigger batch.
- **`RecordingStubProvider` is generic.** It routes by `stubbedMethodName`, records every
  invocation (name, parameter names, actual argument values), and *throws* rather than
  returning `null` for a method nobody stubbed. `handleMethodCall`'s six parameters are fixed
  by the interface signature (Apex Reference Guide L238486–238488, parameters at L238492–238509) — renaming them is fine,
  reordering or dropping one is a compile error.
- **Void methods must return `null`.** `handleMethodCall` is declared `Object`, so a stubbed
  `void` method still runs through it; the provider has to fall through to `null` instead of
  hitting the "unstubbed" throw.
- **Assertions are on the recording, not on side effects.** `provider.lastCall('notify')`
  proves the service passed the right rows to the collaborator — the thing a transport mock
  cannot tell you.

---

## 1. The seam — interface + selector

```apex
public interface IOpportunitySelector {
    List<Opportunity> selectOpenByAccountIds(Set<Id> accountIds);
}
```

```apex
/**
 * Real implementation. Extends templates/apex/BaseSelector.cls so the query
 * defaults to AccessLevel.USER_MODE (CRUD + FLS + sharing enforced).
 */
public inherited sharing class OpportunitySelector
        extends BaseSelector
        implements IOpportunitySelector {

    public List<Opportunity> selectOpenByAccountIds(Set<Id> accountIds) {
        assertNotNull(accountIds, 'accountIds');
        return (List<Opportunity>) Database.queryWithBinds(
            'SELECT Id, AccountId, Name, StageName, CloseDate, Amount ' +
            'FROM Opportunity ' +
            'WHERE AccountId IN :accountIds AND IsClosed = false ' +
            'ORDER BY CloseDate ASC',
            new Map<String, Object>{ 'accountIds' => accountIds },
            userMode()
        );
    }
}
```

```apex
public interface IRenewalNotifier {
    /** Returns the number of notifications actually dispatched. */
    Integer notify(List<Opportunity> opportunities);
}
```

---

## 2. The service — constructor injection, bulk-safe

```apex
/**
 * RenewalService — stages open Opportunities for renewal and notifies downstream.
 *
 * Collaborators arrive through the constructor. There is deliberately no
 * Test.isRunningTest() branch: the seam is the constructor, not a runtime flag.
 */
public with sharing class RenewalService extends BaseService {

    public class RenewalException extends Exception {}

    private final IOpportunitySelector selector;
    private final IRenewalNotifier notifier;

    /** Production entry point — wires the real collaborators. */
    public RenewalService() {
        this(new OpportunitySelector(), new EmailRenewalNotifier());
    }

    /** Injection point used by tests and by callers that need a different notifier. */
    public RenewalService(IOpportunitySelector selector, IRenewalNotifier notifier) {
        if (selector == null || notifier == null) {
            throw new RenewalException('RenewalService requires both collaborators');
        }
        this.selector = selector;
        this.notifier = notifier;
    }

    /**
     * Bulk-safe: one selector call, one DML, one notifier call for the whole set.
     * Returns the number of Opportunities staged per Account.
     */
    public Map<Id, Integer> stageRenewals(Set<Id> accountIds, String targetStage) {
        Map<Id, Integer> stagedByAccount = new Map<Id, Integer>();
        if (accountIds == null || accountIds.isEmpty()) {
            return stagedByAccount;
        }

        List<Opportunity> open = selector.selectOpenByAccountIds(accountIds);
        if (open.isEmpty()) {
            return stagedByAccount;
        }

        List<Opportunity> toStage = new List<Opportunity>();
        for (Opportunity opp : open) {
            if (opp.StageName == targetStage) {
                continue;
            }
            opp.StageName = targetStage;
            toStage.add(opp);
            Integer soFar = stagedByAccount.containsKey(opp.AccountId)
                ? stagedByAccount.get(opp.AccountId)
                : 0;
            stagedByAccount.put(opp.AccountId, soFar + 1);
        }

        if (toStage.isEmpty()) {
            return stagedByAccount;
        }

        update as user toStage;
        notifier.notify(toStage);
        return stagedByAccount;
    }
}
```

```apex
/** Real notifier — irrelevant to the tests below, which never construct it. */
public with sharing class EmailRenewalNotifier implements IRenewalNotifier {
    public Integer notify(List<Opportunity> opportunities) {
        // Real dispatch omitted; see apex/apex-http-callout-mocking for the
        // transport-level test double this class would need.
        return opportunities == null ? 0 : opportunities.size();
    }
}
```

---

## 3. The reusable recording `StubProvider`

```apex
/**
 * RecordingStubProvider — a general-purpose StubProvider that
 *   (a) returns canned values keyed by method name,
 *   (b) records every invocation with its parameter names and actual arguments,
 *   (c) throws on any method the test did not stub, so a missing stub fails
 *       at the call site instead of surfacing as an NPE three frames later.
 *
 * Annotated @IsTest so it is excluded from the org's 6 MB Apex code size limit
 * (Apex Developer Guide L35416-35418).
 *
 * Usage:
 *     RecordingStubProvider p = new RecordingStubProvider()
 *         .returns('selectOpenByAccountIds', existingOpps);
 *     IOpportunitySelector stub =
 *         (IOpportunitySelector) Test.createStub(IOpportunitySelector.class, p);
 */
@IsTest
public class RecordingStubProvider implements System.StubProvider {

    public class UnstubbedMethodException extends Exception {}

    /** One recorded call to the stubbed object. */
    public class Invocation {
        public final String methodName;
        public final List<String> paramNames;
        public final List<Object> args;

        public Invocation(String methodName, List<String> paramNames, List<Object> args) {
            this.methodName = methodName;
            this.paramNames = paramNames == null ? new List<String>() : paramNames;
            this.args = args == null ? new List<Object>() : args;
        }

        public Object arg(Integer index) {
            return (index >= 0 && index < args.size()) ? args[index] : null;
        }

        public Object argNamed(String name) {
            Integer index = paramNames.indexOf(name);
            return index == -1 ? null : arg(index);
        }
    }

    private final Map<String, Object> returnsByMethod = new Map<String, Object>();
    private final Map<String, Exception> throwsByMethod = new Map<String, Exception>();
    private final Set<String> voidMethods = new Set<String>();

    /** Every call the stub saw, in order. */
    public final List<Invocation> invocations = new List<Invocation>();

    public RecordingStubProvider returns(String methodName, Object value) {
        returnsByMethod.put(methodName, value);
        return this;
    }

    public RecordingStubProvider throwsOn(String methodName, Exception toThrow) {
        throwsByMethod.put(methodName, toThrow);
        return this;
    }

    /** Register a void method so the provider returns null instead of throwing. */
    public RecordingStubProvider allowsVoid(String methodName) {
        voidMethods.add(methodName);
        return this;
    }

    public Object handleMethodCall(
        Object stubbedObject,
        String stubbedMethodName,
        Type returnType,
        List<Type> listOfParamTypes,
        List<String> listOfParamNames,
        List<Object> listOfArgs
    ) {
        invocations.add(new Invocation(stubbedMethodName, listOfParamNames, listOfArgs));

        if (throwsByMethod.containsKey(stubbedMethodName)) {
            throw throwsByMethod.get(stubbedMethodName);
        }
        if (returnsByMethod.containsKey(stubbedMethodName)) {
            return returnsByMethod.get(stubbedMethodName);
        }
        // A stubbed void method still routes through handleMethodCall; it must
        // get null, not the UnstubbedMethodException below.
        if (voidMethods.contains(stubbedMethodName) || isVoid(returnType)) {
            return null;
        }
        throw new UnstubbedMethodException(
            'No stub registered for ' + stubbedMethodName +
            ' (return type ' + (returnType == null ? 'void' : returnType.getName()) + ')'
        );
    }

    private Boolean isVoid(Type returnType) {
        // UNVERIFIED (2026-09-05): the Apex Reference Guide documents returnType as
        // System.Type (L238498-238500) but does not state what it holds for a void
        // method. Both null and a 'void'-named Type are handled defensively; call
        // allowsVoid() to be explicit rather than relying on this.
        return returnType == null || 'void'.equalsIgnoreCase(returnType.getName());
    }

    public Integer callCount(String methodName) {
        Integer count = 0;
        for (Invocation call : invocations) {
            if (call.methodName == methodName) {
                count++;
            }
        }
        return count;
    }

    public Invocation lastCall(String methodName) {
        for (Integer i = invocations.size() - 1; i >= 0; i--) {
            if (invocations[i].methodName == methodName) {
                return invocations[i];
            }
        }
        return null;
    }
}
```

---

## 4. The test — `Test.createStub` plus assertions on recorded arguments

```apex
@IsTest
private class RenewalServiceTest {

    private static final String TARGET_STAGE = 'Renewal Pending';

    @TestSetup
    static void seed() {
        // templates/apex/tests/TestDataFactory.cls
        List<Account> accounts = TestDataFactory.createAccounts(2, null);
        insert accounts;
        List<Opportunity> opps = new List<Opportunity>();
        for (Account a : accounts) {
            opps.addAll(TestDataFactory.createOpportunities(3, a.Id, null));
        }
        insert opps;
    }

    @IsTest
    static void stagesEveryOpenOpportunityAndTellsTheNotifier() {
        List<Opportunity> seeded = [
            SELECT Id, AccountId, StageName FROM Opportunity WITH USER_MODE
        ];
        Set<Id> accountIds = new Map<Id, Account>(
            [SELECT Id FROM Account WITH USER_MODE]
        ).keySet();

        RecordingStubProvider selectorProvider = new RecordingStubProvider()
            .returns('selectOpenByAccountIds', seeded);
        RecordingStubProvider notifierProvider = new RecordingStubProvider()
            .returns('notify', seeded.size());

        IOpportunitySelector selectorStub = (IOpportunitySelector) Test.createStub(
            IOpportunitySelector.class, selectorProvider
        );
        IRenewalNotifier notifierStub = (IRenewalNotifier) Test.createStub(
            IRenewalNotifier.class, notifierProvider
        );

        Test.startTest();
        Map<Id, Integer> staged =
            new RenewalService(selectorStub, notifierStub).stageRenewals(accountIds, TARGET_STAGE);
        Test.stopTest();

        Assert.areEqual(2, staged.size(), 'Both Accounts should have staged rows');

        // Assert on the ARGUMENTS the service handed the collaborator — the thing
        // a transport mock can never show you.
        Assert.areEqual(1, selectorProvider.callCount('selectOpenByAccountIds'),
            'Selector must be called exactly once for the whole set (bulk-safe)');
        RecordingStubProvider.Invocation selectCall =
            selectorProvider.lastCall('selectOpenByAccountIds');
        Assert.areEqual(accountIds, (Set<Id>) selectCall.arg(0),
            'Service must pass the full Account Id set, not one Id at a time');
        Assert.areEqual('accountIds', selectCall.paramNames[0],
            'listOfParamNames carries the declared parameter name');

        RecordingStubProvider.Invocation notifyCall = notifierProvider.lastCall('notify');
        Assert.isNotNull(notifyCall, 'Notifier must be invoked once rows were staged');
        Assert.areEqual(seeded.size(), ((List<Opportunity>) notifyCall.arg(0)).size(),
            'Notifier receives every staged row in one call');
    }

    @IsTest
    static void skipsNotifierWhenNothingChanged() {
        List<Opportunity> alreadyStaged = [
            SELECT Id, AccountId, StageName FROM Opportunity WITH USER_MODE
        ];
        for (Opportunity opp : alreadyStaged) {
            opp.StageName = TARGET_STAGE;
        }

        RecordingStubProvider selectorProvider = new RecordingStubProvider()
            .returns('selectOpenByAccountIds', alreadyStaged);
        RecordingStubProvider notifierProvider = new RecordingStubProvider()
            .returns('notify', 0);

        Test.startTest();
        new RenewalService(
            (IOpportunitySelector) Test.createStub(IOpportunitySelector.class, selectorProvider),
            (IRenewalNotifier) Test.createStub(IRenewalNotifier.class, notifierProvider)
        ).stageRenewals(new Set<Id>{ alreadyStaged[0].AccountId }, TARGET_STAGE);
        Test.stopTest();

        Assert.areEqual(0, notifierProvider.callCount('notify'),
            'No rows changed, so the notifier must not be called at all');
    }

    @IsTest
    static void surfacesCollaboratorFailure() {
        RecordingStubProvider selectorProvider = new RecordingStubProvider()
            .throwsOn('selectOpenByAccountIds', new QueryException('simulated selector failure'));

        Test.startTest();
        try {
            new RenewalService(
                (IOpportunitySelector) Test.createStub(IOpportunitySelector.class, selectorProvider),
                (IRenewalNotifier) Test.createStub(IRenewalNotifier.class, new RecordingStubProvider())
            ).stageRenewals(new Set<Id>{ [SELECT Id FROM Account WITH USER_MODE LIMIT 1].Id }, TARGET_STAGE);
            Assert.fail('Selector failure should propagate');
        } catch (QueryException expected) {
            Assert.isTrue(expected.getMessage().contains('simulated'), expected.getMessage());
        }
        Test.stopTest();
    }

    @IsTest
    static void bulkPathStaysWithinOneQueryAndOneDml() {
        // templates/apex/tests/BulkTestPattern.cls documents the 200-record shape.
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;
        List<Opportunity> bulk = TestDataFactory.createOpportunities(200, accounts[0].Id, null);
        insert bulk;

        RecordingStubProvider selectorProvider = new RecordingStubProvider()
            .returns('selectOpenByAccountIds', bulk);

        Test.startTest();
        Integer dmlBefore = Limits.getDMLStatements();
        new RenewalService(
            (IOpportunitySelector) Test.createStub(IOpportunitySelector.class, selectorProvider),
            (IRenewalNotifier) Test.createStub(
                IRenewalNotifier.class, new RecordingStubProvider().returns('notify', 200)
            )
        ).stageRenewals(new Set<Id>{ accounts[0].Id }, TARGET_STAGE);
        Integer dmlAfter = Limits.getDMLStatements();
        Test.stopTest();

        Assert.areEqual(1, dmlAfter - dmlBefore, '200 rows must cost exactly one DML statement');
        Assert.areEqual(1, selectorProvider.callCount('selectOpenByAccountIds'),
            'Selector must not be called per record');
    }
}
```

---

## 5. Negative example — what the Stub API refuses

Every line below fails; the list is the documented one (Apex Developer Guide L42209–42219).

```apex
@IsTest
private class StubApiLimitationsTest {

    // Static methods (including @future methods) cannot be mocked (L42210).
    public class TaxUtil {
        public static Decimal rate() { return 0.08; }
    }

    // Classes with only private constructors cannot be mocked (L42217).
    public class LockedDown {
        private LockedDown() {}
        public String hello() { return 'hi'; }
    }

    // Inner classes cannot be mocked (L42214) — every class in THIS file is an
    // inner class, which is why a real seam must be a top-level type.
    public class Nested {
        public String hello() { return 'hi'; }
    }

    @IsTest
    static void documentsWhatCannotBeStubbed() {
        RecordingStubProvider p = new RecordingStubProvider().returns('rate', 0.10);

        // 1. Stubbing does not intercept a static call. Even if createStub
        //    succeeded, TaxUtil.rate() is resolved statically and returns 0.08.
        Assert.areEqual(0.08, TaxUtil.rate(), 'Static dispatch ignores the stub');

        // 2. Inner class / private-constructor class / Batchable implementor /
        //    System type / trigger / private method / property — all rejected.
        //    The failure is a runtime error from createStub, not a compile error,
        //    so it only shows up when the test runs.
        try {
            Object rejected = Test.createStub(Nested.class, p);
            Assert.fail('Inner classes cannot be stubbed: ' + rejected);
        } catch (Exception expected) {
            Assert.isNotNull(expected.getMessage());
        }
    }
}
```

**The fix in every case is the same shape as section 1:** promote the dependency to a
top-level interface (or a top-level class with a public constructor), inject it, and stub
the interface. `@TestVisible` (Apex Developer Guide L6290–L6296) widens a *private member*
for a test; it does not make a static method stubbable.

---

## 6. `-meta.xml` for every class

Each `.cls` above needs a sibling `<ClassName>.cls-meta.xml`. `apiVersion` matches the
repo templates (`templates/apex/BaseService.cls-meta.xml`); `ApexClass.apiVersion` and
`status` are the Metadata API fields (Metadata API Developer Guide L22212+, L22240+).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 7. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>IOpportunitySelector</members>
        <members>IRenewalNotifier</members>
        <members>OpportunitySelector</members>
        <members>EmailRenewalNotifier</members>
        <members>RenewalService</members>
        <members>RecordingStubProvider</members>
        <members>RenewalServiceTest</members>
        <members>StubApiLimitationsTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 8. Deploy and verify

```bash
# Retrieve the current state before you change anything.
sf project retrieve start --manifest manifest/package.xml --target-org devhub-sandbox

# Deploy and run only this skill's tests.
sf project deploy start \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests RenewalServiceTest --tests StubApiLimitationsTest \
  --target-org devhub-sandbox

# Run the tests on their own, synchronously, with coverage.
sf apex run test \
  --tests RenewalServiceTest --tests StubApiLimitationsTest \
  --result-format human --code-coverage --synchronous \
  --target-org devhub-sandbox
```

**Verification step — prove the seam is actually injectable, not just present.** After the
deploy, confirm no production class reaches for a test-only escape hatch:

```bash
sf apex run test --tests RenewalServiceTest --result-format json --synchronous \
  --target-org devhub-sandbox | python3 -c "import json,sys; r=json.load(sys.stdin)['result']; print(r['summary']['outcome'], r['summary']['testsRan'])"

# And run this skill's checker over the source tree:
python3 skills/apex/apex-mocking-and-stubs/scripts/check_apex_mocking_and_stubs.py \
  --manifest-dir force-app/main/default/classes
```

A SOQL check that the classes landed and are compiled:

```soql
SELECT Name, ApiVersion, Status, IsValid
FROM ApexClass
WHERE Name IN ('RenewalService', 'RecordingStubProvider', 'OpportunitySelector')
ORDER BY Name
```

`IsValid = false` on any row means the class needs recompiling before the stub tests mean
anything.
