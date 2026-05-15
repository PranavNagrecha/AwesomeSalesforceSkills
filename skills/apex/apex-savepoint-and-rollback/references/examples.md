# Examples — Apex Savepoint and Rollback

Two worked scenarios and one anti-pattern. Each example assumes the
operation has at least two reversible DML steps and no HTTP callout
in between. For mixed DML+callout flows, see the anti-pattern at the
bottom for why savepoint is the wrong tool.

---

## Example 1: Atomic parent-child creation with rethrow

**Context:** A custom REST endpoint accepts a payload containing one
Account and 1–50 Contacts. Both inserts must succeed together — a
partial creation (Account with no Contacts) leaves a useless orphan
in the database, and the caller must see a single failure response
rather than a half-baked success.

**Problem:** Without a savepoint, `insert account; insert contacts;`
will leave the Account in place if the Contact insert fails (e.g.,
because one row violates a required-field validation rule). The
caller's retry then creates a duplicate Account. Practitioners
try to fix this by deleting the Account in the catch block —
which works for simple cases but breaks if a flow has already
fired follow-on logic against the Account between the two
inserts.

**Solution:**

```apex
@RestResource(urlMapping='/accountWithContacts/*')
global with sharing class AccountWithContactsApi {
    @HttpPost
    global static Map<String, Object> create(Account acct, List<Contact> contacts) {
        Savepoint sp = Database.setSavepoint();
        try {
            insert acct;
            for (Contact c : contacts) {
                c.AccountId = acct.Id;
            }
            insert contacts;
            return new Map<String, Object>{
                'success' => true,
                'accountId' => acct.Id,
                'contactIds' => collectIds(contacts)
            };
        } catch (DmlException e) {
            Database.rollback(sp);
            acct.Id = null;
            for (Contact c : contacts) c.Id = null;
            ApplicationLogger.error('AccountWithContactsApi', e);
            throw new AuraHandledException(
                'Account creation failed at row '
                + e.getDmlIndex(0) + ': ' + e.getDmlMessage(0)
            );
        }
    }

    private static List<Id> collectIds(List<Contact> cs) {
        List<Id> ids = new List<Id>();
        for (Contact c : cs) ids.add(c.Id);
        return ids;
    }
}
```

**Why it works:** The savepoint snapshot is taken *before* any DML.
On failure, the rollback erases both inserts in a single operation
— no compensating delete needed. The `Id = null` step on the
in-memory `acct` and `contacts` is essential: rollback erases the
database row but NOT the populated `Id` field on the Apex objects.
If the caller retries with the same payload (some retry policies
do this transparently), the second attempt would otherwise fail
with `DUPLICATE_VALUE: duplicate id`.

---

## Example 2: Service-layer pattern — caller owns the savepoint

**Context:** A `LeadConversionService` orchestrates several
sub-operations: convert the Lead, create an Opportunity, create a
Quote, attach related-object records. Each sub-operation is a
separate method, possibly in a separate class. The whole orchestration
should be atomic, but the savepoint placement should not leak into
every sub-method.

**Problem:** Practitioners place savepoints *inside* each sub-method
"to be safe." This generates one savepoint+rollback per sub-method,
which means: (1) governor budget burned 2×N DML statements on
savepoint bookkeeping alone, (2) inner rollback inadvertently
undoes work that *should* persist when the outer operation
catches and recovers, and (3) the outer caller has no way to
roll back work done by completed sub-methods.

**Solution:** Single ownership at the orchestration boundary.

```apex
public with sharing class LeadConversionService {

    public Result convertWithFullSetup(Id leadId, ConversionOptions opts) {
        Savepoint sp = Database.setSavepoint();
        try {
            ConvertedRecord cr = convertLead(leadId);
            Opportunity opp    = OpportunityFactory.fromLead(cr, opts);
            insert opp;
            Quote q            = QuoteFactory.initialQuote(opp, opts);
            insert q;
            attachStandardLineItems(q, opts);
            return new Result(cr, opp, q, /*success*/ true);
        } catch (Exception e) {
            Database.rollback(sp);
            ApplicationLogger.error('LeadConversionService', e,
                new Map<String,Object>{ 'leadId' => leadId });
            throw new ServiceException('Lead conversion aborted', e);
        }
    }

    private static ConvertedRecord convertLead(Id leadId) { ... }
    private static void attachStandardLineItems(Quote q, ConversionOptions opts) { ... }
}
```

And the sub-classes (`OpportunityFactory.fromLead`,
`attachStandardLineItems`, etc.) contain **no** savepoint logic.
They throw on failure, trusting the caller.

**Why it works:** One savepoint, one rollback — 2 DML statements
spent on transaction control. The atomicity boundary is visible
at the orchestration layer where it belongs. Sub-methods stay
composable; the same `OpportunityFactory.fromLead` can be called
from a unit test or a different orchestrator without dragging
savepoint plumbing along. The pattern matches the canonical
`templates/apex/BaseDomain` + `BaseService` shape — savepoint
lives in the Service, never in the Domain or Selector.

---

## Anti-Pattern: Savepoint inside a per-record loop

**What practitioners do:**

```apex
for (Account a : accounts) {
    Savepoint sp = Database.setSavepoint();
    try {
        insert a;
        insert buildContactsFor(a);
    } catch (Exception e) {
        Database.rollback(sp);
        failedAccountIds.add(a.Id);
    }
}
```

**What goes wrong:** Each iteration consumes **2 DML statements**
(one for `setSavepoint`, one for `rollback`) plus the actual
DML operations. For 200 records that's 400+ DML statements from
savepoint bookkeeping alone — well over the 150-statement
governor limit. The first ~37 records succeed, then the
transaction dies with `System.LimitException: Too many DML
statements: 151` and the platform rolls back EVERYTHING — the
"isolated try/catch" the developer thought they had is fictional.

**Correct approach:** Hoist the DML out of the loop entirely.
Collect candidate records, attempt one bulk `Database.insert(..., false)`
with `allOrNone=false`, and inspect the `Database.SaveResult[]`
to identify which rows failed. Savepoints are for atomicity of a
*transaction*, not for per-record error isolation:

```apex
List<Contact> allContacts = new List<Contact>();
for (Account a : accounts) allContacts.addAll(buildContactsFor(a));

Database.SaveResult[] accountResults =
    Database.insert(accounts, false);
List<Contact> validContacts = new List<Contact>();
for (Integer i = 0; i < accountResults.size(); i++) {
    if (accountResults[i].isSuccess()) {
        for (Contact c : contactsForAccount(accounts[i].Id, allContacts)) {
            c.AccountId = accountResults[i].getId();
            validContacts.add(c);
        }
    } else {
        failedAccountIds.add(accounts[i].ExternalId__c);
    }
}
Database.insert(validContacts, false);
```

If you genuinely need per-record atomicity (account+contacts
together-or-not), batch into smaller groups (say, 25 accounts
per Queueable chain) and use one savepoint per Queueable execution,
not per record.
