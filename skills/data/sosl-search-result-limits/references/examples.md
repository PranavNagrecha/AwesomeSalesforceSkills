# Examples — SOSL Search Result Limits

All SOSL below is illustrative scaffolding authored from the official *SOSL Limits on
Search Results* topic and the SOQL/SOSL limits cheat sheet. Replace object and field names
with your own. The per-stage limits (2,000-record scan, 250 single-object default,
min(2000/n, 250) multi-object split, permission filtering, and the SearchQuery length
thresholds) are documented platform behaviors, not maturity-gated features.

## Example 1: The 250-record single-object cap, and lifting it

**Context:** a batch reconciliation searches Accounts by an imported name fragment and
expects to process every match. In a full-size org it quietly processes only 250.

**Problem:** a single-object SOSL with no `WHERE` or `ORDER BY` inside the `RETURNING` clause
caps at 250 records — "If you query one object only, a maximum of 250 records are returned."
The developer assumed the 2,000 statement ceiling applied.

**Solution:**

```apex
// BEFORE — silently capped at 250
List<List<SObject>> capped = [
    FIND :fragment IN NAME FIELDS RETURNING Account(Id, Name)
];

// AFTER — a WHERE (or ORDER BY) inside the parentheses raises the cap to 2,000
List<List<SObject>> raised = [
    FIND :fragment IN NAME FIELDS
    RETURNING Account(Id, Name WHERE RecordType.DeveloperName = 'Customer' ORDER BY Name)
];
List<Account> accounts = (List<Account>) raised[0];
```

**Why it works:** the docs state "To return up to 2,000 results, include either the WHERE
clause or ORDER BY clause." Either clause, placed inside the object's parentheses, lifts the
single-object ceiling from 250 to 2,000.

---

## Example 2: Multi-object division shrinks each object's slice

**Context:** a global search box returns Accounts, Contacts, Leads, Cases, and five more
custom objects from one SOSL statement. Users complain that recent Contacts are missing.

**Problem:** each object does not get 250 (let alone 2,000). Per the docs, "each object
returns up to the minimum number between 2,000/n and 250." With 10 objects, 2000/10 = 200,
so each object returns at most 200 — below the 250 you might expect, and far below 2,000.

**Solution:**

```apex
// 10 objects → each capped at min(2000/10, 250) = 200
List<List<SObject>> wide = [
    FIND :term IN ALL FIELDS
    RETURNING Account(Id, Name), Contact(Id, Name), Lead(Id, Name), Case(Id, Subject),
              Opportunity(Id, Name), Asset(Id, Name), Contract(Id, ContractNumber),
              Order(Id, OrderNumber), Product2(Id, Name), Campaign(Id, Name)
];

// Protect a specific object's results by scoping to it (the "Joe" remedy)
List<List<SObject>> focused = [
    FIND :term IN ALL FIELDS
    RETURNING Contact(Id, Name WHERE CreatedDate = LAST_N_DAYS:30 ORDER BY CreatedDate DESC)
];
```

**Why it works:** narrowing to one object removes the min(2000/n, 250) division —
"If Joe limits his search to just one object, the limit applies to only that object,
increasing the chance that the record he wants is returned" — and the `WHERE`/`ORDER BY`
inside `RETURNING` lifts that single object to the 2,000 ceiling.

---

## Example 3: Guarding a dynamic SearchQuery against the length thresholds

**Context:** an Apex service builds a search string from a caller-supplied list of terms and
runs it with `Search.query`. Occasionally it returns zero rows, and occasionally an `AND`
search behaves like a broad `OR`.

**Problem:** two silent thresholds. "If the SearchQuery string is longer than 10,000
characters, no result rows are returned." And "If SearchQuery is longer than 4,000
characters, any logical operators are removed" — so `AND` degrades toward matching anything.
Neither throws an exception.

**Solution:**

```apex
public with sharing class ProductSearchService {
    public class SearchInputException extends Exception {}

    public List<List<SObject>> run(String searchQuery) {
        // Bound well under 4,000 so logical operators are never stripped,
        // and never approach the 10,000-char zero-result cliff.
        if (searchQuery.length() > 4000) {
            throw new SearchInputException(
                'Search string is ' + searchQuery.length() +
                ' chars; over 4,000 removes logical operators (over 10,000 returns nothing).'
            );
        }
        return Search.query(searchQuery);
    }
}
```

**Why it works:** the check fails fast and loudly *before* the platform silently changes the
match semantics or empties the result set, turning two invisible failures into one explicit,
testable error.

---

## Anti-Pattern: "add more objects so we don't miss anything"

**What practitioners do:** when a record is missing from a search, they append more objects to
the `RETURNING` clause, reasoning that a wider net catches more.

**What goes wrong:** the opposite happens. Each object's cap is min(2000/n, 250), so every
object added past the eighth *lowers* the per-object slice (2000/9 = 222, 2000/16 = 125).
The target record becomes less likely to survive, not more.

**Correct approach:** narrow, don't widen. Scope the search to the single object that holds
the record so it gets the full single-object budget, and add a `WHERE`/`ORDER BY` inside its
`RETURNING` parentheses to raise that budget to 2,000.
