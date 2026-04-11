# LLM Anti-Patterns — FSC Apex Extensions

Common mistakes AI coding assistants make when generating or advising on FSC Apex Extensions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting the try/finally Block When Disabling FSC Triggers

**What the LLM generates:** Code that disables a `FinServ__TriggerSettings__c` flag before a DML operation and re-enables it after, but with the re-enable statement in the main execution path rather than a `finally` block:

```apex
ts.FinServ__AccountTrigger__c = false;
upsert ts;
insert accounts;
ts.FinServ__AccountTrigger__c = true;  // WRONG: skipped if insert throws
upsert ts;
```

**Why it happens:** LLMs trained on general Apex patterns produce sequential disable/enable patterns by analogy with mutex-style locking in other languages. The `finally` block requirement is an FSC-specific discipline that is not prominent in generic Apex training data.

**Correct pattern:**

```apex
FinServ__TriggerSettings__c ts = FinServ__TriggerSettings__c.getInstance();
Boolean wasEnabled = ts.FinServ__AccountTrigger__c;
try {
    ts.FinServ__AccountTrigger__c = false;
    upsert ts;
    insert accounts;
} finally {
    if (wasEnabled) {
        ts.FinServ__AccountTrigger__c = true;
        upsert ts;
    }
}
```

**Detection hint:** Search generated code for `FinServ__TriggerSettings__c` writes that are not inside a `try` block. Any upsert of a `TriggerSettings__c` with a `false` value must have a corresponding `finally` block.

---

## Anti-Pattern 2: Inserting Share Records Directly on CDS-Governed Objects

**What the LLM generates:** Standard Apex sharing code using `insert` on `AccountShare` or `FinancialAccountShare`:

```apex
AccountShare share = new AccountShare(
    AccountId = financialAccountId,
    UserOrGroupId = advisorUserId,
    AccountAccessLevel = 'Read',
    OpportunityAccessLevel = 'None'
);
insert share;  // WRONG: CDS recalculation will delete this
```

**Why it happens:** LLMs have extensive training data on standard Apex sharing patterns. CDS is an FSC-specific override of the sharing model with limited public documentation, so LLMs default to the standard pattern they have seen most often.

**Correct pattern:**

```apex
FinServ__ShareParticipant__c participant = new FinServ__ShareParticipant__c(
    FinServ__FinancialAccount__c = financialAccountId,
    FinServ__User__c = advisorUserId,
    FinServ__ShareRole__c = advisorRoleId
);
insert participant;
// CDS engine generates and maintains the share record
```

**Detection hint:** Flag any `insert` DML on `AccountShare`, `FinancialAccountShare`, or similar share sObjects in an FSC org. These should be replaced with `FinServ__ShareParticipant__c` inserts if the org uses CDS.

---

## Anti-Pattern 3: Invoking RollupRecalculationBatchable with Default or High Batch Size

**What the LLM generates:** A `Database.executeBatch` call with either no explicit batch size (defaults to 200 per platform default for some batchables but is often generated as higher) or an explicitly high value:

```apex
// WRONG: no size specified, or too large
Database.executeBatch(new FinServ.RollupRecalculationBatchable());
Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 2000);
```

**Why it happens:** LLMs optimize for throughput in generic batch patterns and suggest high batch sizes to reduce job iterations. FSC rollup recalculation involves complex SOQL across household graphs per batch item; high batch sizes cause CPU limit violations that are not present in simpler batchables.

**Correct pattern:**

```apex
// Always use 200 or lower; 200 is the FSC Admin Guide-recommended size
Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200);
```

**Detection hint:** Any `executeBatch` call on `FinServ.RollupRecalculationBatchable` without an explicit batch size argument, or with a batch size above 200, should be flagged.

---

## Anti-Pattern 4: Skipping Rollup Recalculation After Bulk Data Loads

**What the LLM generates:** A data migration script or integration batch that inserts FinancialAccount records and marks the job complete without triggering rollup recalculation:

```apex
Database.executeBatch(new FinancialAccountMigrationBatch(), 2000);
// Migration done — WRONG: household totals are now stale
```

**Why it happens:** LLMs model bulk data loads as complete when the DML succeeds. The FSC rollup dependency is a post-DML side effect that is not implied by the data model itself, and it is absent from most generic Apex migration pattern training data.

**Correct pattern:**

```apex
// In the finish() method of the migration batch:
public void finish(Database.BatchableContext ctx) {
    Database.executeBatch(new FinServ.RollupRecalculationBatchable(), 200);
}
```

**Detection hint:** Any migration batch or integration batch that inserts or updates `FinServ__FinancialAccount__c`, `FinServ__FinancialAccountTransaction__c`, or `FinServ__FinancialGoal__c` records must have a `finish()` method that invokes `RollupRecalculationBatchable` or explicitly documents why recalculation is handled elsewhere.

---

## Anti-Pattern 5: Calling FSC Managed Package Methods with Newer Platform Types Without Version Checking

**What the LLM generates:** Code that passes a type introduced in a recent API version to an FSC managed class method, without checking whether the package's compiled API version supports that type:

```apex
// WRONG if FSC package was compiled before the type was introduced
FinServ.SomeManager.process(Schema.describeSObjects(new List<String>{'Account'})[0]);
```

**Why it happens:** LLMs do not track package-level API version constraints. They generate calls using current platform types without awareness that managed package classes are frozen at older API versions and cannot resolve types introduced after their compilation version.

**Correct pattern:**

```apex
// Before using a newer platform type with FSC managed code:
// 1. Check the FSC package API version: Setup > Installed Packages > FSC > View Components
// 2. Verify the type used was available in that API version
// 3. If uncertain, pass primitive types or API-stable types and let FSC code handle the resolution internally
// 4. Test in a full-copy sandbox matching production's package version — not a Developer Edition
```

**Detection hint:** Any code that calls a method on a class prefixed with `FinServ.` and passes non-primitive arguments should be reviewed for API version compatibility. Newly introduced `System`, `Schema`, or domain-specific types are the highest risk.

---

## Anti-Pattern 6: Not Setting FinServ__TriggerSettings__c in Test Classes

**What the LLM generates:** Test classes that test FSC trigger handler logic without explicitly inserting a `FinServ__TriggerSettings__c` record:

```apex
@IsTest
static void testBalanceChange() {
    FinServ__FinancialAccount__c fa = TestDataFactory.createFinancialAccount();
    fa.FinServ__Balance__c = 100000;
    update fa;
    // WRONG: TriggerSettings__c not set; handler may take wrong code path
    System.assert(/* assertion */);
}
```

**Why it happens:** LLMs follow common Apex test patterns that work for standard objects. Custom settings with trigger gating are an FSC-specific infrastructure requirement that training data does not consistently represent.

**Correct pattern:**

```apex
@TestSetup
static void setup() {
    insert new FinServ__TriggerSettings__c(
        SetupOwnerId = UserInfo.getOrganizationId(),
        FinServ__AccountTrigger__c = true,
        FinServ__FinancialAccountTrigger__c = true
    );
}

@IsTest
static void testBalanceChange() {
    FinServ__FinancialAccount__c fa = TestDataFactory.createFinancialAccount();
    fa.FinServ__Balance__c = 100000;
    update fa;
    System.assert(/* assertion with correct trigger behavior */);
}
```

**Detection hint:** Any test class that exercises `FinServ__FinancialAccount__c` or `FinServ__AccountContactRelation__c` trigger handlers should have a `@TestSetup` method that inserts a `FinServ__TriggerSettings__c` record.
