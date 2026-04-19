# LLM Anti-Patterns — Apex Batch Chaining

Common mistakes AI coding assistants make when generating or advising on Apex Batch Chaining.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Chaining Without a Flex Queue Capacity Guard

**What the LLM generates:**

```apex
public void finish(Database.BatchableContext bc) {
    Database.executeBatch(new StepTwoBatch(), 200);
}
```

**Why it happens:** Training data is dominated by simple chaining examples that show the minimum viable `finish()` method. The Flex Queue saturation risk is not visible in most tutorial code, so the model does not learn to include the guard.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    Integer depth = [
        SELECT COUNT() FROM AsyncApexJob
        WHERE JobType = 'BatchApex'
        AND Status IN ('Holding','Queued','Processing','Preparing')
    ];
    if (depth >= 95) {
        // Log and alert — do not silently drop the chain
        System.debug(LoggingLevel.ERROR, 'Flex Queue near capacity. Chain aborted.');
        return;
    }
    Database.executeBatch(new StepTwoBatch(), 200);
}
```

**Detection hint:** Any `finish()` method that calls `Database.executeBatch` without a preceding `AsyncApexJob` COUNT query is missing the capacity guard.

---

## Anti-Pattern 2: Testing the Full Chain End-to-End in a Single Test Method

**What the LLM generates:**

```apex
@isTest
static void testFullChain() {
    Test.startTest();
    Database.executeBatch(new StepOneBatch(), 200);
    Test.stopTest();
    // Asserts on StepTwoBatch effects
    List<Account> updated = [SELECT Id, IsArchived__c FROM Account];
    System.assertEquals(true, updated[0].IsArchived__c); // from StepTwoBatch
}
```

**Why it happens:** LLMs generalize from single-batch test patterns where `Test.stopTest()` synchronously drives execution. They apply the same pattern to chains without knowing that `stopTest()` only flushes one level.

**Correct pattern:**

Test each batch class in isolation. For `finish()` chain verification, use a test flag or assert on a staging record written by `finish()`:

```apex
@isTest
static void testStepOneChainsToStepTwo() {
    insert new Account(Name = 'Test');
    Test.startTest();
    Database.executeBatch(new StepOneBatch(), 200);
    Test.stopTest();
    // Only StepOneBatch ran synchronously. Assert StepOne effects only.
    // Assert that finish() enqueued StepTwo by checking a side-effect
    // (e.g., a flag record, or a mock capture).
    List<AsyncApexJob> jobs = [
        SELECT Id, Status FROM AsyncApexJob WHERE ApexClass.Name = 'StepTwoBatch'
    ];
    System.assertNotEquals(0, jobs.size(), 'StepTwoBatch should have been enqueued');
}
```

**Detection hint:** Any test method that asserts on the data effects of a batch class that is NOT the first class enqueued in `Test.startTest()` will silently produce a false-green test.

---

## Anti-Pattern 3: Using System.scheduleBatch() for Immediate Next-Step Chaining

**What the LLM generates:**

```apex
public void finish(Database.BatchableContext bc) {
    System.scheduleBatch(new StepTwoBatch(), 'Step Two', 1); // 1-minute delay
}
```

**Why it happens:** `System.scheduleBatch` is surfaced in the same documentation section as batch chaining. LLMs see it as an alternative and sometimes prefer it because the method signature explicitly labels the delay, which appears to make the code more readable.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    // Database.executeBatch enqueues immediately to the Flex Queue
    Database.executeBatch(new StepTwoBatch(), 200);
}
```

**Detection hint:** Any `finish()` method that calls `System.scheduleBatch` instead of `Database.executeBatch` is introducing an unnecessary delay and an extra CronTrigger entry.

---

## Anti-Pattern 4: Assuming Database.Stateful State Is Available in the Next Chained Job

**What the LLM generates:**

```apex
global class StepOneBatch implements Database.Batchable<SObject>, Database.Stateful {
    global List<Id> processedIds = new List<Id>();

    global void execute(Database.BatchableContext bc, List<SObject> scope) {
        for (SObject s : scope) processedIds.add(s.Id);
    }

    global void finish(Database.BatchableContext bc) {
        // WRONG assumption: StepTwoBatch will somehow see processedIds
        Database.executeBatch(new StepTwoBatch(), 200);
    }
}
```

**Why it happens:** `Database.Stateful` is introduced alongside batch chaining in the documentation, and LLMs conflate the two features. They assume `Stateful` provides cross-job persistence.

**Correct pattern:**

```apex
global void finish(Database.BatchableContext bc) {
    // Pass accumulated state explicitly via constructor
    Database.executeBatch(new StepTwoBatch(this.processedIds), 200);
}
```

**Detection hint:** Any chained batch class that implements `Database.Stateful` and does NOT pass its accumulated fields through the chained job's constructor is likely relying on an incorrect state-sharing assumption.

---

## Anti-Pattern 5: Recursive Self-Chaining Without a Terminal Condition

**What the LLM generates:**

```apex
public void finish(Database.BatchableContext bc) {
    // Re-enqueue self to process remaining records
    Database.executeBatch(new SelfChainingBatch(), 200);
}
```

**Why it happens:** LLMs model this pattern from "process all records" use cases and assume the batch's own query will return 0 records when done. They do not account for cases where the query always returns results (e.g., a formula field that is always true, or a status field that the batch itself does not update).

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    // Only re-enqueue if there are more records to process
    Integer remaining = [SELECT COUNT() FROM MyObject__c WHERE Status__c = 'Pending'];
    if (remaining > 0) {
        Database.executeBatch(new SelfChainingBatch(), 200);
    }
    // Otherwise the chain terminates naturally
}
```

**Detection hint:** Any `finish()` that calls `Database.executeBatch(new [SameClassName]())` without a preceding count check or explicit exit condition is a potential infinite chain.

---

## Anti-Pattern 6: Ignoring AsyncApexJob Status Before Chaining

**What the LLM generates:**

Code that immediately chains in `finish()` without checking whether the completed job had errors:

```apex
public void finish(Database.BatchableContext bc) {
    Database.executeBatch(new StepTwoBatch(), 200); // proceeds even if StepOne had errors
}
```

**Why it happens:** LLMs follow the happy path. The `Database.BatchableContext` object provides a `getJobId()` method that can be used to query `AsyncApexJob.NumberOfErrors`, but this pattern rarely appears in tutorial code.

**Correct pattern:**

```apex
public void finish(Database.BatchableContext bc) {
    AsyncApexJob job = [
        SELECT NumberOfErrors, ExtendedStatus
        FROM AsyncApexJob WHERE Id = :bc.getJobId()
    ];
    if (job.NumberOfErrors > 0) {
        // Log and halt the chain — do not proceed with dirty data
        insert new Error_Log__c(
            Message__c = 'StepOneBatch finished with errors: ' + job.ExtendedStatus,
            Severity__c = 'ERROR'
        );
        return;
    }
    Database.executeBatch(new StepTwoBatch(), 200);
}
```

**Detection hint:** Any `finish()` that calls `Database.executeBatch` without first querying `AsyncApexJob.NumberOfErrors` for the current job is proceeding blindly into the next step despite possible upstream failures.
