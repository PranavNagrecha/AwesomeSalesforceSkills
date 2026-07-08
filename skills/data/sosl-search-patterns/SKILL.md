---
name: sosl-search-patterns
description: "Use when choosing or implementing SOSL for cross-object or full-text search, especially around SOSL vs SOQL, search groups, result shaping, and injection-safe dynamic search. Triggers: 'SOSL', 'FIND clause', 'cross object search', 'Search.query', 'SOSL injection'. NOT for structured record retrieval where ordinary SOQL filters are the right tool."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - User Experience
tags:
  - sosl
  - search-query
  - find-clause
  - search-layouts
  - injection
  - list-view
  - returning-clause
triggers:
  - "when should I use SOSL instead of SOQL"
  - "cross object search in Salesforce Apex"
  - "Search.query SOSL injection prevention"
  - "FIND clause wildcard behavior"
  - "search layouts for global search style results"
  - "search query isn't working"
  - "scope a SOSL search to a single list view"
  - "search within a Salesforce list view using SOSL"
  - "escape reserved characters in a SOSL FIND clause"
  - "escape a special character in a SOQL LIKE query"
  - "combine AND, OR, and AND NOT in a SOSL FIND clause"
  - "paginate SOSL results with OFFSET inside a RETURNING clause"
  - "filter or sort one object's slice in a SOSL RETURNING clause"
inputs:
  - "search use case and whether it spans one object or many"
  - "expected result volume and UI shape"
  - "whether the query is static SOSL or dynamic `Search.query`"
outputs:
  - "SOSL versus SOQL recommendation"
  - "review findings for search performance and injection risk"
  - "search pattern for result shaping and object grouping"
dependencies: []
version: 1.4.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# Sosl Search Patterns

Use this skill when the user experience is search, discovery, or typeahead rather than a structured filter form. SOSL is the right tool when the system needs full-text style search across fields or across multiple objects, and it becomes the wrong tool when the query is actually a precise relational filter that SOQL can express cleanly.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the use case global or cross-object search, or is it really one-object filtering?
- Does the UI need a few best matches quickly, or does it need exhaustive reporting-style results?
- Will the query be static SOSL with bind variables, or dynamic search text assembled in code?

---

## Core Concepts

### SOSL Is For Search, SOQL Is For Structured Retrieval

Use SOSL when the user knows a word, phrase, or partial value and wants matching records across one or more objects. Use SOQL when the app already knows the object and wants relational filters, sorting, and explicit field constraints.

### Search Groups And Result Shape Matter

SOSL can search different field groups and return results grouped by object. That makes it a strong fit for search experiences but a poor fit for workflows that expect one neat tabular result set like SOQL.

### Injection Safety Changes With Dynamic Search

Static SOSL with bind variables is the clean path. Dynamic `Search.query` usage needs careful input handling so search strings are not built unsafely from user input.

### Search UX Needs Limits And Relevance Discipline

Search is a user-experience feature first. Teams should design for top matches, sensible caps, and clear object grouping instead of flooding the page with everything the platform can return.

### A Search Can Be Scoped To One List View

The optional `USING ListView=<Name>` clause narrows a `RETURNING` object to the records inside a single named list view instead of the whole object. Salesforce searches only the first 2,000 records of that list view, using the sort order the user has set on the view, so the clause is a scoping decision — the list view defines which records are eligible before the `FIND` text is matched. Only one list view can be specified, the clause is available in API version 41 or later, and it works in SOAP API, REST API, and Apex.

### `RETURNING` Shapes Each Object's Result Slice

`USING ListView` is one of several sub-clauses `RETURNING` can attach to an object; the full per-object shape is `ObjectTypeName(FieldList WHERE ... USING ListView=... ORDER BY ... LIMIT n OFFSET n)`, and the sub-clauses must appear in that order, with at least one field present in `FieldList` before any of them. `FieldList` is a comma-separated list of one or more fields; relationship fields (e.g. `Account.Owner.Name`) follow SOQL's format and depth rules. The per-object `WHERE` filters matched rows by field value — distinct from the `FIND` term, which decides what matched — and `ORDER BY` sorts that object's slice. Two row caps bite: with no `LIMIT` each object returns at most 2,000 rows (API v28+), and an explicit `LIMIT n` still tops out at 2,000, so SOSL is not a bulk-extraction tool. `OFFSET n` pages the result set but is legal **only when the search returns a single object** and must be the last sub-clause. When more than one object is named, each `ObjectTypeName` must be distinct. (A separate class of object types — external objects, articles, documents, feed comments, feed items, files, products, and solutions — is invisible unless named explicitly in `RETURNING`; see gotchas.)

### The `FIND` Search Query Has Operators, A Fixed Precedence, And Size Cliffs

A `FIND` search query can combine terms with `AND`, `OR`, and `AND NOT` plus parentheses. Mixed operators are not read left to right: precedence is fixed as parentheses, then `AND`/`AND NOT` (evaluated right to left), then `OR` — so group intent with explicit parentheses. To match the literal words `and`, `or`, or `and not`, wrap them in double quotes. Text searches are case-insensitive, and the clause does not evaluate run-time expressions (no macros, functions, or regular expressions). Two length cliffs turn into silent production bugs when the search text is assembled from user input: past 4,000 characters the logical operators are removed (results broaden as `AND` constraints drop away), and past 10,000 characters no result rows come back at all. The search value is delimited by curly braces in the Query Editor and API, but by single quotes in Apex.

### Reserved Characters And Escaping Differ Between SOQL And SOSL

The two languages do not share a reserved-character set. SOQL reserves only the single quote (`'`) and the backslash (`\`); both must be preceded by a backslash when they appear as literals inside a quoted string, and the backslash is SOQL's escape character for a fixed table of sequences (`\n`, `\r`, `\t`, `\b`, `\f`, `\"`, `\'`, `\\`, `\uXXXX`, plus `\_` and `\%` that apply only inside `LIKE`). SOSL's `FIND` clause reserves a much larger set — `? & | ! { } [ ] ( ) ^ ~ * : \ " ' + -` — because that punctuation drives its Boolean and proximity syntax, and escaping is required even when the search string is wrapped in double quotes. Getting this wrong is not silently tolerated: an unescaped reserved character, or a backslash used outside a defined escape sequence, raises an error rather than matching literally.

---

## Common Patterns

### Cross-Object Typeahead

**When to use:** Users search people, accounts, and cases from one entry point.

**How it works:** Use SOSL with a constrained result size and explicit object-returning sections.

**Why not the alternative:** A chain of object-specific SOQL queries recreates search badly and wastes queries.

### Object-Known Fallback To SOQL

**When to use:** The UI starts broad, then narrows to one chosen object or exact filter state.

**How it works:** Use SOSL for discovery, then switch to SOQL once the app knows the object and precise constraints.

### Static SOSL With Bind Variables

**When to use:** Apex needs a safe search pattern without building raw query text.

**How it works:** Bind the search term into SOSL directly instead of concatenating a `Search.query` string.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| User needs keyword search across multiple objects | SOSL | Built for search-style discovery |
| Query targets one object with precise filters | SOQL | Better relational filtering and control |
| Search term comes from user input in Apex | Static SOSL or carefully sanitized dynamic SOSL | Reduces injection and syntax risk |
| UI needs controlled display fields and object grouping | SOSL plus shaped result mapping | Better fit than improvised SOQL fan-out |
| Search must be limited to the records in one saved list view | SOSL with `USING ListView=<Name>` | Reuses the org's own view definition instead of duplicating its filter (API v41+) |
| Search combines `AND`, `OR`, and `AND NOT` | Group terms with explicit parentheses | Precedence is fixed (parentheses, then `AND`/`AND NOT` right-to-left, then `OR`), so grouping makes intent unambiguous |
| One object's slice of a multi-object search needs its own filter, sort, or paging | Per-object `WHERE` / `ORDER BY` / `LIMIT` inside `RETURNING` (`OFFSET` single-object only) | Shapes that object independently of the `FIND` term without post-filtering in Apex |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] SOSL is being used for a search problem, not a structured query problem.
- [ ] Dynamic search text is not built unsafely from user input.
- [ ] Result size and object grouping match the UI need.
- [ ] Search layouts or display-field choices are intentional.
- [ ] The design switches to SOQL once the workflow becomes object-specific.
- [ ] Wildcard and relevance expectations are documented for the experience.
- [ ] Reserved characters are escaped for the right language — `'` and `\` in SOQL, SOSL's larger `FIND` set — before a literal search term is run.
- [ ] Mixed `FIND` operators are grouped with explicit parentheses, and an assembled search string stays well under the 4,000-character operator-stripping cliff (and the 10,000-character zero-row cliff).
- [ ] Each `RETURNING` object's `WHERE` / `ORDER BY` / `LIMIT` / `OFFSET` is intentional, `OFFSET` is used only on single-object searches, and no per-object `LIMIT` assumes more than 2,000 rows.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **SOSL returns grouped results, not one flat table** - consumers must map the response intentionally.
2. **Dynamic `Search.query` is the risky path** - string-built search text creates avoidable injection and syntax issues.
3. **Search experiences need display discipline** - technically valid results can still feel unusable in the UI.
4. **Many "search" problems are really SOQL problems** - picking SOSL too early can complicate exact filtering work.
5. **`USING ListView` scopes a search to one saved list view** - it reuses the view's own filter and sort instead of the whole object and requires API version 41 or later.
6. **A long `FIND` query silently changes meaning or returns nothing** - past 4,000 characters the logical operators are removed (results broaden); past 10,000 characters no rows return.
7. **Some object types are invisible unless named in `RETURNING`** - external objects, articles, documents, feed comments/items, files, products, and solutions are skipped otherwise.
8. **`OFFSET` is single-object only; each object caps at 2,000 rows** - `OFFSET` must be the last sub-clause and errors on multi-object searches, so SOSL can't bulk-extract.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Search decision | Recommendation for SOSL versus SOQL |
| Search review | Findings on injection safety, result shape, and UI fit |
| SOSL pattern | Safe cross-object search scaffold with object grouping |

---

## Related Skills

- `apex/soql-security` - use when the real problem is query safety and record access enforcement rather than search design.
- `lwc/lifecycle-hooks` - use when the search UI behavior is the main issue after the query choice is correct.
- `data/roll-up-summary-alternatives` - use when the requirement is summary computation rather than search.
