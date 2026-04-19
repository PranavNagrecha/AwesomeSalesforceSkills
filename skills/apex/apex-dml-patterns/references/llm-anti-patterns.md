# LLM Anti-Patterns — Apex DML Patterns

Common mistakes AI coding assistants make when generating or advising on Apex DML patterns.

## Anti-Pattern 1: DML inside a loop

**What the LLM generates:**
```apex
for (Contact c : contacts) {
    c.Status__c = 'Active';
    update c; // DML in loop
}
```

**Why it happens:** LLMs trained on general programming patterns default to per-record processing. The Salesforce bulkification requirement is platform-specific and often forgotten in favor of "simpler" loop-per-record code.

**Correct pattern:**
```apex
for (Contact c : contacts) {
    c.Status__c = 'Active';
}
update contacts; // single bulk DML outside loop
```

**Detection hint:** Search for `insert`/`update`/`delete`/`upsert` inside `for` or `while` loops. Any DML statement inside a loop body is almost always wrong.

---

## Anti-Pattern 2: Ignoring SaveResult errors in partial success mode

**What the LLM generates:**
```apex
List<Database.SaveResult> results = Database.insert(records, false);
// No check on results
```

**Why it happens:** LLMs generate the `Database.insert` call with `allOrNone=false` correctly but omit the per-row error inspection loop — treating partial success mode as a "silent ignore all errors" flag.

**Correct pattern:**
```apex
List<Database.SaveResult> results = Database.insert(records, false);
for (Integer i = 0; i < results.size(); i++) {
    if (!results[i].isSuccess()) {
        for (Database.Error err : results[i].getErrors()) {
            System.debug('Row ' + i + ' failed: ' + err.getMessage());
        }
    }
}
```

**Detection hint:** `Database.insert(list, false)` followed immediately by non-result code (no loop checking `isSuccess()`).

---

## Anti-Pattern 3: Confusing DML row count with DML operation count

**What the LLM generates:**
```apex
// Comment: "split into batches of 150 to avoid DML limit"
List<List<Account>> batches = splitIntoChunks(accounts, 150);
for (List<Account> batch : batches) {
    insert batch; // still inside a loop!
}
```

**Why it happens:** LLMs conflate the 150 DML **operations** limit with a per-record limit, causing them to generate chunking logic that actually makes things worse by multiplying DML operations.

**Correct pattern:**
```apex
// One DML operation for all records, regardless of list size
insert accounts;
```

**Detection hint:** Code that chunks a list before calling DML "to avoid limits" when the list itself is not being split for async or heap reasons. One `insert(largeList)` = 1 DML operation.

---

## Anti-Pattern 4: Using Database.merge on non-mergeable objects

**What the LLM generates:**
```apex
// Attempting to merge duplicate Opportunities
Database.merge(masterOpp, duplicateOpp.Id);
```

**Why it happens:** LLMs generalize from the Account/Contact merge pattern to all SObjects without knowing the platform restriction. There is no compile-time error, so the mistake is invisible until runtime.

**Correct pattern:** `Database.merge` is supported only for Account, Contact, and Lead. For other objects, implement custom merge logic: copy related records to the master, then delete the duplicate.

**Detection hint:** `Database.merge(` called with a variable of any type other than Account, Contact, or Lead. Check the declared type of the first argument.

---

## Anti-Pattern 5: Not using DMLOptions for lead assignment rule firing

**What the LLM generates:**
```apex
insert leads; // assignment rule won't fire
```

**Why it happens:** LLMs default to the simpler DML statement form and don't know that assignment rules require explicit opt-in via `Database.DMLOptions` or the `assignmentRuleHeader` on `Database.insert`.

**Correct pattern:**
```apex
Database.DMLOptions opts = new Database.DMLOptions();
opts.assignmentRuleHeader.useDefaultRule = true;
Database.insert(leads, opts);
```

**Detection hint:** Code inserting Leads or Cases that is expected to fire assignment rules, using plain `insert leads` without `Database.DMLOptions`. Confirm with the spec whether assignment rule firing is required.
