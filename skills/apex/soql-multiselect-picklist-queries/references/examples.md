# Examples — SOQL Multi-Select Picklist Queries

All queries below use the SOQL reference's own placeholder object/field (`CustObj__c.MSP1__c`)
or a realistic `Contact.Interests__c`. Swap in your object, field API name, and values. The
grammar is documented behavior of the SOQL `WHERE` clause; the only version gate is that
matching a value by its **API name** requires API version 39.0+.

## Example 1: "Has this value" containment (INCLUDES)

**Context:** a marketing list needs every contact who selected `Golf` in a multi-select
`Interests__c`, regardless of whatever else they picked.

**Problem:** the obvious `Interests__c = 'Golf'` returns only contacts whose *entire*
selection is exactly `Golf`. Anyone who picked `Golf;Tennis` is missed, so the list comes
back far too small and nobody notices until a campaign under-sends.

**Solution:**

```sql
SELECT Id, Interests__c
FROM Contact
WHERE Interests__c INCLUDES ('Golf')
```

**Why it works:** `INCLUDES` is the documented containment operator — "Contains the specified
string." It matches any record where `Golf` is one of the selected values, ignoring the rest
of the semicolon-delimited blob.

---

## Example 2: AND within a group, OR across groups

**Context:** find records where either (both `AAA` and `BBB` are selected) or (`CCC` is
selected). This is the reference's own worked example.

**Problem:** semicolon-AND and comma-OR are easy to invert, and the two forms mean different
things.

**Solution:**

```sql
SELECT Id, MSP1__c
FROM CustObj__c
WHERE MSP1__c INCLUDES ('AAA;BBB','CCC')
```

**Why it works:** the semicolon inside `'AAA;BBB'` requires both values on the same record;
the comma between `'AAA;BBB'` and `'CCC'` is an OR across groups. So `'AAA;BBB'` and
`'AAA;BBB;DDD'` match the first group, while `'CCC'`, `'CCC;EEE'`, and `'AAA;CCC'` match the
second. A record whose only value is `'AAA'` matches neither.

---

## Example 3: Exclusion (EXCLUDES)

**Context:** suppress contacts who opted into `DoNotContact`, or who selected both `Bulk` and
`Promo` together.

**Problem:** `Interests__c != 'DoNotContact'` only excludes contacts whose *sole* selection is
`DoNotContact`; anyone with `DoNotContact;News` slips through the filter.

**Solution:**

```sql
SELECT Id
FROM Contact
WHERE Interests__c EXCLUDES ('DoNotContact','Bulk;Promo')
```

**Why it works:** `EXCLUDES` — "Does not contain the specified string" — is the true negative
containment. Each excluded record must contain neither `DoNotContact` alone nor the `Bulk`+`Promo`
pair.

---

## Example 4: Injection-safe filtering in Apex (static SOQL + bind)

**Context:** an LWC passes user-chosen interests to Apex, which must return matching contacts.

**Problem:** concatenating the incoming values into a `Database.query(...)` string is a
SOQL-injection hole, and hand-building the semicolon/comma grammar in a raw string is
error-prone.

**Solution:**

```apex
public with sharing class InterestSelector {
    // caller supplies each operand already grouped: 'Golf', 'Tennis;Squash', ...
    public static List<Contact> byInterests(List<String> interestGroups) {
        // Filter literals in a WHERE clause are a supported bind position.
        return [
            SELECT Id, Name, Interests__c
            FROM Contact
            WHERE Interests__c INCLUDES :interestGroups
            WITH USER_MODE
        ];
    }
}
```

**Why it works:** the values ride in a bind variable instead of being concatenated into the
query text, so they can't alter the query structure. `WITH USER_MODE` enforces the running
user's CRUD/FLS on the query. The semicolon-AND grouping is expressed inside each String the
caller supplies (e.g. `'Tennis;Squash'`), not in the query literal.

---

## Example 5: Matching by API name vs display label (API 39.0+)

**Context:** the picklist labels were translated for a French org, but the value API names
(set when the values were created) are unchanged English tokens.

**Problem:** filtering by the translated label is fragile — it breaks the moment a label
changes. The stable identifier is the value's API name.

**Solution:**

```sql
-- In API version 39.0 and later, the operand can be the value's API name,
-- which can differ from the actual (display) value:
SELECT Id, Interests__c
FROM Contact
WHERE Interests__c INCLUDES ('Golf')   -- 'Golf' = API name, even if the label shows 'Le Golf'
```

**Why it works:** since API version 39.0, SOQL resolves the operand against the value's API
name, which can differ from the display value. Confirm your query/connection runs at 39.0+
before relying on this.

---

## Anti-Pattern: `LIKE '%value%'` as a containment test

**What practitioners do:** reach for `WHERE Interests__c LIKE '%Golf%'`, reasoning that a
multi-select value is "just a string," so a substring match should find the value.

**What goes wrong:** `LIKE` matches *substrings* across the whole semicolon-delimited blob. It
will match `Golfing` or `MiniGolf`, and its behavior against the delimited storage is not the
supported containment semantics. It also can't express the AND-within / OR-across grouping.

**Correct approach:** use the documented operator — `INCLUDES ('Golf')` — which tests for the
value as a whole selection, and use semicolons/commas for AND/OR grouping.

---

## Anti-Pattern: sorting by the multi-select field

**What practitioners do:** append `ORDER BY Interests__c` to get a tidy, grouped result.

**What goes wrong:** multi-select picklist is one of the data types unsupported in `ORDER BY`
(with rich text area, long text area, encrypted fields, and data category group reference).
The query errors — it does not silently return unsorted rows.

**Correct approach:** order by a supported field (e.g. `ORDER BY Name`), or fetch the rows and
sort them in Apex if you truly need to order by the selection.
