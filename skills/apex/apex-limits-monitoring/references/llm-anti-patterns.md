# LLM Anti-Patterns — Apex Limits Monitoring

Common mistakes AI coding assistants make when generating or advising on Apex governor limit defensive coding and monitoring. These patterns help the consuming agent self-check its own output. `scripts/check_apex_limits_monitoring.py` detects several of them mechanically.

## Anti-Pattern 1: Trying to Catch `System.LimitException`

**What the LLM generates:**

```apex
try {
    List<Account> results = [SELECT Id FROM Account WHERE Name != null];
    update results;
} catch (System.LimitException le) {
    System.debug('Limit hit: ' + le.getMessage());
    // graceful degradation logic
}
```

**Why it happens:** LLMs are trained on Java and general exception-handling idioms where catching runtime exceptions is a common defensive pattern. They apply this to Apex without recognizing that `System.LimitException` is one of the exceptions the Apex runtime refuses to route through a handler.

**Correct pattern:**

```apex
// Guard BEFORE the query — prevention, not recovery
if (LimitGuard.nearSoql(80)) {
    LogService.warn('AccountSync.run', 'degraded: ' + LimitGuard.snapshot());
    return new List<Account>();
}
List<Account> results = [SELECT Id FROM Account WHERE Name != null];
```

**Detection hint:** search for `catch.*LimitException`. Any such block is wrong. The checker treats it as an ERROR.

---

## Anti-Pattern 2: Flushing a Log Buffer in a `finally` Block "So It Survives a Limit Breach"

**What the LLM generates:**

```apex
public static void process(List<Order> orders) {
    try {
        doExpensiveWork(orders);
    } finally {
        // "this always runs, so the limit breach will be logged"
        LogService.flush();
    }
}
```

**Why it happens:** `finally` always runs is true in Java and true in Apex for every *catchable* exception, so the inference is reasonable and wrong. The guide states the exception explicitly: "When exceptions are uncatchable, catch blocks, as well as `finally` blocks if any, aren't executed" (`apexdev L39727–39728`).

**Correct pattern:**

```apex
// Log the decision at the guard, before the operation that might breach.
if (LimitGuard.nearAny(85)) {
    LogService.warn('OrderService.process',
        'stopping early, worst=' + LimitGuard.worst().name + ' ' + LimitGuard.snapshot());
    LogService.flush();          // flushed here, while the transaction is still alive
    return;
}
doExpensiveWork(orders);
```

**Detection hint:** a `finally` block whose only purpose is logging, in a method described as limit-defensive, is a false safety net. Post-mortem belongs in `BatchApexErrorEvent`, a Finalizer, or the `ApexUnexpectedException` event log.

---

## Anti-Pattern 3: Comparing `Limits.getX()` to a Hardcoded Number

**What the LLM generates:**

```apex
// Hardcoded to the sync ceiling — wrong in Batch and Queueable, and brittle everywhere
private static final Integer MAX_SOQL = 100;

if (Limits.getQueries() >= MAX_SOQL - 10) {
    return;
}
```

**Why it happens:** synchronous examples dominate the training corpus, so 100 SOQL, 10,000 ms CPU and 6 MB heap get baked in as constants. The same code in a Batch `execute` throws away half its allocation; a Scheduled class assuming the async numbers has half the room it expects.

**Correct pattern:**

```apex
// getLimitQueries() returns the ceiling for whatever context this is
if ((Limits.getLimitQueries() - Limits.getQueries()) < 10) {
    return;
}
// or, once LimitGuard is deployed:
if (!LimitGuard.hasRoomFor('soql', 10)) {
    return;
}
```

**Detection hint:** any integer literal or constant compared against `Limits.getQueries()`, `getDMLStatements()`, `getCpuTime()` or `getHeapSize()` should be the matching `getLimitX()` call instead. The checker flags this as a WARN.

---

## Anti-Pattern 4: Calling `getLimitX()` Without `getX()`

**What the LLM generates:**

```apex
// WRONG — this checks the ceiling, not remaining headroom
if (Limits.getLimitQueries() < 10) {
    return;
}
```

**Why it happens:** the model knows `getLimitX()` is "the limit method" and drops the consumption half. The condition is a constant: the ceiling does not move within a transaction, so the branch is dead code that reads as protection.

**Correct pattern:**

```apex
Integer soqlRemaining = Limits.getLimitQueries() - Limits.getQueries();
if (soqlRemaining < 10) {
    return;
}
```

**Detection hint:** a guard that names `getLimitX()` with no paired `getX()` subtraction is always wrong for a headroom check.

---

## Anti-Pattern 5: Polling `Limits.getCpuTime()` on Every Iteration of a Tight Loop

**What the LLM generates:**

```apex
for (Integer i = 0; i < 50000; i++) {
    if (Limits.getCpuTime() > 9000) {   // checked 50,000 times
        break;
    }
    total += compute(items[i]);
}
```

**Why it happens:** "check the limit before each expensive operation" is correct advice for SOQL and DML, and the model generalises it to CPU. But the check is itself Apex execution, and CPU time is "calculated for the executing Apex code" (`apexdev L19645–19646`) — the guard consumes the resource it is guarding, and does so proportionally to the loop it is protecting.

**Correct pattern:**

```apex
Integer checkEvery = 500;
for (Integer i = 0; i < items.size(); i++) {
    if (Math.mod(i, checkEvery) == 0 && LimitGuard.nearCpu(85)) {
        LogService.warn('Calc.run', 'stopped at ' + i + ': ' + LimitGuard.snapshot());
        break;
    }
    total += compute(items[i]);
}
```

**Detection hint:** `Limits.getCpuTime()` inside a loop body with no modulo or counter gate. The checker raises this as ADVISORY, not ERROR — it is a cost question, not a correctness one, and in a short loop the sampling gate is not worth the complexity.

---

## Anti-Pattern 6: Guarding `getAggregateQueries()` Before a `COUNT()` or `GROUP BY`

**What the LLM generates:**

```apex
// Believed to be the guard for aggregate-function queries. It is not.
if ((Limits.getLimitAggregateQueries() - Limits.getAggregateQueries()) < 5) {
    return;
}
AggregateResult[] results = [
    SELECT AccountId, COUNT(Id) total FROM Contact GROUP BY AccountId
];
```

**Why it happens:** the method name says "aggregate", and the query uses an aggregate function, so the association is irresistible. The platform means something else by the word: the meter tracks parent-child relationship subqueries, and its ceiling "corresponds to" three times the top-level query limit (`apexdev L19612–19616`).

**Correct pattern:**

```apex
// A COUNT()/GROUP BY query consumes an ordinary SOQL slot.
if (!LimitGuard.hasRoomFor('soql', 1)) {
    return;
}
AggregateResult[] results = [
    SELECT AccountId, COUNT(Id) total FROM Contact GROUP BY AccountId
];

// A relationship subquery consumes one slot on EACH meter.
if (!LimitGuard.hasRoomFor('soql', 1)) {
    return;
}
List<Account> withKids = [SELECT Id, (SELECT Id FROM Contacts) FROM Account LIMIT 50];
```

**Detection hint:** an aggregate-query guard sitting above a query whose text contains `COUNT(`, `SUM(` or `GROUP BY` but no nested `(SELECT`. Conversely, nested-subquery code guarded only on `getQueries()` is missing the other meter.

---

## Anti-Pattern 7: Mocking `OrgLimits` in the Poller Test

**What the LLM generates:**

```apex
@IsTest
static void pollerWritesRows() {
    // Neither of these compiles or runs: OrgLimits is a System type with static methods.
    OrgLimits mock = (OrgLimits) Test.createStub(OrgLimits.class, new OrgLimitsStub());
    Test.setMock(HttpCalloutMock.class, new OrgLimitsMock());
    OrgLimitsPoller.run();
}
```

**Why it happens:** every other external dependency in Apex has a mocking story — `Test.setMock` for callouts, `Test.createStub` for classes — so the model reaches for one. The Stub API limitation list rules out both static methods and System types (`apexdev L42205–42211`), and `OrgLimits.getAll()` is both. `Test.setMock` is for HTTP and web-service callouts; `OrgLimits` is neither.

**Correct pattern:**

```apex
@IsTest
static void pollerClassifiesInjectedReadings() {
    OrgLimitsPoller.injectedReadings = new List<OrgLimitsPoller.Reading>{
        new OrgLimitsPoller.Reading('DailyApiRequests', 9500, 10000)
    };
    Test.startTest();
    List<Limit_Snapshot__c> rows = OrgLimitsPoller.run();
    Test.stopTest();
    Assert.areEqual('CRITICAL', rows[0].Severity__c, '95% is past the critical threshold');
}
```

**Detection hint:** `Test.createStub` or `Test.setMock` in a test whose subject reads `OrgLimits`, `Limits`, `UserInfo` or `System.Request`. The fix is a `@TestVisible` seam with a plain DTO, not a mocking framework.

---

## Anti-Pattern 8: A Guard Test That Asserts Without Consuming Anything

**What the LLM generates:**

```apex
@IsTest
static void testLimitGuard() {
    Test.startTest();
    Assert.isFalse(LimitGuard.nearSoql(80));   // true on an empty transaction, always
    Assert.isFalse(LimitGuard.nearCpu(80));
    Test.stopTest();
}
```

**Why it happens:** the assertions are syntactically about the guard, they pass, and coverage goes up. What they actually assert is that zero is less than eighty. The threshold logic, the `getLimitX()` lookup and the division are all unexercised, and a guard inverted to `<=` would still pass.

**Correct pattern:** consume measurable budget first, then assert the transition in both directions.

```apex
@IsTest
static void nearSoqlFlipsOnceTheCeilingIsApproached() {
    Test.startTest();
    Assert.isFalse(LimitGuard.nearSoql(50), 'no queries yet: ' + LimitGuard.snapshot());
    Integer target = (Integer) (Limits.getLimitQueries() * 0.55);
    for (Integer i = Limits.getQueries(); i < target; i++) {
        Integer ignored = [SELECT COUNT() FROM Organization LIMIT 1];
    }
    Assert.isTrue(LimitGuard.nearSoql(50), 'past 50%: ' + LimitGuard.snapshot());
    Assert.isFalse(LimitGuard.nearSoql(95), 'not yet past 95%: ' + LimitGuard.snapshot());
    Test.stopTest();
}
```

**Detection hint:** a test method asserting on a `nearX`/headroom call with no SOQL, DML or allocation between `Test.startTest()` and the assertion. The checker raises this as ADVISORY.

---

## Anti-Pattern 9: Treating `OrgLimits` Readings as a Real-Time Gate

**What the LLM generates:**

```apex
// "Don't run the integration if we're out of API calls"
System.OrgLimit api = OrgLimits.getMap().get('DailyApiRequests');
if (api.getValue() >= api.getLimit()) {
    throw new IntegrationException('Out of API calls');
}
makeCallout();
```

**Why it happens:** the reading looks like a live counter, so it looks like a valid precondition. Both org-limit surfaces are explicitly lagged: "Limit values are updated asynchronously, in near-real-time" (`apexrefguide L226215`), and the REST resource is "accurate within five minutes of resource consumption" (`api_rest L7792`). A burst of consumption in the last five minutes is invisible, so the gate passes exactly when it should not.

**Correct pattern:** use these readings for trend and alerting — snapshot them into `Limit_Snapshot__c` on a schedule and alert on slope and threshold crossings. Gate individual transactions on the per-transaction `Limits` methods, which are exact for the current transaction, or handle the failure the API itself returns. Also do not confuse the two surfaces' semantics: `OrgLimit.getValue()` is consumed, REST `Remaining` is what is left.

**Detection hint:** `OrgLimits.getAll()` or `getMap()` in a code path that throws, returns early, or branches on the result within a user-facing or integration transaction, rather than in a scheduled or batch monitoring class.
