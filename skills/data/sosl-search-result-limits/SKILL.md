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
  - "find out why records of my custom object never show up in SOSL or global search"
  - "stop an AND search term from behaving like OR when the search text gets long"
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
version: 1.1.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# SOSL Search Result Limits

This skill activates when a SOSL search returns fewer records than expected, or a record that plainly matches the search term never appears, and you need to say which limit removed it. The cause is rarely the `RETURNING` field list; it is a stack of limits the search engine applies at each stage, most of which fail without an error.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the symptom is a missing or capped result.** SOSL vs SOQL, `FIND` wildcards, escaping, and `USING ListView` belong to `data/sosl-search-patterns`.
- **Count the objects in `RETURNING`.** The per-object cap depends on that count.
- **Establish the running user's access.** View All Data holders see the full result set; everyone else gets permission filters.
- **Measure the search term, not the statement.** The 4,000 and 10,000 character thresholds apply to the `{SearchQuery}` text inside `FIND`; the whole SOSL statement has a separate 100,000-character default limit.
- **Check that the object is searchable.** A custom object with search turned off returns nothing however the query is written.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "How many objects does the RETURNING clause name, and which one holds the missing record?" | Each object gets min(2,000/n, 250), so more objects shrink every slice (Gotcha 2) | A narrower object list, or a per-object search for the one that matters |
| "Does the object's RETURNING clause have a WHERE or ORDER BY, and does it list at least one field?" | Only WHERE or ORDER BY lifts a single object from 250 to 2,000, and both need a field list (Gotcha 1) | A clause that actually raises the cap and still parses |
| "Did the reporter run the search as themselves, and do they have View All Data?" | Non-admins get permission filters on the results (Gotcha 3) | A reproduction in the affected user's context |
| "Is the object's Allow Search setting on, and has anyone searched it in the last 120 days?" | Search is off by default for new custom objects and can be switched off for idle ones (Gotcha 5) | `enableSearch` confirmed true in the object metadata |
| "How long can the text inside FIND {…} get when it is built from input?" | Over 4,000 characters, AND becomes OR; over 10,000, no rows (Gotcha 4) | A length guard on the search term before the call |
| "Were the records created or changed in bulk in the last few hours?" | New and changed data must be indexed before search can find it (Gotcha 6) | A re-test after indexing instead of a query rewrite |
| "Is the expectation 'every matching record' rather than 'best matches'?" | A statement tops out at 2,000 rows and LIMIT cannot raise it (Gotcha 7) | A decision to use SOQL or a report for exhaustive retrieval |

A proper configuration adds a stage-by-stage explanation of where the record was dropped and a guard for each stage, instead of a widened search that hides the same failure until the data grows.

---

## Core Concepts

### The stages, in order

| Stage | Limit | Source wording |
|---|---|---|
| Term matching | The engine looks for matches across a maximum of 2,000 records (API 28.0+) | SOSL Limits on Search Results |
| One object returned | 250 records; a WHERE or ORDER BY in the object's RETURNING clause raises it to 2,000 | same |
| Several objects returned | Each object returns up to min(2,000/n, 250): 2 objects → 250 each, 10 objects → 200 each | same |
| Statement total | 2,000 results (API 28.0+) including child objects, unless custom limits are set | Limits Quick Reference |
| Permission filter | View All Data sees everything returned; other users see only records they can access | SOSL Limits on Search Results |

UNVERIFIED (2026-10-19): the 250 single-object default, the WHERE/ORDER BY raise to 2,000, the min(2,000/n, 250) split, and the View All Data wording come from the SOQL and SOSL Reference page "SOSL Limits on Search Results", which is not in the Summer '26 PDF corpus; the corpus confirms only the 2,000-per-statement total from API 28.0 (Limits Quick Reference 264 L682-685) and that results are narrowed by access permissions and limits after the index search (LDV guide L171-174).

Result sets and order also vary by user and "can change throughout the day as records are added or removed from the index."

### What LIMIT does and does not do

`LIMIT n` sets a maximum up to 2,000, and the default is 2,000. The SOSL reference is explicit that "the LIMIT clause can't increase the maximum number of records returned." A statement-level LIMIT spreads results evenly across objects; a per-object LIMIT stops one object from using up the statement's budget. A LIMIT of 0 returns no records for that object.

### Search term length versus statement length

| What is measured | Threshold | Effect |
|---|---|---|
| `{SearchQuery}` text inside `FIND` | Over 4,000 characters | Logical operators are removed; AND defaults to OR |
| `{SearchQuery}` text inside `FIND` | Over 10,000 characters | No result rows are returned |
| Whole SOSL statement | 100,000 characters by default | Tied to the org's SOQL statement limit |

### Objects that cannot be found at all

The `enableSearch` field on a custom object (Allow Search in Setup) controls whether its records can be found by SOSL and Salesforce search. It defaults to off for new custom objects, and the Metadata API guide says searchability is disabled for custom objects that haven't been searched for more than 120 days.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- excerpt: objects/Project__c/Project__c.object-meta.xml — only the search-related element is shown;
     merge it into the retrieved file rather than deploying this fragment on its own. -->
<CustomObject xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableSearch>true</enableSearch>
</CustomObject>
```

---

## Common Patterns

### Raise the single-object cap from 250 to 2,000

```apex
// Capped at 250: one object, no WHERE or ORDER BY in its RETURNING clause
List<List<SObject>> capped = [FIND 'Acme*' IN NAME FIELDS RETURNING Account(Id, Name)];

// Up to 2,000: ORDER BY (or WHERE) inside the parentheses, with a field list
List<List<SObject>> raised = [
    FIND 'Acme*' IN NAME FIELDS
    RETURNING Account(Id, Name WHERE Industry = 'Technology' ORDER BY Name)
];
```

Adding `LIMIT 2000` instead does not lift the cap.

### Narrow to one object to protect a specific record

The reference's "Joe" example: a global search spreads the budget across object types, and the wanted record falls outside it. Searching one object gives that object the whole budget, and a more specific term (`Industrial Computing San Francisco` instead of `Industrial`) returns better matches under the same limits.

### Guard the search term length

```apex
public with sharing class AccountSearch {
    public class SearchTermTooLongException extends Exception {}

    public static List<List<SObject>> run(String term) {
        // The 4,000 / 10,000 thresholds apply to the FIND {term}, not the whole statement.
        if (term == null || term.length() > 4000) {
            throw new SearchTermTooLongException('Search term must be 1 to 4,000 characters.');
        }
        return [FIND :term IN NAME FIELDS RETURNING Account(Id, Name ORDER BY Name)];
    }
}
```

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Single-object search returns exactly 250 rows | Add WHERE or ORDER BY inside that object's RETURNING clause | Only these raise the single-object cap to 2,000 |
| One record missing from a multi-object search | Search that object alone, with a more specific term | Removes the min(2,000/n, 250) split |
| Nine or more objects in RETURNING | Cut the list or split into per-object searches | 2,000/n falls below 250 once n is over 8 |
| Admin sees the record, the user does not | Fix the user's access; never grant View All Data to fix search | Permission filters apply to non-admins |
| Custom object never appears in any search | Check `enableSearch` in the object metadata | Search is off by default for new custom objects |
| AND search returns far too much | Measure the FIND term length | Over 4,000 characters, AND defaults to OR |
| Need every matching row, ordered | Use SOQL or a report | SOSL tops out at 2,000 per statement |

---

## Recommended Workflow

1. Copy the statement and the symptom into `templates/sosl-search-result-limits-template.md`, and record n (objects in RETURNING) and whether the user has View All Data.
2. Reproduce as the affected user; if the record appears for an admin only, stop and treat it as an access problem.
3. Retrieve the object's metadata and confirm `<enableSearch>true</enableSearch>`; for newly loaded data, wait for indexing and re-test.
4. Map the symptom to a stage with the Core Concepts tables and apply the matching pattern (WHERE/ORDER BY, narrower object list, term length guard); `references/worked-example.md` walks one missing record through every stage.
5. Run `python3 skills/data/sosl-search-result-limits/scripts/check_sosl_search_result_limits.py --manifest-dir force-app/main/default` and resolve every ERROR; review the WARN lines.
6. Add an Apex test that uses `Test.setFixedSearchResults` for the search method and asserts on the record count the code expects, then re-run the real search as the affected user.

---

## Review Checklist

- [ ] The search was reproduced as the affected user, not only as an admin
- [ ] Single-object searches that need more than 250 rows have WHERE or ORDER BY (not just LIMIT) inside RETURNING, with a field list
- [ ] Multi-object searches account for min(2,000/n, 250); object count is not over 8 without reason
- [ ] The design does not expect more than 2,000 rows from one statement
- [ ] The FIND term is length-checked under 4,000 characters when built from input
- [ ] Searched custom objects have `enableSearch` set to true
- [ ] The checker reports no ERROR lines

---

## Salesforce-Specific Gotchas

Full write-ups are in `references/gotchas.md`:

| # | Gotcha |
|---|---|
| 1 | 250, not 2,000, is the single-object default, and the raising clause needs a field list |
| 2 | More objects means fewer results per object |
| 3 | Admins and standard users see different result sets |
| 4 | The FIND term length changes results with no error |
| 5 | Custom objects can be unsearchable by default or after 120 idle days |
| 6 | New and changed data is invisible until the search index catches up |
| 7 | LIMIT cannot raise any cap |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Stage-limit diagnosis | Which stage (scan, single-object cap, split, permission filter, term length, searchability, indexing) dropped the record |
| Remediated SOSL | RETURNING clause with WHERE/ORDER BY, a narrower object list, or a term length guard |
| Object metadata fix | `enableSearch` set to true on the custom object, when that was the cause |
| Checker output | `scripts/check_sosl_search_result_limits.py` findings |
| Filled worksheet | `templates/sosl-search-result-limits-template.md` |

---

## Related Skills

- `data/sosl-search-patterns` — how to write the search: SOSL vs SOQL, FIND syntax, search groups, injection safety
- `data/sosl-with-clauses` — WITH SNIPPET, WITH NETWORK, and the other WITH clauses
- `data/sosl-external-object-search-limits` — search limits that apply to external objects
- `data/soql-query-optimization` — when the requirement turns out to need exhaustive, ordered SOQL instead
- `apex/soql-fundamentals` — the SOQL side of query syntax

Templates: `templates/apex/BaseSelector.cls` is where a search method belongs so its caps and `USER_MODE` handling are reviewed in one place.
