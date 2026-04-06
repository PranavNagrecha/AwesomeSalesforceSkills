# LLM Anti-Patterns — Apex Managed Sharing

Common mistakes AI coding assistants make when generating or advising on programmatic record sharing in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using RowCause 'Manual' instead of a custom Apex sharing reason

**What the LLM generates:**

```apex
CustomObj__Share share = new CustomObj__Share();
share.ParentId = recordId;
share.UserOrGroupId = userId;
share.AccessLevel = 'Edit';
share.RowCause = Schema.CustomObj__Share.RowCause.Manual;
insert share;
```

**Why it happens:** LLMs default to `Manual` because it is the most commonly shown row cause in examples. But `Manual` shares are deleted when record ownership changes, cannot be distinguished from user-created UI shares, and cannot be recalculated by a batch sharing recalculation class.

**Correct pattern:**

```apex
CustomObj__Share share = new CustomObj__Share();
share.ParentId = recordId;
share.UserOrGroupId = userId;
share.AccessLevel = 'Edit';
share.RowCause = Schema.CustomObj__Share.RowCause.Territory_Access__c; // Custom Apex sharing reason
insert share;
```

**Detection hint:** `RowCause\.Manual` or `RowCause = 'Manual'` in share record creation code for custom objects.

---

## Anti-Pattern 2: Inserting share records one at a time instead of in bulk

**What the LLM generates:**

```apex
for (Id userId : targetUserIds) {
    CustomObj__Share share = new CustomObj__Share();
    share.ParentId = recordId;
    share.UserOrGroupId = userId;
    share.AccessLevel = 'Read';
    share.RowCause = Schema.CustomObj__Share.RowCause.Custom_Reason__c;
    insert share; // DML in loop
}
```

**Why it happens:** LLMs generate share creation inside loops, treating each as an independent operation. With many users, this hits the 150 DML statement limit.

**Correct pattern:**

```apex
List<CustomObj__Share> shares = new List<CustomObj__Share>();
for (Id userId : targetUserIds) {
    shares.add(new CustomObj__Share(
        ParentId = recordId,
        UserOrGroupId = userId,
        AccessLevel = 'Read',
        RowCause = Schema.CustomObj__Share.RowCause.Custom_Reason__c
    ));
}
Database.insert(shares, false); // AllOrNone=false to handle duplicates gracefully
```

**Detection hint:** `insert` inside a `for` loop that iterates over user or group IDs for share records.

---

## Anti-Pattern 3: Attempting to share standard objects with a custom sharing reason

**What the LLM generates:**

```apex
AccountShare share = new AccountShare();
share.AccountId = accountId;
share.UserOrGroupId = userId;
share.AccountAccessLevel = 'Edit';
share.RowCause = 'Custom_Reason__c'; // Invalid for standard objects
insert share;
```

**Why it happens:** LLMs apply the custom-object sharing pattern to standard objects. Standard objects like Account, Case, and Opportunity do NOT support custom Apex sharing reasons — only `Manual` is available as a programmable row cause.

**Correct pattern:**

```apex
AccountShare share = new AccountShare();
share.AccountId = accountId;
share.UserOrGroupId = userId;
share.AccountAccessLevel = 'Edit';
share.OpportunityAccessLevel = 'None'; // Required companion field on AccountShare
share.RowCause = Schema.AccountShare.RowCause.Manual;
insert share;
```

**Detection hint:** Custom `RowCause` on `AccountShare`, `CaseShare`, `OpportunityShare`, or `LeadShare`.

---

## Anti-Pattern 4: Running sharing recalculation without 'without sharing' keyword

**What the LLM generates:**

```apex
public class SharingRecalcBatch implements Database.Batchable<SObject> {
    // Missing: without sharing
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id, OwnerId FROM CustomObj__c');
    }
}
```

**Why it happens:** LLMs often omit the sharing keyword. A sharing recalculation batch must see all records regardless of the running user's sharing rules — otherwise it silently skips records the user cannot see.

**Correct pattern:**

```apex
public without sharing class SharingRecalcBatch implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator('SELECT Id, OwnerId FROM CustomObj__c');
    }

    public void execute(Database.BatchableContext bc, List<CustomObj__c> scope) {
        List<CustomObj__Share> oldShares = [
            SELECT Id FROM CustomObj__Share
            WHERE ParentId IN :scope
            AND RowCause = :Schema.CustomObj__Share.RowCause.Territory_Access__c
        ];
        delete oldShares;
        List<CustomObj__Share> newShares = calculateShares(scope);
        Database.insert(newShares, false);
    }

    public void finish(Database.BatchableContext bc) {}
}
```

**Detection hint:** Batch class that creates or deletes `__Share` records but does not have `without sharing` in its class declaration.

---

## Anti-Pattern 5: Setting AccessLevel to 'All' (Full Access) via Apex

**What the LLM generates:**

```apex
share.AccessLevel = 'All'; // Attempt to grant Full Access
```

**Why it happens:** LLMs see `All` as a valid value in documentation. However, `All` (Full Access) cannot be granted programmatically via Apex managed sharing — only `Read` and `Edit` are valid. Inserting with `All` throws a DML exception.

**Correct pattern:**

```apex
// Only 'Read' and 'Edit' are valid for programmatic sharing
share.AccessLevel = 'Edit';
```

**Detection hint:** `AccessLevel\s*=\s*'All'` in any share record assignment.

---

## Anti-Pattern 6: Not deleting old shares before inserting new ones during recalculation

**What the LLM generates:**

```apex
public void execute(Database.BatchableContext bc, List<CustomObj__c> scope) {
    List<CustomObj__Share> newShares = calculateShares(scope);
    insert newShares; // Stale shares accumulate with each run
}
```

**Why it happens:** LLMs generate the "insert new shares" step but skip the "delete stale shares" step. Over multiple runs, duplicate or stale share records accumulate, granting access to users who should have lost it.

**Correct pattern:**

```apex
public void execute(Database.BatchableContext bc, List<CustomObj__c> scope) {
    Set<Id> scopeIds = new Map<Id, CustomObj__c>(scope).keySet();
    List<CustomObj__Share> staleShares = [
        SELECT Id FROM CustomObj__Share
        WHERE ParentId IN :scopeIds
        AND RowCause = :Schema.CustomObj__Share.RowCause.Territory_Access__c
    ];
    if (!staleShares.isEmpty()) {
        delete staleShares;
    }
    List<CustomObj__Share> newShares = calculateShares(scope);
    Database.insert(newShares, false);
}
```

**Detection hint:** Sharing recalculation `execute` method with `insert` for share records but no `delete` of existing shares with the same row cause.
