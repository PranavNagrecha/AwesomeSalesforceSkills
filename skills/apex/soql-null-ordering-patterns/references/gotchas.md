# Gotchas — SOQL NULL Ordering Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Default null position flips with sort direction

**What happens:** Engineer writes `ORDER BY field ASC` expecting nulls last. Nulls land first.

**When it occurs:** ASC defaults to NULLS FIRST; DESC defaults to NULLS LAST. Many implementations assume a single default.

**How to avoid:** Always specify `NULLS FIRST` or `NULLS LAST` explicitly. Treat the absence as a code smell.

---

## Gotcha 2: OFFSET caps at 2,000 records total

**What happens:** Pagination works fine for the first 10 pages of 200, then `LIMIT 200 OFFSET 2000` throws "Offset exceeds maximum allowed limit."

**When it occurs:** Any OFFSET-based paging that goes past 2k.

**How to avoid:** Use cursor pagination keyed on `(sortField, Id)`. There is no equivalent low-effort "deep paging" with OFFSET in SOQL.

---

## Gotcha 3: Non-deterministic order on ties

**What happens:** Same query rerun returns ties in different order. Pagination misses or duplicates records around the page boundary.

**When it occurs:** Single-field ORDER BY with duplicate sort-key values.

**How to avoid:** Always include `Id` (or another guaranteed-unique field) as the final tiebreaker.

---

## Gotcha 4: Custom indexes don't cover nulls

**What happens:** Sorting on a custom-indexed field that is mostly null performs as if it had no index — full scan.

**When it occurs:** A field is custom-indexed for filtering, but the team also expects it to support sorting; the index doesn't include nulls by default.

**How to avoid:** For high-null-percentage sort fields, request a "nulls included" index from Salesforce Support. Or rewrite the query to filter out nulls before sorting if the use case allows.

---

## Gotcha 5: NULLS FIRST/LAST keyword form

**What happens:** `NULLS_LAST`, `NULLSLAST`, or `NULLS-LAST` are syntax errors.

**When it occurs:** Engineer transfers other-database syntax.

**How to avoid:** Two separate keywords with a space: `NULLS LAST` or `NULLS FIRST`. No underscore, no hyphen, no concatenation.

---

## Gotcha 6: Standard list-view sorting flipped in Spring '26 — SOQL did not

**What happens:** A custom LWC datatable backed by `ORDER BY SomeField__c ASC` shows blank-field records at the top, while the standard Lightning list view beside it shows those same records at the bottom. Both are "sorted ascending," so users report the custom component as the broken one.

**When it occurs:** Spring '26 changed list-view sorting only. Per the release note *Use Updated Empty Value Placement in List View Sorting*: "When you sort a list view, blank fields, or null values, now are treated as the highest value in the dataset. ... Previously, Salesforce treated blank fields as the lowest value." It applies to Lightning Experience in all editions. SOQL was not part of that change — for an ascending sort the ORDER BY reference still gives nulls first ("By default, null values are sorted first"), so `ORDER BY SomeField__c ASC` still returns blanks at the top. Note the release note frames it as a ranking change ("the highest value in the dataset"), not a pin to the bottom, so a *descending* list-view sort now surfaces blanks first.

**How to avoid:** Any query whose results sit next to, or replace, a standard list view needs an explicit `NULLS LAST` on an ascending sort to match the platform's new convention — the SOQL default and the UI default no longer agree. When a user reports that ordering "changed," establish which surface they are looking at before debugging the query. Exports, saved screenshots, and test assertions captured before Spring '26 are no longer valid expected-output for the list-view side.
