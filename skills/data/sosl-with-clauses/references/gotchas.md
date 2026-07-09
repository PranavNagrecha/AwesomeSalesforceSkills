# Gotchas — SOSL WITH Clauses

Non-obvious Salesforce platform behaviors that cause real production problems when using SOSL
WITH clauses.

## Gotcha 1: The WITH clause order is fixed and enforced

**What happens:** a query with two or more valid WITH clauses fails to parse because they are in
the wrong sequence.

**When it occurs:** you order the clauses freely (as you would SOQL `WHERE`/`ORDER BY`). SOSL
requires one fixed order: `DivisionFilter → DATA CATEGORY → SNIPPET → NETWORK → PricebookId →
METADATA → HIGHLIGHT → SPELL_CORRECTION`, followed by `LIMIT`, then `UPDATE`.

**How to avoid:** assemble the clauses in canonical order every time; use the ordered skeleton in
`templates/sosl-with-clauses-template.md` and lint with `scripts/check_sosl_with_clauses.py`.

---

## Gotcha 2: Wildcards suppress snippets and highlights

**What happens:** the query returns rows, but `WITH SNIPPET` excerpts and `WITH HIGHLIGHT`
markup are missing — with no error.

**When it occurs:** the `FIND` term contains a `*` or `?` wildcard. Snippets aren't displayed and
search terms containing a wildcard aren't highlighted.

**How to avoid:** decide whether the search needs wildcard breadth or presentation. If you need
excerpts/highlighting, use complete terms; if you need wildcards, don't wire the UI to expect
snippet/highlight output.

---

## Gotcha 3: Snippets only render at 20 or fewer results per page

**What happens:** snippets show up in a small test result set but disappear once the search
returns more hits.

**When it occurs:** more than 20 results are returned on a page — snippets are only displayed
when 20 or fewer results are returned on a page.

**How to avoid:** page or `LIMIT` the query so a page holds ≤20 rows when the excerpt matters,
and don't treat a missing snippet on a large result set as a bug.

---

## Gotcha 4: Clauses are silently gated by object and API version

**What happens:** a WITH clause has no effect and produces no error, so it looks like it "isn't
working."

**When it occurs:** the clause is used on an unsupported object (e.g. `SNIPPET`/`HIGHLIGHT`/`DATA
CATEGORY` on entities that don't support them) or under an API version below the floor
(`DATA CATEGORY` 18.0, `SNIPPET` 32.0, `HIGHLIGHT` 39.0 / 40.0 for custom, `SPELL_CORRECTION`
40.0).

**How to avoid:** confirm each clause's supported objects and the issuing context's `apiVersion`
before relying on it; drop clauses the target objects don't support.

---

## Gotcha 5: WITH NETWORK only scopes users and feeds

**What happens:** a site-scoped search still returns records from other Experience Cloud sites or
internal company data, even though `WITH NETWORK` is present.

**When it occurs:** the `RETURNING` list includes objects other than `User` and feeds. For those
objects the network filter is ignored, and matches include all sites plus internal data.
Separately, you can't run scoped and unscoped searches in the same query.

**How to avoid:** only rely on `WITH NETWORK` to scope `User` and feed results; for groups or
topics, filter with a `WHERE NetworkId = ...` instead, and don't combine scoped and unscoped
objects in one statement.

---

## Gotcha 6: SNIPPET target_length out of range silently defaults to 300

**What happens:** you request a 40-character or 5,000-character excerpt and get ~300 characters
instead, with no warning.

**When it occurs:** `target_length` is outside the valid 50–1,000 range (or otherwise invalid) —
the length defaults to 300.

**How to avoid:** keep `target_length` within 50–1,000; if the UI needs a specific excerpt size,
verify the returned length rather than assuming your requested value was honored.
