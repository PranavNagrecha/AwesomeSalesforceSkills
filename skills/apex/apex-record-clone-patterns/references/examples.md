# Examples — Apex Record Clone Patterns

Two worked scenarios and one anti-pattern showing how to use
`SObject.clone()` correctly — when the four-arg form earns its keep,
when `.clone()` is the wrong tool because the platform doesn't
traverse children, and when manual field copying is a hidden
maintenance bomb.

---

## Example 1: "Duplicate Case" button using the 4-arg clone

**Context:** Service ops wants a "Duplicate Case" button on the Case
record page. The user picks an existing Case, clicks the button, and
a new Case opens in edit mode with all field values from the source
copied over — including custom fields the support team has added over
the years. Subject should be prefixed with "COPY: " before save. The
new Case must get a fresh `CaseNumber` autonumber so it shows up as a
distinct record in queues, and it should NOT keep the source's
`CreatedDate` (audit hygiene — the new record was created now, not
when the source was logged).

**Problem:** The naive approach is to write a controller that does
`Case copy = new Case(Subject = orig.Subject, Status = orig.Status,
Priority = orig.Priority, ...)` and lists every field. Every time the
team adds a custom field on Case (which happens monthly in an active
support org), the duplicate button silently stops copying that field.
Users discover the gap weeks later when they realize the duplicates
are missing data they entered.

**Solution:** `.clone()` with the four-arg form, picking each flag
intentionally.

```apex
public with sharing class CaseDuplicator {

    @AuraEnabled
    public static Id duplicate(Id sourceCaseId) {
        // Query every accessible field so the clone is faithful.
        // Dynamic SOQL over Schema.SObjectType.getDescribe().fields.getMap()
        // pulls custom fields automatically as they're added.
        Map<String, Schema.SObjectField> caseFields =
            Schema.SObjectType.Case.fields.getMap();
        String fieldList = String.join(new List<String>(caseFields.keySet()), ',');
        String soql = 'SELECT ' + fieldList +
                      ' FROM Case WHERE Id = :sourceCaseId';
        Case src = Database.query(soql);

        // clone(preserveId, isDeepClone, preserveReadonlyTimestamps, preserveAutonumber)
        //  preserveId = false               → new record, so let the platform mint the Id
        //  isDeepClone = true               → duplicate formula/aggregate values
        //                                     in the in-memory copy so the controller
        //                                     can use them before insert
        //  preserveReadonlyTimestamps =false → new CreatedDate (audit hygiene; preserving
        //                                     would also require CreateAuditFields perm)
        //  preserveAutonumber = false       → fresh CaseNumber so queue routing
        //                                     treats this as a distinct record
        Case copy = (Case) src.clone(false, true, false, false);
        copy.Subject = 'COPY: ' + src.Subject;
        copy.Status = 'New';        // override — duplicates always start at New
        copy.IsClosed = false;      // formula-overridden by Status, but explicit is fine
        insert copy;
        return copy.Id;
    }
}
```

**Why it works:** The dynamic-field SOQL pulls every accessible field
on Case — standard, custom, and any added in future months — so the
clone stays faithful as the schema evolves. The four-arg form lets
the code state intent precisely: every flag is deliberate. Setting
`isDeepClone=true` matters here because the controller hands `copy`
back to LWC, which may read formula and roll-up summary values from
the in-memory record before the insert completes. `preserveAutonumber
=false` is the difference between "new Case shows up in Queue Routing"
and "two records share a CaseNumber and confuse the routing engine"
(autonumbers aren't strictly unique on the field, but routing logic
that keys off `CaseNumber` will treat them as identical). The
override of `Status='New'` and `Subject` happens AFTER `.clone()` so
the override-vs-copy boundary is visible in code review.

---

## Example 2: Deep-clone Account + Contacts via JSON serializer

**Context:** A partner-onboarding tool needs to spin up a new Account
that mirrors an existing one — every field on the Account, plus every
related Contact (typically 20–80 per Account). The "Duplicate Account"
operation is invoked once per partner, never in bulk. The cloned
Contacts must reparent to the new Account, the cloned `ReportsToId`
chain among Contacts must be rewritten to point at the corresponding
NEW Contact Ids (preserving the org-chart structure), and the
operation must succeed within one transaction.

**Problem:** `Account.clone()` doesn't traverse to Contacts — the
documented "deep clone" flag is about formula values, not child
records. A naive implementation iterates Contacts manually, calls
`oli.clone()` on each, and inserts — but loses the `ReportsToId`
graph because the new Contact Ids haven't been minted yet at the
point the relationships are read.

**Solution:** JSON-serialize the parent with its children subselect,
deserialize into fresh in-memory objects (which clears all Ids), then
walk the result and reparent via an old→new Id map.

```apex
public with sharing class AccountGraphCloner {

    public static Id cloneWithContacts(Id sourceAccountId) {
        // 1. Query parent + children + ReportsToId relationships
        Account src = [
            SELECT Id, Name, BillingStreet, BillingCity, Industry,
                   AnnualRevenue,
                   (SELECT Id, FirstName, LastName, Email, Title,
                           ReportsToId
                      FROM Contacts)
            FROM Account WHERE Id = :sourceAccountId
        ];

        // 2. Serialize/deserialize wipes all Ids and gives independent
        //    in-memory copies. SObject.clone() can't do this for
        //    nested child relationships — only this pattern can.
        String json = JSON.serialize(src);
        Account copy = (Account) JSON.deserialize(json, Account.class);

        // 3. Detach children from copy before inserting parent.
        //    Reflection lets us pull the child collection in a way
        //    that works across object types.
        List<Contact> childCopies = copy.Contacts;
        copy.Contacts = null;     // clear child relationship; insert parent alone
        insert copy;

        // 4. Build old→new Id map for the Contacts so we can rewrite
        //    the ReportsToId chain. We rely on positional order
        //    being preserved between src.Contacts and childCopies —
        //    JSON.serialize maintains list ordering.
        Map<Id, Id> oldToNewContactId = new Map<Id, Id>();
        List<Contact> srcContacts = src.Contacts;
        for (Integer i = 0; i < childCopies.size(); i++) {
            Contact child = childCopies[i];
            child.AccountId = copy.Id;   // reparent to new Account
        }
        insert childCopies;              // first insert mints new Ids
        for (Integer i = 0; i < childCopies.size(); i++) {
            oldToNewContactId.put(srcContacts[i].Id, childCopies[i].Id);
        }

        // 5. Rewrite ReportsToId chain. Walk childCopies; for each
        //    one with a non-null ReportsToId (the OLD Id, which
        //    survived the JSON round-trip on this lookup field
        //    because we didn't clear it), translate to the NEW Id.
        List<Contact> toUpdate = new List<Contact>();
        for (Contact c : childCopies) {
            if (c.ReportsToId != null && oldToNewContactId.containsKey(c.ReportsToId)) {
                c.ReportsToId = oldToNewContactId.get(c.ReportsToId);
                toUpdate.add(c);
            }
        }
        if (!toUpdate.isEmpty()) update toUpdate;

        return copy.Id;
    }
}
```

**Why it works:** `JSON.serialize()` followed by `JSON.deserialize()`
gives a complete in-memory copy with all Ids stripped (Salesforce
clears `Id` automatically on deserialize) — exactly what `.clone()`
refuses to do for nested children. The `oldToNewContactId` map is the
linchpin: after the first child insert, you have both halves of the
mapping (old Id from `src.Contacts`, new Id from `childCopies` post-
insert), so the ReportsToId rewrite is a one-pass loop. The two-insert
pattern (children once for Ids, again for rewritten lookups) is
unavoidable when self-referential FKs are in play — there's no order
of inserts that mints all Ids before any reference is set.

---

## Anti-Pattern: Manual field-by-field copy via `new Account(...)`

**What practitioners do:**

```apex
// WRONG — looks tidy in code review, breaks every time the schema changes
public static Account duplicateAccount(Account src) {
    return new Account(
        Name           = src.Name,
        BillingStreet  = src.BillingStreet,
        BillingCity    = src.BillingCity,
        BillingState   = src.BillingState,
        BillingCountry = src.BillingCountry,
        Industry       = src.Industry,
        AnnualRevenue  = src.AnnualRevenue,
        Phone          = src.Phone,
        Website        = src.Website
        // ...the list has 47 more standard fields and grows every sprint
    );
}
```

**What goes wrong:** The day someone adds `Customer_Tier__c` to
Account, this method silently stops copying it on duplicates — but
nothing in the code, tests, or PR review flags the gap. The duplicate
"works" (no exception), the new record just has `Customer_Tier__c =
null` where the user expected the source's tier. Discovery happens
weeks or months later when a sales rep notices duplicated accounts are
missing data, files a bug, and the team has to audit every duplication
flow for missing fields. The same pattern repeats on every field
addition: governance teams have to remember to update the duplicator
class, and they don't — because nothing connects the two.

The second-order failure: the manual copy bypasses the `.clone()`
contract entirely. `preserveAutonumber`, `preserveReadonlyTimestamps`,
and `isDeepClone` semantics simply don't exist in the manual form, so
any audit-field preservation or autonumber handling must be re-
invented (and usually isn't, because the developer didn't think about
it). Every per-record handler that does this drifts further from the
platform contract every release.

**Correct approach:** Use `src.clone(false, false, false, false)` (or
the four-arg form with intentional flags as in Example 1) and override
the specific fields you want to change AFTER the clone. The clone
captures every accessible field automatically, so schema additions
flow through with zero code changes. If you need the duplicate to
exclude certain fields (e.g., reset `Status` to 'New'), assign the
override explicitly after the clone — that line is the visible
documentation of what differs between source and copy. See Example 1
for the canonical pattern; the contrast between "one `.clone()` line
plus 3 explicit overrides" and "47 field assignments and counting" is
the entire argument.
