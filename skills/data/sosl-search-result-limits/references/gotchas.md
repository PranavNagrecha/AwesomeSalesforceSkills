# Gotchas — SOSL Search Result Limits

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The single-object default is 250, not 2,000

**What happens:** a single-object SOSL search returns exactly 250 records and no more, even
though thousands match the term. No error is raised.

**When it occurs:** the statement targets one object and the object's `RETURNING` parentheses
contain no `WHERE`, `ORDER BY`, or custom `LIMIT`. Per the docs, "If you query one object
only, a maximum of 250 records are returned." Developers routinely assume the 2,000 statement
ceiling is the default and never add a clause.

**How to avoid:** add a `WHERE` filter or an `ORDER BY` inside the object's parentheses to
raise the cap to 2,000 — "To return up to 2,000 results, include either the WHERE clause or
ORDER BY clause." If you genuinely need more than 2,000, redesign around SOQL/reporting; SOSL
tops out at 2,000 total per statement.

---

## Gotcha 2: More objects means fewer results per object

**What happens:** widening a search to more objects returns fewer rows for each of them, so
recently created records in a heavily searched object start disappearing from results.

**When it occurs:** any multi-object search where the object count `n` exceeds 8. Each object
returns min(2000/n, 250): with 2 objects each gets 250, but with 10 objects each gets only
200 (2000/10), and with 16 objects only 125. "This limit includes results from child
objects," so nested `RETURNING` relationships count toward the same budget.

**How to avoid:** keep the object list as small as the requirement allows. To protect a
specific object's results, scope the search to just that object — the documented "Joe" remedy —
which removes the division entirely and restores the single-object budget.

---

## Gotcha 3: Admins and standard users see different result counts

**What happens:** a "missing record" bug cannot be reproduced by the admin investigating it —
the admin's search returns the record fine — yet the standard user still cannot find it.

**When it occurs:** the running user lacks View All Data. "Admins (users with the View All
Data permission) see the full set of results returned. For all other users, SOSL applies user
permission filters." The engine matches the record, then removes it from the standard user's
result set because sharing/FLS/CRUD hide it. This filtering stacks on top of the numeric caps.

**How to avoid:** always reproduce a missing-record report as the affected user, not as an
admin. If the record only vanishes for non-admins, the cause is record access (sharing rules,
role hierarchy, FLS), not a result cap — fix the access, not the query.

---

## Gotcha 4: Dynamic SearchQuery length silently changes results

**What happens:** a dynamically built `Search.query` sometimes returns nothing, and sometimes
an `AND` search returns far too many records — with no exception and no debug-log warning.

**When it occurs:** the `SearchQuery` string crosses a length threshold. "If SearchQuery is
longer than 4,000 characters, any logical operators are removed" (so `AND` effectively
broadens the match), and "If the SearchQuery string is longer than 10,000 characters, no
result rows are returned." The overall SOSL statement also has a default 100,000-character
limit, "tied to the SOQL statement character limit defined for your org."

**How to avoid:** measure `String.length()` on the search string before calling
`Search.query` and reject it above a safe bound comfortably under 4,000 characters. Never rely
on the platform to raise an error at these thresholds — it does not.
