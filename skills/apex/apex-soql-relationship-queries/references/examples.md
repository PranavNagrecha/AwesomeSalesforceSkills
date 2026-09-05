# Examples — SOQL Relationship Queries

## Example 1: Account with Related Contacts — Parent-to-Child Subquery

**Context:** A trigger or service class needs to process every Contact under a set of Accounts in a single SOQL call, without issuing a query per Account.

**Problem:** Querying inside a loop issues one SOQL call per Account, exhausting the 100-query governor limit quickly in any bulk scenario.

**Solution:**

```apex
// Collect Account IDs from the trigger or calling context
Set<Id> accountIds = new Map<Id, Account>(Trigger.new).keySet();

// Single query — parent-to-child subquery using standard relationship name 'Contacts'
List<Account> accounts = [
    SELECT Id,
           Name,
           BillingCity,
           (SELECT Id, FirstName, LastName, Email, Title
            FROM Contacts
            WHERE IsEmailBounced = false
            ORDER BY LastName ASC
            LIMIT 200)
    FROM Account
    WHERE Id IN :accountIds
];

for (Account acc : accounts) {
    // getSObjects() returns null when the Account has no Contacts — guard is mandatory
    List<SObject> childRows = acc.getSObjects('Contacts');
    if (childRows == null) {
        continue;
    }
    for (SObject row : childRows) {
        Contact c = (Contact) row;
        System.debug('Processing ' + c.LastName + ' at ' + acc.Name);
        // ... business logic here
    }
}
```

**Why it works:** The subquery uses the standard child relationship name `Contacts` (not `Contact` — singular is wrong). The `getSObjects('Contacts')` call returns the pre-fetched child list with zero additional SOQL queries. The null guard prevents a `NullPointerException` when an Account has no matching Contacts.

---

## Example 2: Task with Polymorphic WhatId Using TYPEOF

**Context:** A reporting utility needs to show what record each Task is related to, which could be an Account, Opportunity, or Case depending on the business context.

**Problem:** `Task.WhatId` is a polymorphic field — it can reference any of several object types. Dot notation like `WhatId.Name` is not valid SOQL syntax. Without `TYPEOF`, you cannot selectively retrieve type-specific fields.

**Solution:**

```soql
-- SOQL string (works identically inline in Apex or via Database.query())
SELECT Id,
       Subject,
       ActivityDate,
       Status,
       TYPEOF WhatId
           WHEN Account     THEN Name, Phone
           WHEN Opportunity THEN Name, StageName, CloseDate
           WHEN Case        THEN Subject, Status
           ELSE Id
       END
FROM Task
WHERE OwnerId = :UserInfo.getUserId()
  AND ActivityDate = TODAY
```

```apex
List<Task> tasks = [
    SELECT Id, Subject, ActivityDate, Status,
           TYPEOF WhatId
               WHEN Account     THEN Name, Phone
               WHEN Opportunity THEN Name, StageName, CloseDate
               WHEN Case        THEN Subject, Status
               ELSE Id
           END
    FROM Task
    WHERE OwnerId = :UserInfo.getUserId()
      AND ActivityDate = TODAY
];

for (Task t : tasks) {
    if (t.WhatId == null) continue;

    // getSObjectType() on the polymorphic field value reveals the concrete type
    Schema.SObjectType whatType = t.WhatId.getSObjectType();

    if (whatType == Account.getSObjectType()) {
        Account relatedAcc = (Account) t.What;
        System.debug('Task linked to Account: ' + relatedAcc.Name);

    } else if (whatType == Opportunity.getSObjectType()) {
        Opportunity relatedOpp = (Opportunity) t.What;
        System.debug('Task linked to Opp: ' + relatedOpp.Name + ' / ' + relatedOpp.StageName);

    } else if (whatType == Case.getSObjectType()) {
        Case relatedCase = (Case) t.What;
        System.debug('Task linked to Case: ' + relatedCase.Subject);
    }
}
```

**Why it works:** `TYPEOF` is the only valid syntax for querying fields on a polymorphic relationship. The `ELSE Id` branch ensures the query does not fail when the WhatId points to an object type not listed in the `WHEN` clauses. In Apex, `t.What` exposes the related record as a generic `SObject` that can be cast after checking `getSObjectType()`.

---

## Example 3: Child-to-Parent Dot Notation — Contact to Account to Owner

**Context:** A list view controller or report export needs the Contact's name, Account name, Account owner email, and Account billing city in one query.

**Problem:** Issuing separate queries for Account and User data per Contact is not scalable.

**Solution:**

```apex
List<Contact> contacts = [
    SELECT Id,
           FirstName,
           LastName,
           Email,
           Account.Name,
           Account.BillingCity,
           Account.Owner.Email,     -- two hops: Account -> Owner
           Account.Owner.FullPhotoUrl
    FROM Contact
    WHERE Account.Type = 'Customer'
      AND Account.Owner.IsActive = true
    ORDER BY Account.Name, LastName
    LIMIT 1000
];

for (Contact c : contacts) {
    String line = c.LastName + ', '
        + c.Account?.Name + ' ('
        + c.Account?.BillingCity + ') — owner: '
        + c.Account?.Owner?.Email;
    System.debug(line);
}
```

**Why it works:** Each dot step (`Account.Owner`) traverses one relationship level. This query uses two levels, well within the five-level maximum. The `WHERE Account.Owner.IsActive = true` clause also uses dot notation — standard cross-object filters are allowed; only cross-object formula fields are not.

---

## Example 4: The 200-Child Boundary — Same Query, Two Loop Shapes

**Context:** A nightly job summarises Contacts per Account. It works in every sandbox and throws in
production on a handful of large Accounts.

**Problem:** The query is identical in both versions below. What differs is the *loop*: a SOQL for
loop chunks results through `queryMore` to save heap, and inside that construct a child set of 200 or
more cannot be assigned or sized. The Apex guide states it and shows both forms
(`apexdev L10078–10098`).

**Solution — the failing shape, then the fix:**

```apex
// WRONG — throws System.QueryException: Aggregate query has too many rows for
// direct assignment, use FOR loop, on any Account with 200+ Contacts.
for (Account acct : [SELECT Id, Name, (SELECT Id, Email FROM Contacts) FROM Account]) {
    List<Contact> contactList = acct.Contacts;   // apexdev L10087: "Causes an error"
    Integer count = acct.Contacts.size();        // apexdev L10088: "Causes an error"
    summary.put(acct.Id, count);
}

// RIGHT — iterate the children instead of materialising or sizing the set.
for (Account acct : [SELECT Id, Name, (SELECT Id, Email FROM Contacts) FROM Account]) {
    Integer count = 0;
    for (Contact c : acct.Contacts) {            // apexdev L10095-L10098
        if (String.isNotBlank(c.Email)) { count++; }
    }
    summary.put(acct.Id, count);
}

// ALSO RIGHT, and cheaper when only the count is wanted — no child rows on the heap at all.
for (AggregateResult ar : [
    SELECT AccountId aid, COUNT(Id) c FROM Contact WHERE Email != null GROUP BY AccountId
]) {
    summary.put((Id) ar.get('aid'), (Integer) ar.get('c'));
}
```

**Why it works:** The nested `for` never holds the whole child set at once, which is exactly the
condition the exception exists to enforce. The aggregate variant sidesteps the relationship entirely —
see `apex/apex-aggregate-queries`. One more trap in the same guide section: `JSON.serialize()` on
`acct` inside a SOQL for loop will not carry the complete child set, because the loop keeps "only a
subset of the record data in memory" (`apexdev L10108–10110`), so a serialised payload built this way
is quietly incomplete rather than wrong-looking.

---

## Anti-Pattern: Assuming Only One Child Accessor Exists

**What practitioners do:** commit to one accessor everywhere, in either direction.

```apex
// Version A — getSObjects() on a query that already returned a concrete type.
// Works, but trades compile-time safety for a string literal and a cast per row.
List<SObject> rows = acc.getSObjects('Contacts');

// Version B — typed access on a Database.query() result. Does not compile.
SObject parent = Database.query(dynamicSoql)[0];
for (Contact c : parent.Contacts) { }   // 'Contacts' is not a member of SObject
```

**What goes wrong:** Version A survives review and then breaks on a relationship rename, because the
compiler never saw the name. Version B fails at compile time, which is the harmless failure — but the
developer who hits it often "fixes" it by abandoning dynamic SOQL rather than by reaching for
`getSObjects()`.

**Correct approach:** pick by what the query returns, not by habit.

```apex
// Concrete type -> typed access (the guide's own pattern, apexdev L20254)
for (Account acc : accounts) {
    if (acc.Contacts == null || acc.Contacts.isEmpty()) { continue; }
    for (Contact c : acc.Contacts) { /* ... */ }
}

// Generic SObject -> getSObjects(), "primarily used with dynamic DML"
// (apexrefguide L233176-L233178), guarded as the guide guards it (apexdev L11719-L11721)
for (SObject parent : Database.query(dynamicSoql)) {
    SObject[] children = parent.getSObjects(relationshipName);
    if (children == null) { continue; }
    for (SObject child : children) { /* ... */ }
}
```
