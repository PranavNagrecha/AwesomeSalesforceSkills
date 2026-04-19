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

## Anti-Pattern: Casting Child Rows Without getSObjects()

**What practitioners do:**

```apex
// WRONG — attempting a direct cast of a relationship result
List<Contact> contacts = (List<Contact>) acc.Contacts;
```

**What goes wrong:** The relationship result is not a `List<Contact>`. Salesforce returns an `SObject[]` accessor, not a typed list. This cast throws a `System.TypeException` at runtime.

**Correct approach:**

```apex
// CORRECT — use getSObjects() and cast each row individually
List<SObject> rows = acc.getSObjects('Contacts');
if (rows != null) {
    for (SObject row : rows) {
        Contact c = (Contact) row;
    }
}
```
