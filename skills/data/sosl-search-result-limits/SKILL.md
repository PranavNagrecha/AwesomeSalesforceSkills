---
name: sosl-search-result-limits
description: "Use when a SOSL search silently omits a record that clearly matches the search term — diagnosing the search engine's internal per-stage record caps: the 2,000-record term-matching scan (API v28.0+), the 250-record single-object default and how a WHERE or ORDER BY inside the RETURNING clause raises it to 2,000, the min(2000/n, 250) multi-object split, View All Data vs. per-user permission filtering of results, and the dynamic SearchQuery string-length thresholds (>4,000 chars strips logical operators, >10,000 chars returns zero rows) plus the 100,000-character statement limit. Triggers: 'SOSL not returning all records', 'SOSL only returns 250', '2000 record search cap', 'missing search result', 'SearchQuery too long'. NOT for choosing SOSL vs SOQL, FIND syntax, injection safety, search groups, or USING ListView scoping (use data/sosl-search-patterns); NOT for SOQL row limits or general query governor limits."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "my SOSL search isn't returning a record I know matches the term"
  - "why does my SOSL query only return 250 records"
  - "SOSL is silently dropping matching results when I search several objects"
  - "how do I raise the SOSL single-object result cap above 250"
  - "my dynamic Search.query returns zero rows for a long search string"
tags:
  - sosl-search-result-limits
  - search-result-cap
  - searchquery-length
  - permission-filtering
  - silent-exclusion
inputs:
  - "The SOSL statement (static `[FIND ...]` or dynamic `Search.query`) with the objects and fields in its RETURNING clause"
  - "Whether the running user holds View All Data, plus the object's sharing/OWD model"
  - "The symptom: a specific matching record is missing, results are capped, or zero rows are returned"
outputs:
  - "A diagnosis of which stage limit (2,000-record scan, 250 single-object default, min(2000/n, 250) split, permission filter, or SearchQuery length) is dropping the record"
  - "A remediation: add WHERE/ORDER BY/LIMIT inside the RETURNING clause, narrow to fewer objects, or bound the SearchQuery string length"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOSL Search Result Limits

This skill activates when a SOSL search returns fewer records than expected — or a specific record that plainly matches the search term never appears — and you need to explain *why*. The cause is almost never the developer's `RETURNING` field list; it is a stack of internal limits the search engine applies at each stage of query processing, most of which fail silently rather than raising an error.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the symptom is a missing/capped result, not a syntax or injection problem.** If the question is SOSL vs SOQL, `FIND` wildcards, escaping, or `USING ListView`, that belongs to `data/sosl-search-patterns`. This skill is specifically about records that match but do not come back.
- **Count the objects in the `RETURNING` clause.** The default result cap depends on how many objects a single SOSL statement targets — a one-object search behaves very differently from a ten-object search, and neither uses the 2,000 ceiling most developers assume.
- **Establish the running user's access.** Users with **View All Data** see the full computed result set; every other user has record-level permission filters applied *after* the engine matches, which shrinks results further. The same query returns different counts for an admin and a standard user.
- **Note whether the query is static or dynamic.** A dynamic `SearchQuery` string (as passed to `Search.query`) has its own length thresholds — over 4,000 characters and over 10,000 characters — that change or void results with no exception thrown.

---

## Core Concepts

### The search engine limits records at each stage

Official docs state plainly: "The search engine limits the number of records analyzed at each stage of the search process." A record can be a genuine match on the search term and still be excluded because it fell outside one of those internal stage windows — there is no error, warning, or partial-result flag.

The first stage is term matching: "The search engine looks for matches to the search term across a maximum of 2,000 records (this limit starts with API version 28.0)." So even before any `RETURNING` shaping, the engine only *considers* up to 2,000 records for the term. If the record you want is the 2,001st the engine would have scanned, no amount of `RETURNING` tuning brings it back.

### The returned-record caps are not 2,000 by default

After matching, the number of records actually returned is capped, and the cap depends on object count:

- **One object:** "If you query one object only, a maximum of 250 records are returned." Not 2,000 — 250. To lift it: "To return up to 2,000 results, include either the WHERE clause or ORDER BY clause." That `WHERE`/`ORDER BY` goes *inside* the object's parentheses in the `RETURNING` clause.
- **Multiple objects:** "If you query multiple objects, each object returns up to the minimum number between 2,000/n (where n=number of objects) and 250." So with 2 objects each returns up to 250 (2000/2 = 1000, capped at 250); with 10 objects each returns up to 200 (2000/10 = 200, which is below 250). The more objects you add, the smaller each object's slice becomes once `n` exceeds 8.
- **Statement total:** across the whole statement the ceiling is "2,000 results total (API version 28.0 and later), unless you specify custom limits in the query. This limit includes results from child objects."

### View All Data vs. per-user permission filtering

"Admins (users with the View All Data permission) see the full set of results returned. For all other users, SOSL applies user permission filters." This filtering happens on top of the caps above, so a standard user can receive a shorter result list than an admin running the identical search — records the engine matched are removed because the user cannot see them. When debugging a "missing record," always reproduce as the affected user, not as an admin.

### Dynamic SearchQuery string-length thresholds

When you build the search string dynamically and pass it to `Search.query`, the *string itself* has thresholds that change behavior silently:

- Over 4,000 characters: "If SearchQuery is longer than 4,000 characters, any logical operators are removed." The engine keeps running, but your `AND`/`OR`/`NOT` semantics are gone — matches widen unexpectedly.
- Over 10,000 characters: "If the SearchQuery string is longer than 10,000 characters, no result rows are returned." Not an error — an empty result set.
- The overall SOSL statement: "By default, 100,000 characters. This limit is tied to the SOQL statement character limit defined for your org."

---

## Common Patterns

### Raise the single-object cap from 250 to 2,000

**When to use:** a single-object SOSL search needs more than 250 results (reporting, bulk reconciliation, "find everything named X").

**How it works:** add a `WHERE` filter and/or an `ORDER BY` inside the object's parentheses in the `RETURNING` clause. Per the docs, either one lifts the ceiling to 2,000 for that object.

```apex
// 250-record cap (single object, no WHERE/ORDER BY inside RETURNING)
List<List<SObject>> capped = [FIND 'Acme*' IN NAME FIELDS RETURNING Account(Id, Name)];

// Up to 2,000 — a WHERE or ORDER BY inside the parentheses lifts the cap
List<List<SObject>> raised = [
    FIND 'Acme*' IN NAME FIELDS
    RETURNING Account(Id, Name WHERE Industry = 'Technology' ORDER BY Name)
];
```

**Why not the alternative:** widening the `FIND` term or removing filters does not raise the cap; only the `WHERE`/`ORDER BY` inside `RETURNING` does. Assuming 2,000 is the default and never adding a clause is the most common cause of a silently truncated single-object search.

### Narrow to one object to protect a specific record (the "Joe" pattern)

**When to use:** a user reports that one particular record never appears in a multi-object search, even though it matches.

**How it works:** the docs' own remedy — "If Joe limits his search to just one object, the limit applies to only that object, increasing the chance that the record he wants is returned." Scoping the search to the single object that holds the record removes the min(2000/n, 250) division and gives that object the full single-object budget.

**Why not the alternative:** adding more objects to "cast a wider net" does the opposite — each additional object shrinks every object's slice once `n` passes 8, making the target record *less* likely to survive.

### Bound the SearchQuery length before a dynamic search

**When to use:** the `SearchQuery` string is assembled from user input or a variable-length list of terms and handed to `Search.query`.

**How it works:** measure `String.length()` before the call and reject or truncate above a safe bound well under 4,000 characters, so logical operators are never stripped and you never cross the 10,000-character zero-result cliff.

```apex
String searchQuery = buildSoslFromInput(userTerms);
if (searchQuery.length() > 4000) {
    throw new SearchInputException(
        'Search string exceeds 4,000 characters; logical operators would be removed.'
    );
}
List<List<SObject>> results = Search.query(searchQuery);
```

**Why not the alternative:** relying on Salesforce to error out is unsafe — over 4,000 chars it silently drops operators, and over 10,000 it silently returns nothing. Neither throws.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single-object search returns exactly 250 rows | Add a `WHERE` or `ORDER BY` inside the `RETURNING` object's parentheses | Either clause raises the single-object cap to 2,000 |
| A specific record is missing from a multi-object search | Scope the search to just that object | Removes the min(2000/n, 250) split; gives the object its full budget |
| Search targets 9+ objects and each returns few rows | Reduce object count, or split into per-object searches | Once n > 8, 2000/n drops below 250 and each object shrinks |
| Admin sees the record, standard user does not | Reproduce as the affected user; check sharing/FLS | Non-admins have per-user permission filters applied to results |
| Dynamic `Search.query` returns zero rows unexpectedly | Check `SearchQuery` length against 10,000 chars | Over 10,000 characters, no result rows are returned |
| `AND`/`NOT` in a dynamic search behaves like a broad match | Check `SearchQuery` length against 4,000 chars | Over 4,000 characters, logical operators are removed |
| Need more than 2,000 total results from one statement | Redesign — paginate, filter, or use SOQL/reporting | 2,000 total is the statement ceiling (incl. child objects) unless custom limits are set |

---

## Recommended Workflow

1. **Reproduce as the affected user.** Run the exact SOSL as the reporting user, not as an admin — View All Data hides the permission-filter shrink that a standard user experiences.
2. **Count the objects and read the RETURNING clause.** Determine whether the search is single-object (250 default) or multi-object (min(2000/n, 250) per object), and whether any object's parentheses already contain a `WHERE`/`ORDER BY`/`LIMIT`.
3. **Map the symptom to a stage.** Zero rows from a dynamic query → check `SearchQuery` length (10,000 / 4,000 thresholds). Exactly 250 → single-object cap. Shrinking per-object counts → object-count division. Missing only for some users → permission filtering. Missing beyond ~2,000 scanned → the term-matching scan window.
4. **Apply the matching remedy.** Add `WHERE`/`ORDER BY` inside `RETURNING` to lift a single-object cap; narrow to fewer objects to protect a specific record; bound the `SearchQuery` string length; or set explicit custom per-object limits.
5. **Confirm you are not asking SOSL for a job SOQL should do.** If the requirement is exhaustive, ordered, relational retrieval rather than best-match search, route to SOQL/reporting instead of fighting the caps.
6. **Run the checker and re-verify counts.** Run `scripts/check_sosl_search_result_limits.py` over the Apex, then re-run the search as the affected user and confirm the target record now returns.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The search was reproduced as the affected (non-admin) user, not only as an admin with View All Data
- [ ] Single-object searches that need more than 250 rows include a `WHERE` or `ORDER BY` inside the `RETURNING` parentheses
- [ ] Multi-object searches account for the min(2000/n, 250) per-object cap; object count is not inflated past 8 without reason
- [ ] The design does not assume a single statement can return more than 2,000 rows total (child objects included) without custom limits
- [ ] Dynamic `SearchQuery` strings are length-bounded well under 4,000 characters (operator-stripping) and never approach 10,000 (zero rows)
- [ ] The overall SOSL statement stays within the org's statement character limit (100,000 by default)
- [ ] Any "missing record" claim was traced to a specific stage limit, not left as an unexplained gap

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **250, not 2,000, is the single-object default** — a single-object SOSL with no `WHERE`/`ORDER BY` inside `RETURNING` caps at 250 records, so a search that "works" in dev against small data silently truncates in production.
2. **Adding objects shrinks every object's slice** — because each object returns min(2000/n, 250), a search over 10 objects returns at most 200 per object, not 250; "search more objects to find it" backfires.
3. **Admins and standard users get different results** — permission filtering is applied to search output for everyone without View All Data, so a bug reproduced as an admin can look non-existent while a standard user still cannot see the record.
4. **Dynamic SearchQuery length changes behavior with no error** — over 4,000 characters logical operators are dropped (an `AND` search widens), and over 10,000 characters zero rows return; both fail silently.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Stage-limit diagnosis | Which internal limit (2,000 scan, 250 single-object, min(2000/n, 250) split, permission filter, or SearchQuery length) is dropping the record |
| Remediated SOSL | The `RETURNING` clause with a `WHERE`/`ORDER BY`/custom limit, a narrowed object list, or a length-bounded dynamic string |
| `scripts/check_sosl_search_result_limits.py` output | Findings for single-object 250-caps, high object counts, and unguarded dynamic `Search.query` length risk |
| `templates/sosl-search-result-limits-template.md` | A worksheet mapping each observed symptom to the stage limit and its remedy |

---

## Related Skills

- `data/sosl-search-patterns` — the companion skill for choosing SOSL vs SOQL, `FIND` syntax, search groups, injection safety, and `USING ListView`. Use it for *how to write* the search; use this skill for *why the search dropped a record*.
- `templates/apex/BaseSelector.cls` — the canonical selector layer where a SOSL search method should live so caps, limits, and `USER_MODE` enforcement are set in one reviewed place rather than scattered inline.
- `templates/apex/SecurityUtils.cls` — reference when the missing-record cause turns out to be CRUD/FLS/sharing (the permission-filter stage) rather than a result cap.
