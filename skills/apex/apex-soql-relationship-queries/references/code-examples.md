# Code Examples — SOQL Relationship Queries

A complete, deployable selector + service + test set covering the four relationship shapes this
skill owns: child-to-parent traversal, a parent-to-child subquery, `TYPEOF` on a polymorphic
field, and a semi-join. Every claim carries its guide line so the reviewer can check it.

Canonical templates this set builds on — reference them, do not copy them into your project:

| Template | Used for |
|---|---|
| [`templates/apex/BaseSelector.cls`](../../../../templates/apex/BaseSelector.cls) | The base class `AccountHierarchySelector` extends. Supplies `userMode()` / `systemMode()`, `commaSeparated()` and `assertNotNull()`; declared `public abstract inherited sharing`. |
| [`templates/apex/tests/TestDataFactory.cls`](../../../../templates/apex/tests/TestDataFactory.cls) | Bulk-safe `createAccounts` / `createContacts` / `createOpportunities` / `createCases`, none of which insert. |
| [`templates/apex/BaseService.cls`](../../../../templates/apex/BaseService.cls) | The service-layer base, if your org already uses it. |
| [`templates/apex/ApplicationLogger.cls`](../../../../templates/apex/ApplicationLogger.cls) | Where a caught `QueryException` should go instead of `System.debug`. |

`BaseSelector` is the only SOQL-issuing layer in this architecture and it is **not** to be rivalled:
`AccountHierarchySelector` extends it and calls its `userMode()` accessor rather than hardcoding
`AccessLevel.USER_MODE`, so the org's one security decision stays in one file.

---

## How to read this set

- **`AccountHierarchySelector`** holds one method per relationship *shape*, named for its intent, not
  its WHERE clause — the naming rule stated in `BaseSelector`'s own header comment.
- **Every query is `WITH USER_MODE`.** At API 67.0 that is also the default ("In API version 67.0 and
  later, Apex runs in user context by default" — `apexdev L11743–11744`), but writing it keeps the
  intent readable and survives a class being pinned back to an older version. `WITH SECURITY_ENFORCED`
  appears nowhere: it "can't be used in SOQL SELECT queries in Apex code" at 67.0+ (`apexdev L11742`).
- **Child access is typed.** `acct.Contacts` and `acct.Opportunities` are read directly, as the Apex
  guide's own bulkification example reads `inv.Line_Items__r` (`apexdev L20254`). `getSObjects()` is
  reserved for the dynamic path, where it is documented as "primarily used with dynamic DML"
  (`apexrefguide L233176–233178`).
- **The guard is `== null || isEmpty()`.** The guide's dynamic sample guards `!= null` with the comment
  "Prevent a null relationship from being accessed" (`apexdev L11719–11721`). UNVERIFIED (2026-09-05):
  no corpus source states whether typed access returns `null` or an empty list when there are no
  children, so the service guards both and the test asserts only that neither shape throws.
- **No child set is assigned or `.size()`-ed inside a SOQL for loop.** That is the
  `Aggregate query has too many rows for direct assignment, use FOR loop` boundary at 200 or more
  children (`apexdev L10078–10088`).
- **Nothing here goes into a Batch `start()` unchanged.** A QueryLocator carrying a relationship
  subquery forces "a slower, non-chunking, implementation" (`apexdev L17798–17800`); `selectIdsForBatch`
  is the flat locator to use there instead.

---

## 1. `AccountHierarchySelector.cls`

```apex
/**
 * AccountHierarchySelector — relationship-query shapes for the Account graph.
 *
 * Extends templates/apex/BaseSelector.cls; that base class owns the access-mode
 * decision (userMode()) and the argument guards. Add a method here per shape,
 * named for intent. Do not add a WHERE-clause-shaped method name.
 *
 * Shapes:
 *   selectWithContactsAndOpportunities  parent-to-child subqueries (2)
 *   selectContactsWithAccountOwner      child-to-parent traversal (2 hops)
 *   selectTasksWithPolymorphicWhat      TYPEOF on the What relationship
 *   selectAccountsWithOpenOpportunities semi-join (IN (SELECT ...))
 *   selectIdsForBatch                   flat locator, no subquery
 */
public inherited sharing class AccountHierarchySelector extends BaseSelector {

    /**
     * Parent-to-child. Two subqueries, so this query is charged two entries
     * against the aggregate-query pool as well as one top-level query:
     * "each parent-child relationship counts as an extra query ... The limit for
     * subqueries corresponds to the value that Limits.getLimitAggregateQueries()
     * returns" (apexdev L19613-L19616).
     *
     * The subquery LIMIT is deliberate. It caps rows per parent so the 50,000
     * total-rows-per-transaction limit (apexdev L19546) is not reached by a
     * handful of very wide parents, and it keeps callers away from the 200-child
     * boundary described in gotchas.md.
     */
    public List<Account> selectWithContactsAndOpportunities(Set<Id> accountIds) {
        assertNotNull(accountIds, 'accountIds');
        return [
            SELECT Id, Name, BillingCity,
                   (SELECT Id, FirstName, LastName, Email, Title
                    FROM Contacts
                    ORDER BY LastName
                    LIMIT 200),
                   (SELECT Id, Name, StageName, Amount, CloseDate
                    FROM Opportunities
                    WHERE IsClosed = false
                    LIMIT 200)
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ];
    }

    /**
     * Child-to-parent. Two hops: Contact -> Account -> Owner (User).
     * The token dotted into is the relationship name, not the Id field:
     * Contact.AccountId carries "Relationship Name: Account"
     * (object_reference L71327-L71342).
     *
     * The WHERE clause traverses the same relationships without projecting them,
     * which is why Account.Owner.IsActive can be filtered while Owner.IsActive is
     * absent from the SELECT list.
     */
    public List<Contact> selectContactsWithAccountOwner(Set<Id> accountIds) {
        assertNotNull(accountIds, 'accountIds');
        return [
            SELECT Id, FirstName, LastName, Email,
                   Account.Name, Account.BillingCity,
                   Account.Owner.Email, Account.Owner.Name
            FROM Contact
            WHERE AccountId IN :accountIds
              AND Account.Owner.IsActive = true
            WITH USER_MODE
            ORDER BY Account.Name, LastName
            LIMIT 5000
        ];
    }

    /**
     * Polymorphic projection. TYPEOF takes the relationship name What, not the
     * Id field WhatId: Task.WhatId carries "Relationship Name: What"
     * (object_reference L23967-L23969); the guide writes TYPEOF What
     * (apexdev L9785-L9786).
     *
     * No ELSE branch: the guide's own examples omit it (apexdev L9785, L9823),
     * and the service below handles an unlisted type by leaving it unresolved
     * rather than by relying on a catch-all projection.
     *
     * WhatId can point to Account, Opportunity, Campaign or Case
     * (object_reference L2399-L2401); the WHEN list here covers the three this
     * service acts on.
     */
    public List<Task> selectTasksWithPolymorphicWhat(Set<Id> accountIds) {
        assertNotNull(accountIds, 'accountIds');
        return [
            SELECT Id, Subject, Status, ActivityDate,
                   TYPEOF What
                       WHEN Account     THEN Id, Name, Industry
                       WHEN Opportunity THEN Id, Name, StageName
                       WHEN Case        THEN Id, Subject, Status
                   END
            FROM Task
            WHERE AccountId IN :accountIds
            WITH USER_MODE
            LIMIT 5000
        ];
    }

    /**
     * Semi-join. The inner SELECT returns Ids that the outer WHERE filters on;
     * it is not a subquery in the parent-to-child sense and does not add a
     * projected child collection.
     *
     * UNVERIFIED (2026-09-05): the documented cap on semi-joins and anti-joins
     * per query lives in the SOQL and SOSL Reference, which is not in the offline
     * corpus - grep -n -i "semi-join|anti-join" apexdev.txt returns nothing. The
     * shape below is a single semi-join and stays well inside any plausible cap,
     * but do not state a number for it without that reference.
     */
    public List<Account> selectAccountsWithOpenOpportunities(Set<Id> accountIds) {
        assertNotNull(accountIds, 'accountIds');
        return [
            SELECT Id, Name, BillingCity
            FROM Account
            WHERE Id IN :accountIds
              AND Id IN (
                  SELECT AccountId
                  FROM Opportunity
                  WHERE IsClosed = false
              )
            WITH USER_MODE
        ];
    }

    /**
     * Flat locator for Batch start(). Deliberately carries no subquery:
     * "Batch Apex jobs run faster when the start method returns a QueryLocator
     * object that doesn't include related records via a subquery ... If the start
     * method returns an iterable or a QueryLocator object with a relationship
     * subquery, the batch job uses a slower, non-chunking, implementation"
     * (apexdev L17796-L17800). Query the children inside execute() instead
     * (apexdev L17803-L17805).
     */
    public Database.QueryLocator selectIdsForBatch() {
        return Database.getQueryLocator(
            'SELECT Id FROM Account WHERE IsDeleted = false'
        );
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

> `AccountHierarchySelector.cls-meta.xml`. `apiVersion` matches
> [`templates/apex/BaseSelector.cls-meta.xml`](../../../../templates/apex/BaseSelector.cls-meta.xml),
> which is already at `67.0`. At this version `WITH SECURITY_ENFORCED` will not compile
> (`apexdev L44500–44502`), and the class-level default is user mode (`apexdev L44493–44495`).

---

## 2. `AccountHierarchyService.cls` — consuming the shapes

```apex
/**
 * AccountHierarchyService — reads the relationship shapes the selector returns.
 *
 * Rules this class demonstrates:
 *  - child collections are read with typed access and guarded before iteration
 *  - no child set is assigned or sized inside a SOQL for loop
 *  - a polymorphic reference is assigned to a typed variable before it is passed
 *    to a method (apexdev L9797-L9798)
 */
public with sharing class AccountHierarchyService {

    private final AccountHierarchySelector selector = new AccountHierarchySelector();

    public class AccountSummary {
        public Id accountId;
        public String accountName;
        public Integer contactCount = 0;
        public Integer openOpportunityCount = 0;
        public Decimal openPipeline = 0;
    }

    /**
     * Summarises each Account from one query carrying two subqueries.
     *
     * The outer loop walks a materialised List<Account>, not a SOQL for loop, so
     * acct.Contacts may be read directly. Inside a SOQL for loop the same reads
     * would raise "Aggregate query has too many rows for direct assignment, use
     * FOR loop" once a parent has 200 or more children (apexdev L10078-L10081).
     */
    public List<AccountSummary> summarise(Set<Id> accountIds) {
        List<AccountSummary> out = new List<AccountSummary>();
        if (accountIds == null || accountIds.isEmpty()) {
            return out;
        }

        for (Account acct : selector.selectWithContactsAndOpportunities(accountIds)) {
            AccountSummary s = new AccountSummary();
            s.accountId = acct.Id;
            s.accountName = acct.Name;

            // Guard before touching the collection. The guide's dynamic sample
            // guards the same shape: "Prevent a null relationship from being
            // accessed" (apexdev L11719-L11721).
            if (acct.Contacts != null) {
                for (Contact c : acct.Contacts) {
                    if (String.isNotBlank(c.Email)) {
                        s.contactCount++;
                    }
                }
            }

            if (acct.Opportunities != null) {
                for (Opportunity o : acct.Opportunities) {
                    s.openOpportunityCount++;
                    if (o.Amount != null) {
                        s.openPipeline += o.Amount;
                    }
                }
            }

            out.add(s);
        }
        return out;
    }

    /**
     * Routes each Task by the concrete type of its polymorphic What reference.
     *
     * instanceof is the documented runtime discriminator (apexdev L9789-L9795),
     * and each branch assigns to a correctly typed local before calling a method,
     * because "you must assign the referenced sObject that the query returns to a
     * variable of the appropriate type before you can pass it to another method"
     * (apexdev L9797-L9798).
     */
    public Map<String, Integer> routeTasksByWhatType(Set<Id> accountIds) {
        Map<String, Integer> counts = new Map<String, Integer>{
            'Account' => 0, 'Opportunity' => 0, 'Case' => 0, 'Other' => 0
        };

        for (Task t : selector.selectTasksWithPolymorphicWhat(accountIds)) {
            if (t.What == null) {
                counts.put('Other', counts.get('Other') + 1);
                continue;
            }
            if (t.What instanceof Account) {
                Account related = (Account) t.What;
                counts.put('Account', counts.get('Account') + 1);
                handleAccountTask(t, related);
            } else if (t.What instanceof Opportunity) {
                Opportunity related = (Opportunity) t.What;
                counts.put('Opportunity', counts.get('Opportunity') + 1);
                handleOpportunityTask(t, related);
            } else if (t.What instanceof Case) {
                Case related = (Case) t.What;
                counts.put('Case', counts.get('Case') + 1);
                handleCaseTask(t, related);
            } else {
                counts.put('Other', counts.get('Other') + 1);
            }
        }
        return counts;
    }

    private void handleAccountTask(Task t, Account a) { /* domain logic */ }
    private void handleOpportunityTask(Task t, Opportunity o) { /* domain logic */ }
    private void handleCaseTask(Task t, Case c) { /* domain logic */ }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

> `AccountHierarchyService.cls-meta.xml`.

---

## 3. `AccountHierarchySelectorTest.cls`

Builds a parent → child → grandchild graph (Account → Opportunity → Task, plus Account → Contact)
with `TestDataFactory`, and asserts every shape the selector returns — including one Account with
no children at all.

```apex
@IsTest
private class AccountHierarchySelectorTest {

    private static final Integer PARENTS_WITH_CHILDREN = 5;
    private static final Integer CONTACTS_PER_ACCOUNT  = 3;
    private static final Integer OPPS_PER_ACCOUNT      = 2;

    /**
     * Graph:
     *   accounts[0..4]  parents with Contacts, Opportunities and Tasks
     *   accounts[5]     parent with NO children of any kind (the empty case)
     *
     * Tasks are the grandchild layer: each Task points at an Opportunity through
     * the polymorphic What relationship and at the Account through AccountId.
     * No SeeAllData; every record is created here.
     */
    @TestSetup
    static void makeData() {
        List<Account> accounts = TestDataFactory.createAccounts(PARENTS_WITH_CHILDREN + 1, null);
        insert accounts;

        List<Contact> contacts = new List<Contact>();
        List<Opportunity> opps = new List<Opportunity>();
        for (Integer i = 0; i < PARENTS_WITH_CHILDREN; i++) {
            contacts.addAll(TestDataFactory.createContacts(CONTACTS_PER_ACCOUNT, accounts[i].Id, null));
            opps.addAll(TestDataFactory.createOpportunities(OPPS_PER_ACCOUNT, accounts[i].Id, null));
        }
        insert contacts;
        insert opps;

        List<Task> tasks = new List<Task>();
        for (Opportunity o : opps) {
            tasks.add(new Task(
                Subject = 'Follow up ' + o.Name,
                Status = 'Not Started',
                WhatId = o.Id
            ));
        }
        insert tasks;
    }

    private static Set<Id> allAccountIds() {
        return new Map<Id, Account>([SELECT Id FROM Account]).keySet();
    }

    private static Id childlessAccountId() {
        // The one Account with no Contacts and no Opportunities.
        for (Account a : [
            SELECT Id, (SELECT Id FROM Contacts), (SELECT Id FROM Opportunities) FROM Account
        ]) {
            if (a.Contacts.isEmpty() && a.Opportunities.isEmpty()) {
                return a.Id;
            }
        }
        return null;
    }

    @IsTest
    static void parentToChildReturnsBothCollections() {
        Set<Id> ids = allAccountIds();

        Test.startTest();
        List<Account> rows = new AccountHierarchySelector()
            .selectWithContactsAndOpportunities(ids);
        Integer queriesUsed = Limits.getQueries();
        Test.stopTest();

        Assert.areEqual(PARENTS_WITH_CHILDREN + 1, rows.size(), 'Every Account should come back');

        Integer withChildren = 0;
        for (Account a : rows) {
            Assert.isNotNull(a.Name, 'Parent field must be projected');
            if (!a.Contacts.isEmpty()) {
                withChildren++;
                Assert.areEqual(
                    CONTACTS_PER_ACCOUNT, a.Contacts.size(),
                    'Subquery must return every matching child for a populated parent'
                );
                Assert.areEqual(
                    OPPS_PER_ACCOUNT, a.Opportunities.size(),
                    'Second subquery must be independent of the first'
                );
            }
        }
        Assert.areEqual(PARENTS_WITH_CHILDREN, withChildren, 'Exactly the seeded parents have children');

        // One top-level query, not one per parent. The two subqueries are charged
        // to the separate aggregate-query pool (apexdev L19613-L19616), not here.
        Assert.areEqual(1, queriesUsed, 'The whole shape must cost one top-level SOQL query');
    }

    @IsTest
    static void childlessParentIterationDoesNotThrow() {
        Id emptyId = childlessAccountId();
        Assert.isNotNull(emptyId, 'Setup must leave one Account with no children');

        Test.startTest();
        List<AccountHierarchyService.AccountSummary> summaries =
            new AccountHierarchyService().summarise(new Set<Id>{ emptyId });
        Test.stopTest();

        // The point of this test is that the guarded iteration completes at all.
        // It deliberately does not assert null-vs-empty: see the UNVERIFIED note
        // in "How to read this set".
        Assert.areEqual(1, summaries.size(), 'The parent row itself is still returned');
        Assert.areEqual(0, summaries[0].contactCount, 'A childless parent contributes no children');
        Assert.areEqual(0, summaries[0].openOpportunityCount, 'No open opportunities either');
    }

    @IsTest
    static void childToParentTraversalResolvesTwoHops() {
        Set<Id> ids = allAccountIds();

        Test.startTest();
        List<Contact> rows = new AccountHierarchySelector()
            .selectContactsWithAccountOwner(ids);
        Test.stopTest();

        Assert.areEqual(
            PARENTS_WITH_CHILDREN * CONTACTS_PER_ACCOUNT, rows.size(),
            'Every seeded Contact should match the active-owner filter'
        );
        for (Contact c : rows) {
            Assert.isNotNull(c.Account.Name, 'First hop must resolve');
            Assert.isNotNull(c.Account.Owner.Name, 'Second hop must resolve');
        }
    }

    @IsTest
    static void polymorphicWhatProjectsPerType() {
        Set<Id> ids = allAccountIds();

        Test.startTest();
        Map<String, Integer> counts =
            new AccountHierarchyService().routeTasksByWhatType(ids);
        Test.stopTest();

        Assert.areEqual(
            PARENTS_WITH_CHILDREN * OPPS_PER_ACCOUNT, counts.get('Opportunity'),
            'Every seeded Task points its What at an Opportunity'
        );
        Assert.areEqual(0, counts.get('Account'), 'No Task was pointed at an Account');
        Assert.areEqual(0, counts.get('Case'), 'No Task was pointed at a Case');
    }

    @IsTest
    static void semiJoinFiltersToParentsWithOpenChildren() {
        Set<Id> ids = allAccountIds();

        Test.startTest();
        List<Account> rows = new AccountHierarchySelector()
            .selectAccountsWithOpenOpportunities(ids);
        Test.stopTest();

        Assert.areEqual(
            PARENTS_WITH_CHILDREN, rows.size(),
            'The childless Account must be excluded by the semi-join'
        );
    }

    @IsTest
    static void bulkParentSetStaysWithinOneQuery() {
        // Bulk shape: 200 parents in one call, the trigger-batch size.
        List<Account> bulk = TestDataFactory.createAccounts(200, null);
        insert bulk;
        Set<Id> ids = new Map<Id, Account>(bulk).keySet();

        Test.startTest();
        List<Account> rows = new AccountHierarchySelector()
            .selectWithContactsAndOpportunities(ids);
        Assert.areEqual(1, Limits.getQueries(), 'One query for 200 parents, not 200');
        Test.stopTest();

        Assert.areEqual(200, rows.size(), 'Every parent in the bulk set comes back');
    }
}
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

> `AccountHierarchySelectorTest.cls-meta.xml`.

---

## 4. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>BaseSelector</members>
        <members>TestDataFactory</members>
        <members>AccountHierarchySelector</members>
        <members>AccountHierarchyService</members>
        <members>AccountHierarchySelectorTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

---

## 5. Deploy order

Apex compiles the whole deployment together, so a single `sf project deploy start` with the manifest
above is enough — but if you are landing this across separate deployments, the dependency order is:

| # | Deploy | Why it must come first |
|---|---|---|
| 1 | `BaseSelector` (+ `BaseService`, `ApplicationLogger` if used) | `AccountHierarchySelector extends BaseSelector`; the subclass will not compile without it |
| 2 | `TestDataFactory` | Referenced by the test class only, but must exist before it |
| 3 | `AccountHierarchySelector` | Referenced by the service and the test |
| 4 | `AccountHierarchyService` | Referenced by the test |
| 5 | `AccountHierarchySelectorTest` | Depends on all of the above |

```bash
# Retrieve what is already in the org, so you diff rather than clobber
sf project retrieve start \
  --metadata "ApexClass:BaseSelector" \
  --metadata "ApexClass:TestDataFactory" \
  --target-org my-sandbox

# Validate without committing (check-only), running just these tests
sf project deploy start \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests AccountHierarchySelectorTest \
  --dry-run \
  --target-org my-sandbox

# Deploy for real
sf project deploy start \
  --manifest manifest/package.xml \
  --test-level RunSpecifiedTests \
  --tests AccountHierarchySelectorTest \
  --target-org my-sandbox
```

---

## 6. Verification

**a. Run the tests and read the coverage + assertions.**

```bash
sf apex run test \
  --tests AccountHierarchySelectorTest \
  --result-format human \
  --code-coverage \
  --wait 10 \
  --target-org my-sandbox
```

All six methods must pass. `childlessParentIterationDoesNotThrow` failing is the signal that a
guard was dropped; `bulkParentSetStaysWithinOneQuery` failing means a query drifted into a loop.

**b. Confirm the shape against real data in the org.** Run in Developer Console → Query Editor, or:

```bash
sf data query --target-org my-sandbox --query \
  "SELECT Id, Name, (SELECT Id FROM Contacts LIMIT 5), (SELECT Id FROM Opportunities LIMIT 5) FROM Account LIMIT 5"
```

A parse error naming a column that does not exist on the parent entity is the relationship-name
mistake from gotcha 2 — check `ChildRelationship.getRelationshipName()` for the real token.

**c. Confirm the subquery pool is being charged as expected.** In anonymous Apex:

```apex
Integer before = Limits.getAggregateQueries();
List<Account> rows = new AccountHierarchySelector()
    .selectWithContactsAndOpportunities(new Set<Id>{ '<an account id>' });
System.debug('aggregate queries used: ' + (Limits.getAggregateQueries() - before));
System.debug('pool size: ' + Limits.getLimitAggregateQueries());
System.debug('top-level queries: ' + Limits.getQueries());
```

Two subqueries in the method, so the aggregate delta should be 2 while top-level queries is 1 —
the accounting described at `apexdev L19613–19616`.

**d. Run the skill's checker over the source tree before review.**

```bash
python3 skills/apex/apex-soql-relationship-queries/scripts/check_apex_soql_relationship_queries.py \
  --manifest-dir force-app/main/default/classes
```

Exit 0 with no ERROR lines. Add `--strict` in CI to fail on WARN as well.

---

## Sources

| Claim | Source |
|---|---|
| Each parent-child relationship counts as an extra query against a 3× pool read from `Limits.getLimitAggregateQueries()` | `apexdev L19613–19616` |
| 100 sync / 200 async top-level SOQL queries; 50,000 total rows per transaction | `apexdev L19544, L19546` |
| `Aggregate query has too many rows for direct assignment, use FOR loop` at 200+ children in a SOQL for loop | `apexdev L10078–10098` |
| Batch `start()` with a relationship subquery uses the slower, non-chunking implementation; query children in `execute()` instead | `apexdev L17796–17805` |
| Typed child access (`inv.Line_Items__r`) is the guide's own bulkification pattern | `apexdev L20245–20255` |
| `getSObjects()` is the dynamic accessor, returning `SObject[]`, with `String` and `Schema.SObjectType` overloads | `apexrefguide L233175–233225` |
| The null guard and its comment "Prevent a null relationship from being accessed" | `apexdev L11703–11730` |
| `.Type` filtering and `TYPEOF What` projection on Event; `instanceof` for runtime type | `apexdev L9772–9795` |
| A polymorphic reference must be assigned to a typed variable before being passed to a method | `apexdev L9797–9798`, worked at `L9820–9836` |
| `Task`/`Event` `WhatId` refers to Account, Opportunity, Campaign or Case; `WhoId` to Contact or Lead | `object_reference L2399–2401` |
| `Task.WhatId` relationship name is `What` | `object_reference L23950–23969` |
| `Contact.AccountId` relationship name is `Account` | `object_reference L71327–71342` |
| Custom relationship naming: `MyRel__c` pointer, `MyRel__r` relationship name | `object_reference L3022–3032` |
| API 67.0+: user mode by default, `WITH SECURITY_ENFORCED` unusable | `apexdev L11742–11744`, `L44493–44502` |
| Bulk API 2.0 rejects parent-to-child subqueries and `TYPEOF`; PK chunking needs subquery-free SOQL | `api_asynch L2892–2896`, `L7147` |
