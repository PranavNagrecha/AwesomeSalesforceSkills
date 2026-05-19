# Examples — Compound Field Patterns

Two worked scenarios and one anti-pattern showing how compound
fields (Name, Address, Geolocation) behave across SOQL, Apex DML,
and reporting surfaces. Each example focuses on the second-order
issues that surface once you've internalized the basic rule "DML
uses components, SELECT supports compound" — i.e., the platform
behaviors that bite during real implementation rather than the
rules anyone can read off the SKILL.md table.

---

## Example 1: Bulk-update Contact MailingAddress from a CSV import

**Context:** Marketing ops wants to refresh the `MailingAddress`
on ~30,000 Contacts from a hygiene vendor's CSV. The CSV has six
columns: ContactId, Street, City, State, PostalCode, Country.
State & Country Picklists are enabled on the org, so the State
column is the two-letter code ("CA"), not the full name. The
import will run as a Batch Apex job triggered by an admin.

**Problem:** A first-pass implementation reads the CSV and tries
to assign the compound field directly, copying a pattern that
works in Java:

```apex
// FAILS — compound is read-only for DML
Contact c = new Contact(Id = row.contactId);
c.MailingAddress = new Address(
    street = row.street,
    city = row.city,
    state = row.state,
    postalCode = row.postalCode,
    country = row.country
);
update c;
```

Compilation succeeds (the Address field appears on `Contact` in
the schema), but DML throws `INVALID_FIELD_FOR_INSERT_UPDATE,
MailingAddress: address is not creatable`. Worse, the same code
on Account fails with a different message because Account's
`BillingAddress` has slightly different metadata — practitioners
hunt down "the missing permission" for hours before realizing
the rule is platform-wide: compound is read-only for DML across
every object.

A second pass assigns components but uses the wrong State field:

```apex
c.MailingStreet      = row.street;
c.MailingCity        = row.city;
c.MailingState       = row.state;       // "CA" — but picklist is enabled
c.MailingPostalCode  = row.postalCode;
c.MailingCountry     = row.country;
```

With State & Country Picklists on, the `MailingState` text field
expects the *full* state name ("California"), not the code. The
job runs successfully — no error — but the address is saved as
`MailingState = "California"`, `MailingStateCode = null` (because
the platform couldn't reverse-lookup "CA" → "California" from a
text field at DML time). Downstream reports filtering by
`MailingStateCode = 'CA'` silently miss every record this job
touched.

**Solution:** Assign components, prefer the `-Code` field when
State & Country Picklists are enabled, and let the platform
back-fill the text field from the code:

```apex
public class ContactAddressBatch implements Database.Batchable<SObject>, Database.Stateful {

    Map<Id, AddressRow> rowsById;

    public ContactAddressBatch(Map<Id, AddressRow> rowsById) {
        this.rowsById = rowsById;
    }

    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([
            SELECT Id FROM Contact WHERE Id IN :rowsById.keySet()
        ]);
    }

    public void execute(Database.BatchableContext bc, List<Contact> scope) {
        List<Contact> toUpdate = new List<Contact>();
        for (Contact c : scope) {
            AddressRow row = rowsById.get(c.Id);
            Contact updated = new Contact(Id = c.Id);
            updated.MailingStreet      = row.street;
            updated.MailingCity        = row.city;
            updated.MailingPostalCode  = row.postalCode;
            // State & Country Picklists enabled → assign the code, NOT the text
            updated.MailingStateCode   = row.state;     // "CA"
            updated.MailingCountryCode = row.country;   // "US"
            toUpdate.add(updated);
        }
        update toUpdate;
    }

    public void finish(Database.BatchableContext bc) { }

    public class AddressRow {
        public String contactId, street, city, state, postalCode, country;
    }
}
```

**Why it works:** Three things make this resilient. First, every
write targets components — no `c.MailingAddress = ...` anywhere
in the code. Second, when State & Country Picklists are on, the
`-Code` field is the source of truth and the platform auto-
populates the matching text field on save (so reports filtering
by either field stay consistent). Third, the SOQL in `start()`
selects only `Id` — there's no point pulling `MailingAddress`
because we're overwriting every component anyway. The job
processes 30,000 records in ~30 chunks of 1,000 without hitting
heap or CPU limits.

---

## Example 2: Store locator — proximity search via SOQL DISTANCE

**Context:** A retail customer has a `Store__c` custom object
with a `Location__c` Geolocation field (decimal notation, 5
decimal places). A customer-facing LWC needs to return the
nearest 10 stores within 25 miles of the user's browser-supplied
lat/lon. Performance bar: < 400ms p95 with 12,000 store records.

**Problem:** The instinct from any non-Salesforce background is
to compute Haversine distance in Apex, sort, and return the top
10:

```apex
// SLOW and governor-fragile
List<Store__c> stores = [SELECT Id, Name, Location__Latitude__s,
                                Location__Longitude__s FROM Store__c];
List<StoreWithDistance> withDistance = new List<StoreWithDistance>();
for (Store__c s : stores) {
    Decimal d = haversine(userLat, userLon,
                          s.Location__Latitude__s, s.Location__Longitude__s);
    if (d <= 25) withDistance.add(new StoreWithDistance(s, d));
}
withDistance.sort(); // sort by distance
return slice(withDistance, 0, 10);
```

At 12,000 stores this returns 12,000 rows, eats most of the
50,000-row SOQL governor budget, runs 12,000 `Math.cos/sin/sqrt`
calls in Apex CPU time (~3-4 seconds), and serializes a giant
sort in memory. The first time someone runs a marketing campaign
that 10× the traffic, CPU limit failures cascade.

**Solution:** Push the math down into SOQL with `DISTANCE` and
`GEOLOCATION`. The platform indexes geolocation for this and
sorts/filters at the database tier:

```apex
public with sharing class StoreLocatorService {

    @AuraEnabled(cacheable=true)
    public static List<StoreResult> findNearest(Decimal lat, Decimal lon) {
        List<Store__c> nearest = [
            SELECT Id, Name, Address__c,
                   DISTANCE(Location__c, GEOLOCATION(:lat, :lon), 'mi') dist
            FROM Store__c
            WHERE DISTANCE(Location__c, GEOLOCATION(:lat, :lon), 'mi') < 25
            ORDER BY DISTANCE(Location__c, GEOLOCATION(:lat, :lon), 'mi')
            LIMIT 10
        ];

        List<StoreResult> out = new List<StoreResult>();
        for (Store__c s : nearest) {
            // DISTANCE() result is accessed via the aliased field name
            // through the field map, not as a typed SObject field
            Decimal d = (Decimal) s.get('dist');
            out.add(new StoreResult(s.Id, s.Name, s.Address__c, d));
        }
        return out;
    }

    public class StoreResult {
        @AuraEnabled public Id storeId;
        @AuraEnabled public String name;
        @AuraEnabled public String address;
        @AuraEnabled public Decimal distanceMiles;
        public StoreResult(Id id, String n, String a, Decimal d) {
            storeId = id; name = n; address = a; distanceMiles = d;
        }
    }
}
```

**Why it works:** `DISTANCE` is one of the few functions allowed
in a SOQL `WHERE` clause against a compound field — the platform
treats it as a special operator, not a compound filter, so it
sidesteps the "no compound in WHERE" restriction. The function
works in `SELECT`, `WHERE`, and `ORDER BY`, which lets the query
return exactly the 10 rows the LWC needs. The result of
`DISTANCE` is exposed as an unnamed aliased column; access it
through `SObject.get('dist')` rather than typed field access
(the compiler doesn't model the alias). Supported units are
`'mi'` and `'km'`; the same float is returned regardless of
ordering operands. p95 drops from ~3.5s to ~80ms because the
database handles bounding-box filtering and sorting before
returning rows.

One subtlety the docs are quiet about: `DISTANCE` in `WHERE`
cannot be combined with `OR` against another `DISTANCE` call —
you get `MALFORMED_QUERY: line N: invalid query` if you try
`WHERE DISTANCE(...) < 25 OR DISTANCE(...) < 10`. Wrap multi-
origin searches as separate queries and merge in Apex.

---

## Anti-Pattern: Filtering a report or SOQL WHERE clause by the compound field

**What practitioners do:** A report builder or a developer needs
"all Accounts in California with a billing ZIP starting with 9".
The instinct from working with non-compound fields is to put the
compound field name in the filter:

```
SELECT Id, Name FROM Account WHERE BillingAddress LIKE '%California%'
```

Or in the Report Builder:

```
Filter: Billing Address contains "California"
```

**What goes wrong:** The SOQL fails immediately with
`MALFORMED_QUERY: line 1:38 no viable alternative at character
'B'` — the parser treats `BillingAddress` in a `WHERE` position
as a syntax error rather than a meaningful filter. There is no
graceful failure mode; the query just doesn't compile.

In the Report Builder, the behavior is worse: the compound
"Billing Address" field appears in the column picker (selecting
it works — it renders as a formatted block) but does NOT appear
as a filterable field in the filter dropdown. Practitioners
search the field list, can't find it, conclude "address filtering
is broken in Reports," and waste an afternoon on the Trailblazer
Community before someone explains that you filter on `Billing
City`, `Billing State`, `Billing State/Province (Code)`, `Billing
Zip/Postal Code`, etc. — one component at a time.

The deeper trap: this rule has ONE exception (`DISTANCE` on
Geolocation in SOQL), which gives a misleading sense that maybe
some other compound filter "should" work too. It doesn't. The
exception is platform-coded for the specific `DISTANCE` operator
on Geolocation only.

**Correct approach:** Filter by components, every time. For the
California ZIP-9 example:

```
-- SOQL
SELECT Id, Name FROM Account
WHERE BillingStateCode = 'CA'        -- code field if SCP enabled, else BillingState
  AND BillingPostalCode LIKE '9%'

-- Report Builder filter rows
Billing State/Province (Code)  equals  CA
Billing Zip/Postal Code        starts with  9
```

For Geolocation proximity, use `DISTANCE` (the documented
exception). For everything else — Name, Address, custom
Geolocation when you just want exact lat/lon match — break the
compound into its components and filter component-by-component.
If the user-facing requirement is "filter by address as one
string," concatenate components in a formula field on the object
and filter on the formula field; do not try to coerce the
compound itself into a filterable shape.
