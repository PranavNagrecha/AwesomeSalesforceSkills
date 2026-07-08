# Gotchas — SOSL External Object Search Results Limits

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Syncing the data source silently resets the object's search flag

**What happens:** an external-object search that worked yesterday returns nothing today, with no code
change and no error.

**When it occurs:** the external data source was synced. Syncing **always overwrites the external
object's search status to match the search status of the external data source**. If the data source has
search off, every sync flips the object's search flag off again.

**How to avoid:** enable search on the external **data source** (not just the object) so syncs preserve
it, and re-verify object search after any sync as part of the runbook. Don't assume a one-time object
toggle is durable.

---

## Gotcha 2: An object with no searchable field returns zero records, not an error

**What happens:** searches over the external object come back empty even though rows clearly exist in the
source system.

**When it occurs:** the object has no `Text` / `Text Area` / `Long Text Area` field, or none are
searchable. Only those text types are indexed for SOSL; **if an external object has no searchable fields,
searches on that object return no records** — silently.

**How to avoid:** confirm at least one text field exists and is searchable before blaming the adapter or
the data. Number, date, checkbox, picklist, and lookup fields never make an object searchable.

---

## Gotcha 3: `IN ALL FIELDS` does not include external objects — RETURNING must name them

**What happens:** a broad `FIND {term} IN ALL FIELDS` returns matches from standard objects but never
from the external object, even when its text fields match.

**When it occurs:** the external object is not named in a `RETURNING` clause. **External objects must be
specified explicitly in a RETURNING clause to be returned in search results** — the search group alone
won't pull them in.

**How to avoid:** always add `RETURNING <Object>__x(textFieldA, textFieldB)` for every external object
you expect in the results, even when using `IN ALL FIELDS`.

---

## Gotcha 4: Adapter-scoped limits are easy to apply to the wrong adapter

**What happens:** a workaround "fixes" one object but is applied needlessly to another, or the real limit
is missed because it was assumed universal.

**When it occurs:** two limits are adapter-specific. **OData 2.0/4.0 adapters don't support logical
operators (`AND`/`OR`/`AND NOT`) in a FIND clause.** **Custom (Apex Connector Framework) adapters don't
support `convertCurrency()` or generic `WITH` clauses.** Treating `convertCurrency()` as blocked on OData,
or logical operators as blocked on custom adapters, either over-constrains a valid query or masks the
real cause.

**How to avoid:** determine the adapter first. Split the FIND (or move logic to Apex) for OData; drop
`convertCurrency()`/`WITH` for custom adapters. Don't generalize either rule across adapter types.

---

## Gotcha 5: The 100-character FIND-term cap is an external-object rule

**What happens:** a long search string that runs fine against standard objects is rejected when the same
statement targets an external object.

**When it occurs:** the FIND search text exceeds 100 characters. For external objects, **text strings must
be 100 or fewer characters.**

**How to avoid:** trim or tokenize the search term to ≤100 characters before issuing an external-object
search; don't pass an unbounded user-supplied string straight into FIND.
