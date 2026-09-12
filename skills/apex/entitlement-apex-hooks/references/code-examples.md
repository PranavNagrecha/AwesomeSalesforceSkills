# Code Examples — Entitlement Apex Hooks

A complete, deployable bundle for the one thing Apex is actually allowed to do to a
milestone: stamp `CompletionDate` on an open `CaseMilestone`.

`references/examples.md` names `CaseMilestoneTrigger` and `CaseMilestoneService`; this
file is the deployable form of those two, plus the handler that joins them, the test, the
metadata files, the manifest, and the verification run. Class and trigger names are stable
— the case-onboarding build's `M4-S05` step cites them.

Every class here is pinned to `apiVersion` 67.0. That version choice is load-bearing and
is explained in [What `apiVersion` 67.0 changes](#what-apiversion-670-changes) below.

---

## Bundle contents

| File | Kind | Role |
|---|---|---|
| `CaseMilestoneService.cls` | class | The logic. One SOQL, one DML, partial-success handling. |
| `CaseMilestoneTriggerHandler.cls` | class | Subclass of `templates/apex/TriggerHandler.cls`; owns the `afterUpdate` context. |
| `CaseMilestoneTrigger.trigger` | trigger | `after update` on `Case`. One line, no logic. |
| `CaseMilestoneServiceTest.cls` | class | Bulk + idempotency + skip-completed assertions. |
| `package.xml` | manifest | Deploy/retrieve manifest for the bundle. |

Referenced by relative path, not copied into this bundle:

| Template | Why this bundle needs it |
|---|---|
| `templates/apex/TriggerHandler.cls` | Base class. `CaseMilestoneTriggerHandler` extends it and overrides `afterUpdate()`. |
| `templates/apex/TriggerControl.cls` | `TriggerHandler.run()` calls `TriggerControl.isActive(...)` on its first line. Deploy it, and its `cmdt/Trigger_Setting__mdt/` dependency, or the handler will not run. |
| `templates/apex/ApplicationLogger.cls` | `CaseMilestoneService` writes partial-success failures here. Carries its own dependencies — `Application_Log__c` and `Logger_Setting__mdt`. See the [optional-dependency note](#if-you-do-not-want-the-applicationlogger-dependency). |
| `templates/apex/tests/TestDataFactory.cls` | `CaseMilestoneServiceTest` builds its 200 cases with `TestDataFactory.createCases(...)` rather than a hand-rolled loop. |

See **Deploy prerequisites** below for what happens if one of these does not ship alongside the class that calls it.

---

## `CaseMilestoneService.cls`

The whole point of the class is the three-clause `WHERE`: the case Ids, the milestone type
name, and `CompletionDate = NULL`. That last clause is doing two jobs — it selects only
open milestones, and it is the idempotency guard that makes a second trigger pass a no-op.

```apex
/**
 * CaseMilestoneService — completes CaseMilestone rows in response to a Case change.
 *
 * The only supported write. CaseMilestone's documented supported calls are
 * describeLayout(), describeSObjects(), query(), retrieve(), update() — the platform
 * creates and deletes the rows, Apex can only update them. Of the object's fields, only
 * CompletionDate and StartDate carry the `Update` property; IsCompleted, IsViolated and
 * TargetDate do not. So "complete this milestone" means exactly one thing: write
 * CompletionDate.
 *
 * Bulk shape: one SOQL, one DML, regardless of how many Cases are in Trigger.new.
 */
public with sharing class CaseMilestoneService {

    private static final String LOG_SOURCE = 'CaseMilestoneService.completeMilestones';

    /** Governor-safe ceiling on a single trigger pass. 10,000 is the DML row limit. */
    private static final Integer MAX_MILESTONES = 10000;

    /**
     * Case Status values that count as "the milestone is satisfied". Kept as a constant
     * rather than a literal so a Setup rename is a one-line change. @TestVisible so the
     * test can assert against the same set the trigger uses instead of a copy of it.
     */
    @TestVisible
    private static final Set<String> COMPLETING_STATUSES = new Set<String>{
        'Working', 'Escalated', 'Closed'
    };

    /** What one pass did. Returned so the caller and the test can assert on it. */
    public class CompletionResult {
        public Integer attempted = 0;
        public Integer completed = 0;
        public List<String> failures = new List<String>();
    }

    /**
     * Completes every open milestone of the named type on Cases whose Status just moved
     * into COMPLETING_STATUSES.
     *
     * @param newCases          Trigger.new
     * @param oldCases          Trigger.oldMap
     * @param milestoneTypeName exact MilestoneType.Name from Setup
     */
    public static CompletionResult completeMilestones(
            List<Case> newCases,
            Map<Id, Case> oldCases,
            String milestoneTypeName) {

        CompletionResult result = new CompletionResult();
        if (newCases == null || oldCases == null || String.isBlank(milestoneTypeName)) {
            return result;
        }

        // Pass 1 — collect Ids only. No SOQL and no DML inside this loop.
        Set<Id> caseIds = new Set<Id>();
        for (Case changed : newCases) {
            Case previous = oldCases.get(changed.Id);
            if (previous == null) {
                continue;
            }
            if (changed.Status == previous.Status) {
                continue;
            }
            if (COMPLETING_STATUSES.contains(changed.Status)) {
                caseIds.add(changed.Id);
            }
        }
        if (caseIds.isEmpty()) {
            return result;
        }

        // The one query. WITH USER_MODE is redundant at apiVersion 67.0 — user mode is
        // the default — but it states the intent at the call site, where a future
        // version downgrade would otherwise change behaviour silently.
        List<CaseMilestone> openMilestones = [
            SELECT Id, CaseId, CompletionDate, TargetDate
            FROM CaseMilestone
            WHERE CaseId IN :caseIds
              AND MilestoneType.Name = :milestoneTypeName
              AND CompletionDate = NULL
            WITH USER_MODE
            LIMIT 10000
        ];
        if (openMilestones.isEmpty()) {
            return result;
        }
        if (openMilestones.size() >= MAX_MILESTONES) {
            ApplicationLogger.warn(
                LOG_SOURCE,
                'Milestone batch hit the ' + MAX_MILESTONES + ' ceiling for ' +
                caseIds.size() + ' cases; some milestones were not completed on this pass.'
            );
        }

        DateTime completedAt = System.now();
        for (CaseMilestone milestone : openMilestones) {
            milestone.CompletionDate = completedAt;
        }
        result.attempted = openMilestones.size();

        // The one DML. allOrNone = false so a single locked or inaccessible milestone
        // does not roll back the Case save that triggered this. The Apex Developer Guide
        // is explicit that Database class methods with partial success return a results
        // array instead of throwing, and that your code must iterate it to find out what
        // failed.
        List<Database.SaveResult> saveResults = Database.update(openMilestones, false);
        for (Integer i = 0; i < saveResults.size(); i++) {
            Database.SaveResult saveResult = saveResults[i];
            if (saveResult.isSuccess()) {
                result.completed++;
                continue;
            }
            for (Database.Error err : saveResult.getErrors()) {
                String detail = 'CaseMilestone ' + openMilestones[i].Id + ' (' +
                    err.getStatusCode() + '): ' + err.getMessage();
                result.failures.add(detail);
                ApplicationLogger.error(LOG_SOURCE, detail);
            }
        }
        return result;
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- CaseMilestoneService.cls-meta.xml -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

### If you do not want the `ApplicationLogger` dependency

`templates/apex/ApplicationLogger.cls` writes to a custom object `Application_Log__c` and
reads `Logger_Setting__mdt`. If the target org has neither, the service will not compile.
Two clean options, in order of preference:

1. Deploy the logger and its two metadata dependencies first (see the deploy order below).
   You want the failures queryable in production — this is a silent-failure domain.
2. Replace the two `ApplicationLogger` calls with `System.debug(LoggingLevel.ERROR, ...)`
   and accept that a partial-success failure is only visible in a debug log you have to be
   capturing at the time. Record the trade-off; do not leave the failures unhandled.

Do not delete the `for (Database.Error err : ...)` loop. Dropping it is how partial-success
DML becomes worse than all-or-nothing DML: the failures vanish with no exception raised.

---

## `CaseMilestoneTriggerHandler.cls`

```apex
/**
 * CaseMilestoneTriggerHandler — Case trigger handler for milestone completion.
 *
 * Extends templates/apex/TriggerHandler.cls. That base class owns the recursion guard,
 * the depth counter, and the TriggerControl activation check; this subclass owns one
 * decision — which milestone type this org completes on a Status change.
 *
 * afterUpdate() is the only overridden context. Entitlement rules run at step 15 of the
 * order of execution, after all before triggers (step 4) and all after triggers (step 8),
 * so a before-update hook would query milestone rows that do not exist yet on the save
 * that first puts the Case into the process.
 */
public with sharing class CaseMilestoneTriggerHandler extends TriggerHandler {

    /**
     * Exact MilestoneType.Name from Setup > Entitlement Management > Milestones.
     * @TestVisible so the test drives the same constant the trigger uses. If this org
     * needs more than one milestone type completed, promote it to Custom Metadata rather
     * than adding a second literal here.
     */
    @TestVisible
    private static String milestoneTypeName = 'First Response';

    protected override void afterUpdate() {
        CaseMilestoneService.completeMilestones(
            (List<Case>) Trigger.new,
            (Map<Id, Case>) Trigger.oldMap,
            milestoneTypeName
        );
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- CaseMilestoneTriggerHandler.cls-meta.xml -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## `CaseMilestoneTrigger.trigger`

One line. Every trigger in the org has this shape, which is what makes the
`TriggerControl` kill switch and the recursion guard uniform across objects.

```apex
/**
 * CaseMilestoneTrigger — completes CaseMilestone rows when a Case Status changes.
 *
 * Named for what it does to milestones, but it is a Case trigger: CaseMilestone rows are
 * created by the platform, not by DML, so there is no CaseMilestone DML event to hang
 * completion off. The Case save is the observable event.
 */
trigger CaseMilestoneTrigger on Case (after update) {
    new CaseMilestoneTriggerHandler().run();
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- CaseMilestoneTrigger.trigger-meta.xml -->
<ApexTrigger xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexTrigger>
```

`status` is `Active` on both file kinds, but the enumeration is not the same on both.
`ApexTrigger` accepts `Active`, `Inactive` and `Deleted`. `ApexClass` accepts only `Active`
and `Deleted` — the Metadata API guide notes that `ApexCodeUnitStatus` includes an
`Inactive` option but that it is supported only for `ApexTrigger`. Writing
`<status>Inactive</status>` into a `.cls-meta.xml` is a deploy error, not a disabled class.

---

## What `apiVersion` 67.0 changes

Per `agents/_shared/AGENT_CONTRACT.md` § *Apex security idiom by API version*, the
controlling fact is the `apiVersion` in the `-meta.xml`, not the org's release. At **67.0**:

| | At 67.0 (this bundle) | At 57.0 – 66.0 |
|---|---|---|
| Default access mode | **User mode.** SOQL, DML and `Database` methods enforce the running user's sharing, FLS and object permissions with no keyword | System mode |
| Read idiom | `WITH USER_MODE` to state intent explicitly; `WITH SYSTEM_MODE` plus a `// reason:` comment to opt out | `WITH USER_MODE` |
| Write idiom | `as user` / `as system`, or `AccessLevel.USER_MODE` on `Database` methods | same |
| `WITH SECURITY_ENFORCED` | **Does not compile.** Removed in 67.0 | Compiles, but legacy — migrate it |

Two consequences for this bundle specifically:

- **Do not add `WITH SECURITY_ENFORCED` to the `CaseMilestone` query.** At 67.0 it is a
  compile failure, not a style note. The checker flags it as ERROR when it can read a
  67.0+ `-meta.xml` next to the file, and as WARN when it cannot.
- **The trigger's own sharing context is irrelevant here, and that is not a loophole.**
  Apex triggers cannot carry a sharing declaration and always run implicitly
  `without sharing`; but at 67.0 the database operations *inside* the trigger body run in
  user mode unless system mode is explicitly named, which re-applies the running user's
  sharing on top. A service-agent user who cannot see a `CaseMilestone` row will not
  complete it through this trigger, and `Database.update(..., false)` will hand you that
  row's error rather than throwing.

---

## `CaseMilestoneServiceTest.cls`

### What this test needs from the org, and why it cannot build it itself

This is the part that makes milestone tests different from every other Apex test, so read
it before the code.

| Object | Supported calls | Can a test create it? |
|---|---|---|
| `MilestoneType` | `create()`, `delete()`, `describeSObjects()`, `query()`, `retrieve()`, `update()`, `upsert()` | Yes |
| `Entitlement` | `create()`, `delete()`, `describeLayout()`, `getDeleted()`, `getUpdated()`, `query()`, `retrieve()`, `search()`, `undelete()`, `update()`, `upsert()` | Yes |
| `SlaProcess` | `describeSObjects()`, `query()`, `retrieve()`, `search()`, `describeLayout()` | **No — there is no `create()`** |
| `CaseMilestone` | `describeLayout()`, `describeSObjects()`, `query()`, `retrieve()`, `update()` | **No — there is no `create()`** |

So the chain breaks in two places. A test can create the `Entitlement` and it can create
the `MilestoneType`, but it cannot create the `SlaProcess` that joins them, and it cannot
create the `CaseMilestone` rows that are the thing under test. Both must come from the
org: an entitlement process configured in Setup, and the platform's own entitlement rules
generating the milestone rows when a Case enters that process.

That forces the annotation. The test class below is `@IsTest(SeeAllData=true)` because it
has no other way to reach a real `SlaProcess`. Two constraints come with that choice:

- `@IsTest(SeeAllData=true)` and `@IsTest(IsParallel=true)` cannot be used together on the
  same class, so this class does not get parallel test execution.
- A `SeeAllData=true` test reads the org's actual data. It is order-sensitive and it can
  be broken by an admin deactivating the entitlement process. That is a real cost, and it
  is why the class fails loudly on a missing process instead of returning early.

The alternative — a `SeeAllData=false` class that creates an `Entitlement` pointing at an
`SlaProcessId` queried from the org — still reads the org for the process Id and still
produces no `CaseMilestone` rows if the process is inactive. It trades one dependency for
a subtler one. Pick `SeeAllData=true` and make the prerequisite explicit.

**Never let this test pass when the prerequisite is missing.** An empty
`List<CaseMilestone>` and a green test is the single worst outcome in this domain: it
certifies milestone automation that has never once run.

```apex
/**
 * CaseMilestoneServiceTest — proves the three behaviours that matter:
 *   1. an open milestone gets CompletionDate written
 *   2. an already-completed milestone is skipped on a second pass
 *   3. 200 Cases still cost one query and one DML
 *
 * SeeAllData=true is not laziness. SlaProcess has no create() call, so no test can build
 * an entitlement process; and CaseMilestone has no create() call, so no test can fake the
 * rows. Both have to come from the org.
 */
@IsTest(SeeAllData=true)
private class CaseMilestoneServiceTest {

    private static final String MILESTONE_TYPE = 'First Response';

    /**
     * Returns an active entitlement process, or fails the run with a message that names
     * the missing prerequisite. Deliberately Assert.fail rather than `return null` — a
     * skipped test in this domain is indistinguishable from a passing one.
     */
    private static SlaProcess requireActiveProcess() {
        List<SlaProcess> processes = [
            SELECT Id, Name
            FROM SlaProcess
            WHERE IsActive = true
            LIMIT 1
        ];
        if (processes.isEmpty()) {
            Assert.isTrue(
                false,
                'No active SlaProcess in this org. CaseMilestoneServiceTest cannot ' +
                'create one (SlaProcess has no create() call), so an entitlement ' +
                'process with a "' + MILESTONE_TYPE + '" milestone must exist in the ' +
                'target org before this test can prove anything.'
            );
        }
        return processes[0];
    }

    /** Account + Entitlement + one Case already inside the entitlement process. */
    private static Case caseInsideProcess(SlaProcess process) {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;

        Entitlement entitlement = new Entitlement(
            Name         = 'Milestone Test Entitlement',
            AccountId    = accounts[0].Id,
            SlaProcessId = process.Id,
            StartDate    = Date.today().addDays(-1),
            EndDate      = Date.today().addYears(1)
        );
        insert entitlement;

        List<Case> cases = TestDataFactory.createCases(
            1,
            accounts[0].Id,
            new Map<String, Object>{ 'EntitlementId' => entitlement.Id }
        );
        insert cases;
        return cases[0];
    }

    @IsTest
    static void writesCompletionDateOnAnOpenMilestone() {
        SlaProcess process = requireActiveProcess();
        Case subject = caseInsideProcess(process);

        List<CaseMilestone> before = [
            SELECT Id, CompletionDate
            FROM CaseMilestone
            WHERE CaseId = :subject.Id
              AND MilestoneType.Name = :MILESTONE_TYPE
              AND CompletionDate = NULL
        ];
        Assert.isFalse(
            before.isEmpty(),
            'No open "' + MILESTONE_TYPE + '" milestone was generated for the test ' +
            'Case. The entitlement process exists but does not include this milestone, ' +
            'or the Case did not enter the process. Nothing below would prove anything.'
        );

        // Build the "old" record explicitly rather than cloning — the Id and the prior
        // Status are the only two fields the service reads from Trigger.oldMap.
        Case previous = new Case(Id = subject.Id, Status = subject.Status);
        subject.Status = 'Working';

        Test.startTest();
        CaseMilestoneService.CompletionResult result = CaseMilestoneService.completeMilestones(
            new List<Case>{ subject },
            new Map<Id, Case>{ previous.Id => previous },
            MILESTONE_TYPE
        );
        Test.stopTest();

        Assert.areEqual(before.size(), result.attempted, 'Every open milestone should be attempted.');
        Assert.areEqual(before.size(), result.completed, 'Every attempted milestone should succeed.');
        Assert.areEqual(0, result.failures.size(), String.join(result.failures, ' | '));

        CaseMilestone reloaded = [
            SELECT Id, CompletionDate, IsCompleted
            FROM CaseMilestone
            WHERE Id = :before[0].Id
        ];
        Assert.isTrue(
            reloaded.CompletionDate != null,
            'CompletionDate is the only writable completion control on CaseMilestone; ' +
            'if it is still null the update did not take.'
        );
    }

    @IsTest
    static void skipsAMilestoneThatIsAlreadyCompleted() {
        SlaProcess process = requireActiveProcess();
        Case subject = caseInsideProcess(process);

        Case previous = new Case(Id = subject.Id, Status = subject.Status);
        subject.Status = 'Working';

        // First pass completes whatever is open.
        CaseMilestoneService.CompletionResult first = CaseMilestoneService.completeMilestones(
            new List<Case>{ subject },
            new Map<Id, Case>{ previous.Id => previous },
            MILESTONE_TYPE
        );
        Assert.isTrue(first.attempted > 0, 'Set-up pass must complete at least one milestone.');

        // Second pass over the same Case. The CompletionDate = NULL filter must exclude
        // everything the first pass stamped. This is the assertion that a real trigger
        // needs: a workflow field update re-fires before-update and after-update triggers
        // one more time on the same save, so the body genuinely runs twice.
        Case afterFirst = new Case(Id = subject.Id, Status = 'Escalated');

        Test.startTest();
        CaseMilestoneService.CompletionResult second = CaseMilestoneService.completeMilestones(
            new List<Case>{ afterFirst },
            new Map<Id, Case>{ subject.Id => new Case(Id = subject.Id, Status = 'Working') },
            MILESTONE_TYPE
        );
        Test.stopTest();

        Assert.areEqual(
            0,
            second.attempted,
            'A completed milestone must not be re-stamped. attempted > 0 means the ' +
            'CompletionDate = NULL filter is missing from the query.'
        );
        Assert.areEqual(0, second.failures.size(), String.join(second.failures, ' | '));
    }

    @IsTest
    static void staysAtOneQueryAndOneDmlFor200Cases() {
        SlaProcess process = requireActiveProcess();

        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;

        Entitlement entitlement = new Entitlement(
            Name         = 'Bulk Milestone Test Entitlement',
            AccountId    = accounts[0].Id,
            SlaProcessId = process.Id,
            StartDate    = Date.today().addDays(-1),
            EndDate      = Date.today().addYears(1)
        );
        insert entitlement;

        List<Case> cases = TestDataFactory.createCases(
            200,
            accounts[0].Id,
            new Map<String, Object>{ 'EntitlementId' => entitlement.Id }
        );
        insert cases;

        Map<Id, Case> oldMap = new Map<Id, Case>();
        List<Case> newCases = new List<Case>();
        for (Case original : cases) {
            oldMap.put(original.Id, new Case(Id = original.Id, Status = original.Status));
            newCases.add(new Case(Id = original.Id, Status = 'Working'));
        }

        Test.startTest();
        Integer queriesBefore = Limits.getQueries();
        Integer dmlBefore = Limits.getDmlStatements();

        CaseMilestoneService.CompletionResult result = CaseMilestoneService.completeMilestones(
            newCases, oldMap, MILESTONE_TYPE
        );

        Integer queriesUsed = Limits.getQueries() - queriesBefore;
        Integer dmlUsed = Limits.getDmlStatements() - dmlBefore;
        Test.stopTest();

        Assert.areEqual(1, queriesUsed, '200 Cases must cost exactly one SOQL query.');
        Assert.isTrue(dmlUsed <= 1, '200 Cases must cost at most one DML statement.');
        Assert.areEqual(
            result.attempted,
            result.completed + result.failures.size(),
            'Every attempted milestone must be accounted for as a success or a failure.'
        );
    }

    @IsTest
    static void ignoresCasesWhoseStatusDidNotChange() {
        List<Account> accounts = TestDataFactory.createAccounts(1, null);
        insert accounts;
        List<Case> cases = TestDataFactory.createCases(1, accounts[0].Id, null);
        insert cases;

        // No Status change, so the service must return before it queries anything.
        Test.startTest();
        Integer queriesBefore = Limits.getQueries();
        CaseMilestoneService.CompletionResult result = CaseMilestoneService.completeMilestones(
            cases,
            new Map<Id, Case>(cases),
            MILESTONE_TYPE
        );
        Integer queriesUsed = Limits.getQueries() - queriesBefore;
        Test.stopTest();

        Assert.areEqual(0, result.attempted, 'An unchanged Status must attempt nothing.');
        Assert.areEqual(0, queriesUsed, 'An unchanged Status must not reach the query.');
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- CaseMilestoneServiceTest.cls-meta.xml -->
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

The fourth test method is the only one that does not need the entitlement process at all.
Keep it: it is the one assertion in the class that still runs in a scratch org with no
entitlement configuration, and it covers the early-return path that most of the
production traffic actually takes.

---

## `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>CaseMilestoneService</members>
        <members>CaseMilestoneServiceTest</members>
        <members>CaseMilestoneTriggerHandler</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>CaseMilestoneTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <version>67.0</version>
</Package>
```

The `<version>` in `package.xml` is the deploy-request version. It is not what governs the
security idiom — that is the `<apiVersion>` inside each `-meta.xml`. Keeping both at 67.0
avoids a bundle where the manifest says one thing and the classes behave as another.

If you are deploying the shared templates in the same request, add them to the same
manifest rather than making a second deploy:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>ApplicationLogger</members>
        <members>CaseMilestoneService</members>
        <members>CaseMilestoneServiceTest</members>
        <members>CaseMilestoneTriggerHandler</members>
        <members>TriggerControl</members>
        <members>TriggerHandler</members>
        <name>ApexClass</name>
    </types>
    <types>
        <members>CaseMilestoneTrigger</members>
        <name>ApexTrigger</name>
    </types>
    <types>
        <members>Trigger_Setting__mdt</members>
        <name>CustomObject</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## Deploy prerequisites

Every file in this bundle compiles only if the canonical template classes it references
(see **Bundle contents** above) are present in the same deployable set as verbatim copies
of the files at these paths — each with its own `-meta.xml` — before or alongside the
bundle:

| Template class | Canonical path | Consumed by |
|---|---|---|
| `TriggerHandler` | `templates/apex/TriggerHandler.cls` | `CaseMilestoneTriggerHandler extends TriggerHandler` |
| `TriggerControl` | `templates/apex/TriggerControl.cls` | `TriggerHandler.run()` calls `TriggerControl.isActive(...)` on its first line |
| `ApplicationLogger` | `templates/apex/ApplicationLogger.cls` | `CaseMilestoneService`'s partial-success failure logging |
| `TestDataFactory` | `templates/apex/tests/TestDataFactory.cls` | `CaseMilestoneServiceTest.createAccounts(...)` / `.createCases(...)` |

These four are referenced by relative path in the class bodies above, not copied into this
bundle's own four files. Shipping the bundle without also shipping these — for example, a
build step that ships `CaseMilestoneServiceTest.cls` without a step that ever shipped
`TestDataFactory.cls` — compiles the trigger and the service and then fails deploy with
`Variable does not exist: TestDataFactory` (F-37, case-onboarding M4-S05, org dry run
2026-09-12: `templates/README.md` documents templates as copied into the consuming
project, and "referenced by relative path" in this file is not the same thing as "shipped
by an earlier step"). Rule `EAH009` in this skill's checker (see **Verification** below)
WARNs when a `.cls` under the manifest directory references one of these names with no
matching `.cls` of that name under the same directory.

---

## Deploy order

Metadata deploys resolve within a single request, so a one-shot deploy of the second
manifest above works. The order below is what you need when the pieces land in separate
requests, and it is the order to read when a deploy fails on a missing dependency.

| # | Deploy | Depends on | If you skip it |
|---|---|---|---|
| 1 | Setup: entitlement process with the `First Response` milestone, entitlement applied to the Cases | — | The classes deploy and the tests fail on `requireActiveProcess()`. That is the correct failure. |
| 2 | `Trigger_Setting__mdt` (from `templates/apex/cmdt/`) | — | `TriggerControl.cls` does not compile; its SOQL references the type's fields. |
| 3 | `Application_Log__c` + `Logger_Setting__mdt` | — | `ApplicationLogger.cls` does not compile. |
| 4 | `TriggerControl.cls`, `ApplicationLogger.cls` | 2, 3 | `TriggerHandler.run()` and the service have unresolved references. |
| 5 | `TriggerHandler.cls` | 4 | `CaseMilestoneTriggerHandler` has no base class. |
| 6 | `CaseMilestoneService.cls` | 4 | The handler has nothing to call. |
| 7 | `CaseMilestoneTriggerHandler.cls` | 5, 6 | The trigger has no handler. |
| 8 | `CaseMilestoneTrigger.trigger` | 7 | Nothing fires. |
| 9 | `CaseMilestoneServiceTest.cls` | 1, 6 | No coverage, and the deploy is rejected in production. |

Step 1 is genuinely first. The classes will deploy without it, but every assertion that
matters is unreachable until an entitlement process exists and Cases are entering it.

---

## Verification

Run the skill's checker against the metadata tree before the deploy. It is stdlib-only
Python, so it needs nothing installed and no org connection.

```bash
# From the repo root, pointed at whatever directory holds the four files above.
python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py \
    --manifest-dir force-app/main/default

# Treat WARN findings as blocking too — recommended in CI.
python3 skills/apex/entitlement-apex-hooks/scripts/check_entitlement_apex_hooks.py \
    --manifest-dir force-app/main/default \
    --strict
```

Expected on a clean extraction of this bundle:

```text
scanned 4 Apex file(s) under force-app/main/default: 0 ERROR, 0 WARN
```

Exit codes:

| Situation | Exit code |
|---|---|
| `--manifest-dir` missing or not a directory | 1 |
| Directory exists, no `.cls` / `.trigger` under it | 0 (a WARN is printed; `--strict` makes it 1) |
| One or more ERROR findings | 1 |
| WARN findings only | 0, or 1 with `--strict` |

What the checker will catch in this domain:

| Rule | Severity | What it flags |
|---|---|---|
| `EAH001` | ERROR | SOQL or DML inside a loop — names `Trigger.new` explicitly when that is what is being iterated |
| `EAH002` | ERROR | Assignment to `IsCompleted`, `IsViolated` or `TargetDate` — none carry the `Update` property |
| `EAH003` | ERROR | Any `SlaExitDate` reference in a file that mentions `CaseMilestone` |
| `EAH004` | ERROR | `insert` / `delete` / `upsert` on a `CaseMilestone` variable |
| `EAH005` | ERROR at 67.0+, else WARN | `WITH SECURITY_ENFORCED` — reads the neighbouring `-meta.xml` for the version |
| `EAH006` | WARN | `CaseMilestone` query with no `CompletionDate = NULL` filter |
| `EAH007` | WARN | Numeric comparison against `TimeRemainingInMins` / `TimeRemainingInHrs`, which are `text` |
| `EAH008` | WARN | `CaseMilestone` trigger inspecting `IsViolated`; before-trigger touching `CaseMilestone` |
| `EAH009` | WARN, `--strict` promotes | A `.cls` references a canonical template class name (`TriggerHandler`, `TriggerControl`, `ApplicationLogger`, `TestDataFactory`, `TestRecordBuilder`, `MockHttpResponseGenerator`, `SecurityUtils`, `TestUserFactory`, `BulkTestPattern`, `BaseDomain`, `BaseService`, `BaseSelector`, `HttpClient`) with no `.cls` of that name under the same `--manifest-dir`. WARN because the checker sees one manifest directory, not the whole build plan — it cannot know the class ships from an earlier step. |

After deploy, the org-side verification is a debug log, not a field check. Set a debug log
on the case owner with the **Workflow** category at **INFO** and push a Case through the
intake channel. The Apex Developer Guide documents four entitlement-engine events at that
level: `SLA_PROCESS_CASE` (the engine looked at this Case), `SLA_EVAL_MILESTONE` (a
specific milestone was evaluated), `SLA_NULL_START_DATE` (the Case has no SLA start date
— it never entered a process), and `SLA_END` (what the engine did, including how many case
milestones it inserted, updated or deleted). Absence of all four means the engine never
ran, which is an entitlement-on-the-Case problem and not a problem with any code above.

---

## Source lines behind the claims in this file

Every non-obvious assertion above traces to one of these. Line numbers are into the
plain-text extracts of the v62 *Object Reference for the Salesforce Platform*
(`object_reference.txt`), the v62 *Apex Developer Guide* (`apexdev`), and the
*Metadata API Developer Guide* (`api_meta`).

| Claim | Source |
|---|---|
| `CaseMilestone` supported calls: `describeLayout()`, `describeSObjects()`, `query()`, `retrieve()`, `update()` | `object_reference.txt L63346–63347` |
| `CompletionDate` properties `Filter, Nillable, Update` | `object_reference.txt L63376–63382` |
| `StartDate` properties `Filter, Nillable, Update` | `object_reference.txt L63434–63440` |
| `IsCompleted` properties `Defaulted on create, Filter` (no `Update`) | `object_reference.txt L63404–63410` |
| `IsViolated` properties `Defaulted on create, Filter` | `object_reference.txt L63411–63419` |
| `TargetDate` properties `Filter` only | `object_reference.txt L63441–63447` |
| `TimeRemainingInMins` is type `text`, "format is minutes and seconds" | `object_reference.txt L63492–63499` |
| `SlaProcess` supported calls — no `create()` | `object_reference.txt L270650–270651` |
| `Entitlement` supported calls include `create()` | `object_reference.txt L110181–110182` |
| `MilestoneType` supported calls include `create()` | `object_reference.txt L183197–183198` |
| `SlaExitDate` exists on `WorkOrder`, not on `CaseMilestone` | `object_reference.txt L317989–317993` |
| Order of execution: after triggers step 8, entitlement rules step 15 | `apexdev L15448, L15471` |
| Workflow field update re-fires before/after update triggers once more | `apexdev L15451, L15458–15459` |
| Triggers run implicitly `without sharing`; body operations run in user mode at 67.0 | `apexdev L4881–4885, L4887–4892` |
| Database class methods allow partial success and return a results array to iterate | `apexdev L7583–7585, L8429–8433, L9058–9065` |
| `@IsTest(SeeAllData=true)` semantics; cannot combine with `IsParallel=true` | `apexdev L5802–5824` |
| SOQL inside a for loop executes once per iteration and can exceed the query limit | `apexdev L20220–20222` |
| Entitlement-engine debug events at Workflow/INFO | `apexdev L39104–39117` |
| `ApexClass` `status` accepts `Active` / `Deleted`; `Inactive` is `ApexTrigger`-only | `api_meta L22271–22279` |
| `ApexTrigger` `status` accepts `Active` / `Inactive` / `Deleted` | `api_meta L22767–22773` |
| `-meta.xml` shape for `ApexClass` and `ApexTrigger` | `api_meta L22335–22338, L22789–22792` |

UNVERIFIED (2026-09-12): that writing a non-null `CompletionDate` is what makes
`IsCompleted` read back as `true`. The Object Reference establishes that `CompletionDate`
is updateable and `IsCompleted` is not, which is why the write goes to `CompletionDate` —
but no extract in the corpus states the causal link between the two fields. Assert on
`CompletionDate` being non-null, as the test above does, and treat `IsCompleted` as a
convenience for reporting rather than the thing your code controls.

UNVERIFIED (2026-09-12): the 3-argument `Database.update(records, allOrNone, AccessLevel)`
overload. The Apex Developer Guide shows that shape for `Database.insert`
(`apexdev L12602`), and shows `AccessLevel.USER_MODE` on `Database` DML generally
(`apexdev L11992–11995`), but the extract contains no `Database.update` call with three
arguments. The service above uses the two-argument form and relies on 67.0's default user
mode, so it does not depend on this.

UNVERIFIED (2026-09-12): three identifiers used by the test class above do not appear in
the Apex Developer Guide extract, so they are written from the platform's documented
`System` namespace rather than copied from a corpus line. The extract shows
`Assert.areEqual`, `Assert.isTrue` and `Assert.isFalse` (`apexdev L1319, L5391–5393`) but
none of their message-carrying overloads; it shows `Limits.getQueries()`
(`apexdev L29731`) but not `Limits.getDmlStatements()`; and it shows `Test.startTest()` /
`Test.stopTest()` (`apexdev L5382, L5388`) but no `Assert.fail` or `Assert.isNotNull`,
which is why neither is used above. If a compile fails on a message overload, drop the
message argument — the assertion still holds, you just lose the diagnostic.
