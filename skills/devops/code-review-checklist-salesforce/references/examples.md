# Examples — Code Review Checklist Salesforce

## Example 1: SOQL inside a trigger loop

**Context:** A pull request adds a `before update` trigger on `Opportunity` that loads the parent `Account` for each opportunity to stamp a field.

**Problem:** The author queries `Account` inside `for (Opportunity o : Trigger.new)`, which issues one SOQL per opportunity row. At 200 rows the transaction exceeds the synchronous SOQL limit.

**Solution:**

```apex
// Collect parent ids once, query once, map, then loop
Set<Id> accountIds = new Set<Id>();
for (Opportunity o : (List<Opportunity>) Trigger.new) {
    if (o.AccountId != null) {
        accountIds.add(o.AccountId);
    }
}
Map<Id, Account> accountsById = new Map<Id, Account>(
    [SELECT Id, Industry FROM Account WHERE Id IN :accountIds WITH USER_MODE]
);
for (Opportunity o : (List<Opportunity>) Trigger.new) {
    Account a = accountsById.get(o.AccountId);
    if (a != null) {
        o.Description = a.Industry;
    }
}
```

**Why it works:** SOQL count stays O(1) relative to batch size; `WITH USER_MODE` enforces readable fields for the running user.

---

## Example 2: Tests with no assertions

**Context:** A new service class ships with a test that only constructs the class and calls each public method once with minimal data.

**Problem:** Coverage passes the gate but behavior regressions (wrong default, swallowed exception) never fail the build.

**Solution:**

```apex
@IsTest
private class MyService_Test {
    @IsTest
    static void bulkUpdate_setsExpectedField() {
        List<Account> accs = new List<Account>();
        for (Integer i = 0; i < 200; i++) {
            accs.add(new Account(Name = 'T' + i));
        }
        insert accs;
        Test.startTest();
        MyService.applyDefaultIndustry(accs);
        Test.stopTest();
        List<Account> reloaded = [SELECT Industry FROM Account WHERE Id IN :accs];
        for (Account a : reloaded) {
            System.assertEquals('Technology', a.Industry, 'Industry default should apply for every row');
        }
    }
}
```

**Why it works:** The assertion encodes the contract; bulk size matches trigger reality.

---

## Anti-Pattern: Elevating SOQL without documenting why

**What practitioners do:** Use `without sharing` and `ACCESS_LEVEL.SYSTEM_MODE` everywhere for convenience.

**What goes wrong:** Subscribers or internal users see data their profile should block; security review and customer trust issues follow.

**Correct approach:** Default to user mode or inherited sharing; narrow elevated queries; document the threat model in the class header and in the PR.
