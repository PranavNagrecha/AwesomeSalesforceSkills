# LLM Anti-Patterns — Governor Limits

Common mistakes AI coding assistants make when generating or advising on Apex governor limit compliance.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: SOQL query inside a for loop

**What the LLM generates:**

```apex
for (Contact c : Trigger.new) {
    Account a = [SELECT Id, Name FROM Account WHERE Id = :c.AccountId];
    c.Description = a.Name;
}
```

**Why it happens:** LLMs generate single-record-at-a-time logic because it reads naturally. With 200 records in a trigger batch, this executes 200 SOQL queries — hitting the 100 SOQL query limit on the first batch.

**Correct pattern:**

```apex
Set<Id> accountIds = new Set<Id>();
for (Contact c : Trigger.new) {
    accountIds.add(c.AccountId);
}
Map<Id, Account> accountMap = new Map<Id, Account>(
    [SELECT Id, Name FROM Account WHERE Id IN :accountIds]
);
for (Contact c : Trigger.new) {
    Account a = accountMap.get(c.AccountId);
    if (a != null) {
        c.Description = a.Name;
    }
}
```

**Detection hint:** `\[SELECT.*\]` inside a `for` or `while` loop body.

---

## Anti-Pattern 2: DML statement inside a loop

**What the LLM generates:**

```apex
for (Account a : accounts) {
    a.Status__c = 'Processed';
    update a; // 150 DML statement limit
}
```

**Why it happens:** LLMs generate per-record DML because it mirrors procedural programming patterns. With more than 150 records, this hits the DML statement limit.

**Correct pattern:**

```apex
for (Account a : accounts) {
    a.Status__c = 'Processed';
}
update accounts; // Single DML for all records
```

**Detection hint:** `update ` or `insert ` or `delete ` inside a `for` or `while` loop.

---

## Anti-Pattern 3: Querying all fields with SELECT * equivalent

**What the LLM generates:**

```apex
// LLM suggests querying many fields "just in case"
List<Account> accounts = [
    SELECT Id, Name, Description, Phone, Fax, Website, Industry,
    AnnualRevenue, NumberOfEmployees, BillingStreet, BillingCity,
    BillingState, BillingPostalCode, BillingCountry, ShippingStreet,
    ShippingCity, ShippingState, ShippingPostalCode, ShippingCountry,
    Type, Rating, Ownership, Sic, AccountSource, CreatedDate, LastModifiedDate
    FROM Account
];
```

**Why it happens:** LLMs over-select fields to avoid "field not queried" errors. But querying unnecessary fields increases heap consumption, row size, and can impact query selectivity. When combined with large result sets, this leads to heap size limit issues.

**Correct pattern:**

```apex
// Query only the fields you actually use in the method
List<Account> accounts = [SELECT Id, Name, Status__c FROM Account WHERE Type = 'Customer'];
```

**Detection hint:** SOQL queries with more than 10-15 fields where only 2-3 are used in subsequent code.

---

## Anti-Pattern 4: Not considering trigger batch size in limit calculations

**What the LLM generates:**

```apex
trigger OpportunityTrigger on Opportunity (before insert) {
    for (Opportunity opp : Trigger.new) {
        // Makes 2 SOQL queries per record
        Account a = [SELECT Id FROM Account WHERE Id = :opp.AccountId];
        List<OpportunityLineItem> items = [SELECT Id FROM OpportunityLineItem WHERE OpportunityId = :opp.Id];
    }
}
```

The LLM tests this with 1 record and it works. But `Trigger.new` can contain up to 200 records per batch in Data Loader scenarios, causing 400 SOQL queries.

**Why it happens:** LLMs test with single records. Real bulk operations via Data Loader, integrations, or batch processes fire triggers with up to 200 records per chunk.

**Correct pattern:**

```apex
trigger OpportunityTrigger on Opportunity (before insert) {
    Set<Id> accountIds = new Set<Id>();
    for (Opportunity opp : Trigger.new) {
        accountIds.add(opp.AccountId);
    }
    Map<Id, Account> accountMap = new Map<Id, Account>(
        [SELECT Id, Name FROM Account WHERE Id IN :accountIds]
    );
    // Process using the pre-loaded map
}
```

**Detection hint:** Multiple SOQL queries inside trigger handler loops — multiply by 200 to assess real limit consumption.

---

## Anti-Pattern 5: Assuming async Apex has unlimited governor limits

**What the LLM generates:**

```apex
@future
public static void processAllData() {
    // "It's async, so limits don't matter"
    List<Account> allAccounts = [SELECT Id FROM Account]; // 50K row limit still applies
    for (Account a : allAccounts) {
        a.Status__c = 'Sync';
    }
    update allAccounts; // 10K DML row limit still applies
}
```

**Why it happens:** LLMs know async has "higher limits" and sometimes present it as unlimited. `@future` and Queueable have the same SOQL row limit (50K) and DML row limit (10K) as synchronous. Only Batch `start()` with `Database.getQueryLocator` gets 50M rows, and each `execute()` scope gets fresh limits.

**Correct pattern:**

```apex
// Use Batch Apex for truly large datasets
public class AccountSyncBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id FROM Account');
    }
    public void execute(Database.BatchableContext bc, List<Account> scope) {
        for (Account a : scope) { a.Status__c = 'Sync'; }
        update scope; // Fresh limits per scope
    }
    public void finish(Database.BatchableContext bc) {}
}
```

**Detection hint:** `@future` or `Queueable` methods with unbounded SOQL queries (no `WHERE` filter or `LIMIT`).

---

## Anti-Pattern 6: Using Limits class checks as a substitute for proper bulkification

**What the LLM generates:**

```apex
for (Account a : accounts) {
    if (Limits.getQueries() < Limits.getLimitQueries()) {
        Account detail = [SELECT Id, Owner.Name FROM Account WHERE Id = :a.Id];
        // process
    } else {
        break; // Silently stop processing remaining records
    }
}
```

**Why it happens:** LLMs use `Limits.getQueries()` as a safety valve instead of bulkifying the query. This creates non-deterministic behavior — how many records get processed depends on how many SOQL queries were already consumed earlier in the transaction. Remaining records are silently dropped.

**Correct pattern:**

```apex
// Bulkify the query — no need to check limits per record
Map<Id, Account> detailMap = new Map<Id, Account>(
    [SELECT Id, Owner.Name FROM Account WHERE Id IN :accountIds]
);
for (Account a : accounts) {
    Account detail = detailMap.get(a.Id);
    // process — every record gets handled
}
```

**Detection hint:** `Limits\.getQueries\(\)` or `Limits\.getDMLStatements\(\)` used as a conditional guard inside a loop to decide whether to execute SOQL or DML.
