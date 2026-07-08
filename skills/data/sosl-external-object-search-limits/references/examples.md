# Examples — SOSL External Object Search Results Limits

All SOSL below is illustrative scaffolding authored from the official SOQL and SOSL Reference.
Replace object/field API names with your own. External objects end in `__x`; their custom fields
end in `__c`. The reference page carries no GA/Beta/Pilot maturity label — do not add one.

## Example 1: A correct external-object SOSL search

**Context:** an `Order__x` external object is backed by an OData 2.0 data source. You want to find
orders whose text fields mention "Acme".

**Problem:** ported from a standard-object query, the search returns nothing — the external object was
never named in `RETURNING`, and `IN ALL FIELDS` does not pull external objects into results on its own.

**Solution:**

```apex
// Name the external object explicitly in RETURNING; list only text fields;
// keep the FIND term at 100 characters or fewer; use a wildcard, not LIKE.
List<List<SObject>> hits = [
    FIND 'Acme*'
    IN ALL FIELDS
    RETURNING Order__x(ExternalId__c, AccountName__c, Description__c)
];
List<Order__x> orders = (List<Order__x>) hits[0];
```

**Why it works:** the external object is opt-in to results, so the explicit
`RETURNING Order__x(...)` is what surfaces its matches. `AccountName__c` and `Description__c` are text
fields (the only searchable type on an external object), and `Acme*` is a wildcard search rather than a
`LIKE` operator, which external objects reject.

---

## Example 2: Replacing unsupported operators, functions, and clauses

**Context:** a standard-object SOSL statement is repointed at `Order__x`. It uses `LIKE`, `toLabel()`,
and `WITH DATA CATEGORY` — all valid on standard objects, all invalid on external objects.

**Problem:** the whole SOSL statement fails on the external object, not just the offending token.

**Solution:**

```apex
// WRONG — LIKE, toLabel(), and WITH DATA CATEGORY are unsupported on external objects
// List<List<SObject>> bad = [
//     FIND 'Acme%'                         // LIKE-style wildcard is a SOQL idiom, not SOSL
//     RETURNING Order__x(toLabel(Status__c))
//     WITH DATA CATEGORY Geography__c ABOVE usa__c
// ];

// RIGHT — wildcard in FIND, raw field returned, no WITH DATA CATEGORY
List<List<SObject>> good = [
    FIND 'Acme*'
    RETURNING Order__x(ExternalId__c, Status__c, Description__c)
];
```

**Why it works:** SOSL wildcards (`*`, `?`) live inside the FIND term, so `'Acme*'` replaces the SOQL
`LIKE 'Acme%'`. `toLabel()` and `WITH DATA CATEGORY` are removed entirely — external objects support
neither, and translation/category filtering has to happen in the client or the source system.

---

## Example 3: Diagnosing "returns no records" after a data-source sync

**Context:** a search over `Invoice__x` that worked last week now returns nothing. No code changed, no
error is thrown.

**Problem:** a routine sync of the external data source ran in between. Syncing overwrites the external
object's search status to match the data source's — and the data source had search off.

**Solution (diagnosis order):**

```text
1. Search enabled on the EXTERNAL DATA SOURCE?   -> was OFF; enable it
2. Search enabled on the EXTERNAL OBJECT?         -> sync had reset it OFF; enable it
   (Re-check both after EVERY sync — sync overwrites the object flag.)
3. At least one searchable TEXT field on Invoice__x? -> yes (Description__c)
4. Invoice__x named in the RETURNING clause?      -> yes
5. FIND term <= 100 characters, no LIKE/INCLUDES?  -> yes
```

```apex
// Once search is re-enabled on both layers, the same query returns rows again:
List<List<SObject>> hits = [
    FIND 'unpaid'
    RETURNING Invoice__x(ExternalId__c, Description__c)
];
```

**Why it works:** the failure was never in the query or the adapter endpoint — it was the search-enabled
flag on the object being silently reset by sync. Walking the enablement checks first avoids a wasted
investigation into connectivity.

---

## Example 4: Adapter-scoped limits (OData vs custom adapter)

**Context:** the same logical search is needed against two external objects — `Shipment__x` (OData 4.0)
and `Ledger__x` (custom Apex Connector Framework adapter).

**Problem:** OData rejects logical operators in FIND; the custom adapter rejects `convertCurrency()` and
generic `WITH`. Applying the wrong workaround to the wrong adapter is a needless failure.

**Solution:**

```apex
// OData adapter: no logical operators (AND/OR/AND NOT) in FIND — run two searches, merge in code.
List<List<SObject>> a = [FIND 'Acme'   RETURNING Shipment__x(TrackingNo__c, Description__c)];
List<List<SObject>> b = [FIND 'Globex' RETURNING Shipment__x(TrackingNo__c, Description__c)];
// (combine a[0] and b[0] in Apex instead of "FIND 'Acme OR Globex'")

// Custom adapter: no convertCurrency() and no generic WITH — return the raw amount, convert later.
List<List<SObject>> c = [
    FIND 'invoice'
    RETURNING Ledger__x(EntryId__c, AmountRaw__c, Description__c)
];
```

**Why it works:** the two limits are adapter-specific. Splitting the FIND is the correct fix for the
OData object; dropping `convertCurrency()`/`WITH` is the correct fix for the custom-adapter object.
Neither workaround is needed on the other adapter, so applying them blindly would over-constrain a
query that was already valid.

---

## Anti-Pattern: assuming external-object SOSL matches standard-object SOSL

**What practitioners do:** copy a working standard-object SOSL statement, swap the object name for the
`__x` external object, and expect identical behavior — `LIKE`, `INCLUDES`, `toLabel()`, logical
operators in FIND, no explicit `RETURNING`, and long search strings all carried over.

**What goes wrong:** the statement either errors on the first unsupported token or "succeeds" while
silently returning nothing from the external object (missing `RETURNING`, disabled search, or a
non-text field). The failure mode is often silent, so it's mistaken for a data problem.

**Correct approach:** treat external-object SOSL as its own dialect — explicit `RETURNING`, text fields
only, ≤100-character FIND term, no `INCLUDES`/`LIKE`/`EXCLUDES`/`toLabel()`/`UPDATE TRACKING`/
`UPDATE VIEWSTAT`/`WITH DATA CATEGORY`, and adapter-scoped care for logical operators (OData) and
`convertCurrency()`/`WITH` (custom adapters).
