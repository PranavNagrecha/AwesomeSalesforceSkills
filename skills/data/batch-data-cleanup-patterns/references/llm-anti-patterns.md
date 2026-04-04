# LLM Anti-Patterns — Batch Data Cleanup Patterns

Common mistakes AI coding assistants make when generating or advising on batch data cleanup in Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Deleting Records Directly in an Apex Trigger Instead of a Batch Job

**What the LLM generates:** An `after insert` or `after update` trigger that queries and deletes aged records inline, e.g., `delete [SELECT Id FROM Log__c WHERE CreatedDate < LAST_N_DAYS:30]` inside the trigger body.

**Why it happens:** LLMs associate "automatic deletion when something happens" with triggers, and the trigger pattern is heavily represented in training data. The governor limit implications of bulk DML inside triggers are often missed.

**Correct pattern:**

```apex
// Triggers must NOT perform bulk deletion inline.
// Instead, publish a Platform Event or set a flag, then handle deletion in a Scheduled Batch.
public class NightlyLogCleanupBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id FROM Log__c WHERE CreatedDate < LAST_N_DAYS:30');
    }
    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        Database.delete(scope, false);
    }
    public void finish(Database.BatchableContext bc) {}
}
```

**Detection hint:** Look for `delete [SELECT` inside a `trigger` block. Any delete SOQL inside a trigger body for bulk records is a red flag.

---

## Anti-Pattern 2: Ignoring Recycle Bin Storage Impact After Delete

**What the LLM generates:** A batch that calls `delete scope;` in `execute()` and considers the job complete, with no mention of `Database.emptyRecycleBin()` or hard delete. The LLM may state "records are now deleted" without qualifying that they remain in the Recycle Bin.

**Why it happens:** LLMs treat `delete` as semantically equivalent to permanent removal. The distinction between soft delete (Recycle Bin) and hard delete is a Salesforce-specific platform nuance not present in general programming training data.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    // Must empty recycle bin to actually reclaim storage
    if (!deletedIds.isEmpty()) {
        List<SObject> stubs = new List<SObject>();
        for (Id rid : deletedIds) { stubs.add(new Log__c(Id = rid)); }
        Database.emptyRecycleBin(stubs);
    }
}
```

**Detection hint:** Search for `Database.delete` or `delete scope` in a batch `execute()` method without any corresponding `emptyRecycleBin` or HARD_DELETE mention anywhere in the class or job spec.

---

## Anti-Pattern 3: Using `@isTest(SeeAllData=true)` in Deletion Batch Tests

**What the LLM generates:** A test class annotated with `@isTest(SeeAllData=true)` that runs the deletion batch and asserts that records were deleted — without inserting test records explicitly.

**Why it happens:** LLMs sometimes suggest `SeeAllData=true` to avoid complex test data setup, especially for objects with many required fields. This is flagged less often in general code review training because its danger is specific to deletion tests.

**Correct pattern:**

```apex
@isTest
private class DebugLogCleanupBatchTest {
    @TestSetup
    static void makeData() {
        // Insert records explicitly — never rely on SeeAllData=true for deletion tests
        List<Log__c> logs = new List<Log__c>();
        for (Integer i = 0; i < 10; i++) {
            logs.add(new Log__c(Name = 'Test Log ' + i));
        }
        insert logs;
    }

    @isTest
    static void testBatchDeletesExpiredRecords() {
        Test.startTest();
        Database.executeBatch(new DebugLogCleanupBatch(), 200);
        Test.stopTest();
        System.assertEquals(0, [SELECT COUNT() FROM Log__c]);
    }
}
```

**Detection hint:** Look for `@isTest(SeeAllData=true)` on any test class that exercises a class containing `delete`, `Database.delete`, or `Database.emptyRecycleBin`.

---

## Anti-Pattern 4: Not Handling Partial Delete Failures (`allOrNone=true` Default)

**What the LLM generates:** `delete scope;` in the `execute()` method with no `Database.DeleteResult[]` capture, or `Database.delete(scope, true)` (allOrNone=true). The LLM assumes all records can always be deleted.

**Why it happens:** The bare `delete` statement in Apex defaults to allOrNone=true behavior, meaning one undeletable record (e.g., locked by a trigger, sharing rule, or in-progress workflow) aborts the entire chunk. LLMs model the happy path and omit failure handling.

**Correct pattern:**

```apex
public void execute(Database.BatchableContext bc, List<SObject> scope) {
    // allOrNone=false: one failure does not abort the whole chunk
    Database.DeleteResult[] results = Database.delete(scope, false);
    for (Integer i = 0; i < results.size(); i++) {
        if (!results[i].isSuccess()) {
            // Log failure: results[i].getErrors()[0].getMessage()
            failureCount++;
        }
    }
}
```

**Detection hint:** Any `execute()` method that contains `delete scope;` (bare, without `Database.delete`) or `Database.delete(scope, true)` in a cleanup batch should be flagged for partial-failure risk.

---

## Anti-Pattern 5: Overlooking Cascade Deletion Volume When Setting Batch Size

**What the LLM generates:** A batch with `Database.executeBatch(new MyBatch(), 200)` deleting parent records without any comment on or verification of child record volumes. The LLM may not mention master-detail cascade at all.

**Why it happens:** LLMs generate a default batch size of 200 because it appears in most Salesforce Apex examples. The cascade multiplication effect is a data-model-specific concern that requires knowledge of the org's relationship structure — information not available to the LLM unless provided.

**Correct pattern:**

```apex
// Before setting batch size, estimate cascade volume:
// SELECT COUNT() FROM Child_Object__c WHERE Parent__c IN (select Id from Parent__c WHERE CreatedDate < LAST_N_YEARS:7)
// If avg children per parent = 50, set batch size to floor(10000/50) = 200 (check: 200*50=10000 — at the limit)
// Safer: set to 100 to stay below DML row limit
Database.executeBatch(new ParentCleanupBatch(), 100);
```

**Detection hint:** Any batch cleanup targeting a parent object in a master-detail relationship with a batch size of 200 (the unreflective default) without any comment documenting that cascade volume was checked is a candidate for review.
