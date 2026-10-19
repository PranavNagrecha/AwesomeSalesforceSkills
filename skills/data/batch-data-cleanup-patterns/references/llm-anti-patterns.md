# LLM Anti-Patterns — Batch Data Cleanup Patterns

Common mistakes AI coding assistants make when generating or advising on batch data cleanup in Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Deleting Records Directly in an Apex Trigger

**What the LLM generates:** An `after insert` trigger that runs `delete [SELECT Id FROM Log__c WHERE CreatedDate < LAST_N_DAYS:30]` on every save.

**Why it happens:** Models associate "automatically when something happens" with triggers.

**Correct pattern:** The delete runs in the caller's transaction and spends its DML-row budget (10,000 rows). Move it to a scheduled batch:

```apex
public with sharing class NightlyLogCleanupScheduler implements Schedulable {
    public void execute(SchedulableContext ctx) {
        Database.executeBatch(new RetentionPurgeBatch(30), 200);
    }
}
```

**Detection hint:** `delete [SELECT` or `Database.delete(` inside a `trigger` body or trigger handler.

---

## Anti-Pattern 2: Saying the Recycle Bin Holds Storage, or That Delete Is Permanent

**What the LLM generates:** Either "records in the Recycle Bin count against storage, so empty it to reclaim space," or "the records are now deleted" with no mention that they are restorable for 15 days.

**Why it happens:** Both are plausible from general database experience; neither matches the LDV guide.

**Correct pattern:** Recycle Bin items don't count against storage. They are restorable for 15 days and still have to be excluded from queries. Purge them (per chunk with `emptyRecycleBin`, or with Bulk API 2.0 `hardDelete`) when policy requires permanent deletion or when query performance suffers.

**Detection hint:** "empty the Recycle Bin" paired with "free storage," or a compliance purge that uses only `delete`.

---

## Anti-Pattern 3: Calling `emptyRecycleBin` Once in `finish()` With Every Id

**What the LLM generates:** A `Database.Stateful` batch that accumulates all deleted Ids and empties the bin in `finish()`.

**Why it happens:** It looks tidy, and the 10,000-record cap on the method is easy to miss.

**Correct pattern:**

```apex
public void execute(Database.BatchableContext bc, List<SObject> scope) {
    List<Database.DeleteResult> results = Database.delete(scope, false);
    List<Id> purge = new List<Id>();
    for (Integer i = 0; i < results.size(); i++) {
        if (results[i].isSuccess()) {
            purge.add(scope[i].Id);
        }
    }
    if (!purge.isEmpty()) {
        Database.emptyRecycleBin(purge); // at most one chunk of Ids per call
    }
}
```

**Detection hint:** `emptyRecycleBin` inside `finish()`, or a stateful `List<Id>` that grows across executes.

---

## Anti-Pattern 4: Using `LAST_N_YEARS:n` for "Older Than n Years"

**What the LLM generates:** `WHERE CreatedDate < LAST_N_YEARS:7` with a comment "records older than 7 years."

**Why it happens:** The literal reads like a rolling window.

**Correct pattern:** `LAST_N_YEARS:n` is calendar-year based and ends on December 31 of last year. For a rolling policy, bind a computed date:

```apex
Date cutoff = Date.today().addYears(-7);
List<Loan_Application__c> due = [SELECT Id FROM Loan_Application__c WHERE CreatedDate < :cutoff LIMIT 200];
```

**Detection hint:** `< LAST_N_YEARS:` in a retention query whose comment or policy says "older than."

---

## Anti-Pattern 5: Ignoring Partial Failures

**What the LLM generates:** `delete scope;` in `execute()`, or `Database.delete(scope, true)`.

**Why it happens:** Models write the happy path; bare `delete` is all-or-none, so one locked or protected record rolls back the chunk.

**Correct pattern:** `Database.delete(scope, false)`, count or log every failed `DeleteResult`, and report totals from `finish()`.

**Detection hint:** A cleanup batch with bare `delete scope;` or `allOrNone` set to true.

---

## Anti-Pattern 6: Claiming `SeeAllData=true` Tests Delete Real Data

**What the LLM generates:** "Never use SeeAllData=true in deletion tests or the test will delete real org data."

**Why it happens:** The warning sounds safe, but the reason is wrong: the Apex guide says database changes made in test methods are rolled back when execution completes.

**Correct pattern:** Avoid `SeeAllData=true` because the test then depends on whatever data the org has, so its assertions are not repeatable. Insert records on both sides of the cutoff in `@TestSetup`, and remember a batch test runs only one `execute`, so pass a scope that covers all test rows.

**Detection hint:** A test rationale that says test DML persists, or a batch test whose inserted rows exceed the scope passed to `executeBatch`.
