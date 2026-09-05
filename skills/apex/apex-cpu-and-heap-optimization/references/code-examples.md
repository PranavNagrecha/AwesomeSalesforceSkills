# Code Examples — Apex CPU And Heap Optimization

A complete, deployable before/after pair plus the test that proves the fix, the
`-meta.xml`, a `package.xml`, and the commands that verify it in an org.

---

## The budget you are spending

Every number below is from the *Salesforce Developer Limits and Allocations Quick
Reference*, "Per-Transaction Apex Limits" table
(`salesforce_app_limits_cheatsheet.txt` L57–L106, footnote 4 at L161, footnote 5
at L170–L177) and the Apex Developer Guide's copy of the same table
(`apexdev.txt` L19577–L19601).

| Resource | Synchronous | Asynchronous | Read it at runtime with |
|---|---|---|---|
| Maximum CPU time on the Salesforce servers | 10,000 ms | 60,000 ms | `Limits.getCpuTime()` / `Limits.getLimitCpuTime()` |
| Total heap size | 6 MB | 12 MB | `Limits.getHeapSize()` / `Limits.getLimitHeapSize()` |
| Maximum execution time for each Apex transaction | 10 minutes | 10 minutes | not exposed on `Limits` |
| Records retrieved by `Database.getQueryLocator` | 10,000 | 10,000 | `Limits.getQueryLocatorRows()` |

Three facts that change how you read that table:

- **Asynchronous does not mean "any async".** The table's asynchronous column is
  for Batch Apex and future methods; the guide states "Although scheduled Apex is
  an asynchronous feature, synchronous limits apply to scheduled Apex jobs"
  (`salesforce_app_limits_cheatsheet.txt` L36–L37). A `Schedulable.execute` body
  gets 10,000 ms, not 60,000 ms.
- **Database time is not CPU time, but DML is.** "Application server CPU time
  spent in DML operations is counted towards the Apex CPU limit… the portion of
  execution time spent in the database for DML, SOQL, and SOSL isn't counted, nor
  is waiting time for Apex callouts" (`salesforce_app_limits_cheatsheet.txt`
  L173–L176). So a slow query burns the 10-minute transaction budget without
  moving `Limits.getCpuTime()`.
- **`Limits.getHeapSize()` is approximate.** The Apex Reference Guide defines it
  as "the approximate amount of memory (in bytes) that has been used for the
  heap" (`apexrefguide.txt` L220711–L220722). Treat it as a headroom signal, not
  an accounting record.

---

## 1. Before — the shape that fails

This compiles, is fully bulkified (no SOQL or DML in a loop), and still dies on
`System.LimitException` at volume. Both defects are algorithmic, not database.

```apex
/**
 * ANTI-PATTERN — kept only as the "before" of the refactor. Do not deploy.
 *
 * Defect 1 (CPU): the inner loop rescans every Opportunity for every Account,
 *                 so cost grows with accounts x opportunities.
 * Defect 2 (heap): `summary` is a String rebuilt on every concatenation; Apex
 *                  String size is "governed by the heap size limit"
 *                  (apexdev.txt L1275).
 */
public with sharing class AccountRollupServiceV0 {

    public static void recalculate(List<Account> accounts, List<Opportunity> opportunities) {
        for (Account acct : accounts) {
            Decimal openAmount = 0;
            String summary = '';
            for (Opportunity opp : opportunities) {
                if (opp.AccountId == acct.Id && !opp.IsClosed) {
                    openAmount += (opp.Amount == null ? 0 : opp.Amount);
                    summary += opp.Name + ';';
                }
            }
            acct.AnnualRevenue = openAmount;
            acct.Description = summary;
        }
        update accounts;
    }
}
```

---

## 2. After — index once, then look up

Same behaviour, one pass over each collection, and it reports its own cost
through `templates/apex/ApplicationLogger.cls` instead of `System.debug`.

```apex
/**
 * AccountRollupService — Map-indexed rollup with CPU/heap instrumentation.
 *
 * Extends templates/apex/BaseService.cls (savepoint + logAndRethrow helpers).
 * Logging goes through templates/apex/ApplicationLogger.cls so the measurement
 * survives in production, where debug logs are usually off.
 */
public with sharing class AccountRollupService extends BaseService {

    private static final String SOURCE = 'AccountRollupService.recalculate';

    public void recalculate(List<Account> accounts, List<Opportunity> opportunities) {
        Integer cpuStart  = Limits.getCpuTime();
        Integer heapStart = Limits.getHeapSize();

        Map<Id, Decimal> openAmountByAccountId = new Map<Id, Decimal>();
        Map<Id, List<String>> openNamesByAccountId = new Map<Id, List<String>>();

        for (Opportunity opp : opportunities) {
            if (opp.AccountId == null || opp.IsClosed) {
                continue;
            }
            Decimal running = openAmountByAccountId.get(opp.AccountId);
            Decimal amount  = opp.Amount == null ? 0 : opp.Amount;
            openAmountByAccountId.put(opp.AccountId, (running == null ? 0 : running) + amount);

            List<String> names = openNamesByAccountId.get(opp.AccountId);
            if (names == null) {
                names = new List<String>();
                openNamesByAccountId.put(opp.AccountId, names);
            }
            names.add(opp.Name);
        }

        for (Account acct : accounts) {
            Decimal openAmount   = openAmountByAccountId.get(acct.Id);
            List<String> names   = openNamesByAccountId.get(acct.Id);
            acct.AnnualRevenue   = openAmount == null ? 0 : openAmount;
            acct.Description     = names == null ? null : String.join(names, ';').left(32000);
        }

        update accounts;

        ApplicationLogger.info(
            SOURCE,
            'accounts=' + accounts.size()
                + ' opps=' + opportunities.size()
                + ' cpuMs=' + (Limits.getCpuTime() - cpuStart)
                + ' of ' + Limits.getLimitCpuTime()
                + ' heapBytes=' + (Limits.getHeapSize() - heapStart)
                + ' of ' + Limits.getLimitHeapSize()
        );
        ApplicationLogger.flush();
    }
}
```

**Instrumentation rules this obeys**

- The checkpoints bracket a *block*, never sit inside the hot loop. Calling
  `Limits.getCpuTime()` per iteration adds its own cost and tells you nothing you
  cannot get from a block delta.
- It logs a delta plus the ceiling from `getLimitCpuTime()` / `getLimitHeapSize()`
  rather than a raw number, so the same line reads correctly in a synchronous
  (10,000 ms / 6 MB) and asynchronous (60,000 ms / 12 MB) context.
- `ApplicationLogger.info` buffers; `flush()` performs one DML at the end. Call
  `flush()` once per entry point, not per checkpoint.

---

## 3. Heap-safe chunking — SOQL for loop inside Batch Apex

The guide's own remedy for the heap limit: "Use SOQL for loops to operate on
records in batches of 200. This helps avoid the heap size limit of 6 MB"
(`apexdev.txt` L20271–L20285). The list form runs the body once per list of 200
sObjects (`apexdev.txt` L10023–L10030).

```apex
/**
 * AccountRollupBatch — rolls up open Opportunity amounts account by account.
 *
 * Deliberately NOT Database.Stateful: "all member variables are reset to their
 * initial state at the start of each transaction" (apexdev.txt L17742-L17743),
 * which is what keeps heap flat across chunks. Governor limits are reset for
 * each execution of execute (apexdev.txt L17709-L17710).
 */
public with sharing class AccountRollupBatch implements Database.Batchable<SObject> {

    public Database.QueryLocator start(Database.BatchableContext ctx) {
        return Database.getQueryLocator(
            'SELECT Id, Name FROM Account WHERE Id IN (SELECT AccountId FROM Opportunity WHERE IsClosed = false)'
        );
    }

    public void execute(Database.BatchableContext ctx, List<Account> scope) {
        Map<Id, Account> accountsById = new Map<Id, Account>(scope);
        Map<Id, Decimal> openAmountByAccountId = new Map<Id, Decimal>();

        for (List<Opportunity> chunk : [
            SELECT Id, AccountId, Amount
            FROM Opportunity
            WHERE AccountId IN :accountsById.keySet() AND IsClosed = false
            WITH USER_MODE
        ]) {
            for (Opportunity opp : chunk) {
                Decimal running = openAmountByAccountId.get(opp.AccountId);
                Decimal amount  = opp.Amount == null ? 0 : opp.Amount;
                openAmountByAccountId.put(opp.AccountId, (running == null ? 0 : running) + amount);
            }
        }

        List<Account> toUpdate = new List<Account>();
        for (Id accountId : openAmountByAccountId.keySet()) {
            toUpdate.add(new Account(Id = accountId, AnnualRevenue = openAmountByAccountId.get(accountId)));
        }
        if (!toUpdate.isEmpty()) {
            update toUpdate;
        }

        ApplicationLogger.info(
            'AccountRollupBatch.execute',
            'scope=' + scope.size()
                + ' cpuMs=' + Limits.getCpuTime() + ' of ' + Limits.getLimitCpuTime()
                + ' heapBytes=' + Limits.getHeapSize() + ' of ' + Limits.getLimitHeapSize()
        );
        ApplicationLogger.flush();
    }

    public void finish(Database.BatchableContext ctx) {
        ApplicationLogger.info('AccountRollupBatch.finish', 'job=' + ctx.getJobId());
        ApplicationLogger.flush();
    }
}
```

**Why the accumulator map is safe and a `List<Opportunity>` is not:** the map
holds one `Decimal` per account in scope (at most 2,000 entries — the maximum
`scope` value for a `QueryLocator` start method, `apexdev.txt` L17703–L17707).
The rejected alternative, `List<Opportunity> all = [SELECT …]`, holds every child
row of every account in the chunk at once, and "There is no limit on the number
of items a collection can hold. However, there is a general limit on heap size"
(`apexdev.txt` L1431).

**The cost you accept:** the guide is explicit that the for-loop form "can result
in more CPU cycles being used" than one bulk query (`apexdev.txt` L10014–L10016,
L9601–L9602). You are trading CPU for heap. Instrument both before deciding.

---

## 4. The test — assert headroom, not just correctness

```apex
/**
 * AccountRollupServiceTest — bulk test with CPU and heap headroom assertions.
 *
 * Seeding uses templates/apex/tests/TestDataFactory.cls; the bulk shape follows
 * templates/apex/tests/BulkTestPattern.cls.
 *
 * The measurement MUST be taken between Test.startTest() and Test.stopTest():
 * "Any code that executes after the call to startTest and before stopTest is
 * assigned a new set of governor limits" and "Any code that executes after the
 * stopTest method is assigned the original limits that were in effect before
 * startTest was called" (apexrefguide.txt L241071, L241086-L241087). A CPU
 * reading taken after stopTest measures the setup block, not the code you are
 * testing.
 */
@IsTest
private class AccountRollupServiceTest {

    private static final Integer ACCOUNT_COUNT     = 200;
    private static final Integer OPPS_PER_ACCOUNT  = 3;

    @TestSetup
    static void seed() {
        List<Account> accounts = TestDataFactory.createAccounts(ACCOUNT_COUNT, null);
        insert accounts;

        List<Opportunity> opportunities = new List<Opportunity>();
        for (Account acct : accounts) {
            opportunities.addAll(TestDataFactory.createOpportunities(OPPS_PER_ACCOUNT, acct.Id, null));
        }
        insert opportunities;
    }

    @IsTest
    static void rollupStaysInsideCpuAndHeapBudgetAt200Accounts() {
        List<Account> accounts = [SELECT Id, Name FROM Account LIMIT 200];
        List<Opportunity> opportunities = [
            SELECT Id, AccountId, Name, Amount, IsClosed FROM Opportunity
        ];
        Assert.areEqual(ACCOUNT_COUNT, accounts.size(), 'Bulk test must run at 200 parent records');
        Assert.areEqual(ACCOUNT_COUNT * OPPS_PER_ACCOUNT, opportunities.size(), 'Seed did not create the expected children');

        Test.startTest();
        Integer cpuBefore  = Limits.getCpuTime();
        Integer heapBefore = Limits.getHeapSize();

        new AccountRollupService().recalculate(accounts, opportunities);

        Integer cpuUsed  = Limits.getCpuTime() - cpuBefore;
        Integer heapUsed = Limits.getHeapSize() - heapBefore;
        Integer cpuCeiling  = Limits.getLimitCpuTime();
        Integer heapCeiling = Limits.getLimitHeapSize();
        Test.stopTest();

        Assert.isTrue(
            cpuUsed < cpuCeiling / 4,
            'Rollup must leave 75% CPU headroom for callers and downstream automation: used '
                + cpuUsed + ' ms of ' + cpuCeiling + ' ms'
        );
        Assert.isTrue(
            heapUsed < heapCeiling / 4,
            'Rollup must leave 75% heap headroom: used ' + heapUsed + ' bytes of ' + heapCeiling + ' bytes'
        );

        Map<Id, Account> reloaded = new Map<Id, Account>(
            [SELECT Id, AnnualRevenue, Description FROM Account WHERE Id IN :accounts]
        );
        for (Account acct : accounts) {
            Assert.areEqual(
                3000,
                reloaded.get(acct.Id).AnnualRevenue,
                'Each account should roll up 3 open opportunities at 1000 each'
            );
        }
    }

    @IsTest
    static void rollupHandlesAccountsWithNoOpportunities() {
        List<Account> orphans = TestDataFactory.createAccounts(200, null);
        insert orphans;

        Test.startTest();
        new AccountRollupService().recalculate(orphans, new List<Opportunity>());
        Test.stopTest();

        for (Account acct : orphans) {
            Assert.areEqual(0, acct.AnnualRevenue, 'Accounts with no open opportunities roll up to zero');
            Assert.isNull(acct.Description, 'No names means no summary string');
        }
    }
}
```

**Why the headroom fraction and not the raw ceiling.** Asserting
`cpuUsed < cpuCeiling` only fails when the code is already broken in production.
A fraction fails while there is still room to fix it, and it survives the
sync/async difference because `getLimitCpuTime()` returns whichever ceiling the
current context has. Note the caveat: "Limits apply individually to each
testMethod" (`salesforce_app_limits_cheatsheet.txt` L180) — a green test is
evidence about one method's budget, not about the whole save order.

---

## 5. Class metadata

Every `.cls` above needs a sibling `<ClassName>.cls-meta.xml`. The API version
matches the repo's canonical classes (`templates/apex/ApplicationLogger.cls-meta.xml`).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 6. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>AccountRollupService</members>
        <members>AccountRollupBatch</members>
        <members>AccountRollupServiceTest</members>
        <members>ApplicationLogger</members>
        <members>BaseService</members>
        <members>TestDataFactory</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 7. Deploy and verify

```bash
# 1. Static check before the org ever sees it
python3 skills/apex/apex-cpu-and-heap-optimization/scripts/check_apex_cpu_and_heap_optimization.py \
    --manifest-dir force-app/main/default/classes

# 2. Deploy the manifest
sf project deploy start --manifest manifest/package.xml --target-org myScratch

# 3. Run the bulk test and read the headroom assertions
sf apex run test \
    --tests AccountRollupServiceTest \
    --result-format human \
    --code-coverage \
    --wait 10 \
    --target-org myScratch

# 4. Read the real numbers out of the debug log for the run
sf apex get log --number 1 --target-org myScratch | grep -A 14 CUMULATIVE_LIMIT_USAGE
```

Step 4 prints the `LIMIT_USAGE_FOR_NS` block — the log event that carries
"Maximum heap size" and CPU per namespace (`apexdev.txt` L38275–L38284,
L38930–L38941). One caution when reading it: "To reduce the overhead on small
transactions, minimal heap usage doesn't warrant an accurate calculation and is
reported as 0(zero)" (`apexdev.txt` L38239–L38241). A zero there means "too small
to bother measuring", not "no heap used".

---

## How to read the artifact

- **`AccountRollupServiceV0` is the specimen, not the deliverable.** Deploy only
  §2, §3 and §4. §1 exists so a reviewer can diff the shape.
- **Both defects in §1 are invisible to a bulkification review.** There is no SOQL
  and no DML inside any loop. Bulkification and CPU/heap safety are separate
  properties.
- **`update accounts` in §2 mutates the caller's list in place.** That is
  deliberate: cloning a large sObject list to "be safe" doubles heap for no
  behavioural gain (see `references/llm-anti-patterns.md` #5).
- **`String.join(names, ';')` replaces `summary += …`.** One join allocates one
  result string; repeated `+=` in a loop allocates a new string per iteration, and
  Apex String size is bounded by the heap limit (`apexdev.txt` L1275). *UNVERIFIED
  (2026-09-05): the Apex Developer Guide states the heap bound on String size but
  does not publish the allocation behaviour of `+=` in a loop; the "one allocation
  per iteration" reasoning is practitioner inference, not a documented claim.*
- **§3 chooses heap over CPU on purpose.** If your failure is CPU rather than
  heap, the SOQL for loop is the wrong lever — see `references/gotchas.md`,
  "A SOQL for loop trades heap for CPU".
- **§4 measures inside `Test.startTest()`/`Test.stopTest()`.** Moving those two
  `Limits` reads outside the block silently changes what is being measured.
