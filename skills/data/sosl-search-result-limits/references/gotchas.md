# Gotchas — SOSL Search Result Limits

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: 250, Not 2,000, Is the Single-Object Default

**What happens:** A single-object SOSL search returns exactly 250 records even though thousands match. No error is raised.

**When it occurs:** The statement names one object and that object's RETURNING clause has no WHERE and no ORDER BY. The reference: "If you query one object only, a maximum of 250 records are returned. To return up to 2,000 results, include either the WHERE clause or ORDER BY clause." Teams that try to lift the cap with `LIMIT 2000` keep getting 250, and teams that write `RETURNING Account(ORDER BY Name)` get a syntax error, because WHERE, ORDER BY, LIMIT, and OFFSET each require at least one field in the field list.

**How to avoid:** Put WHERE or ORDER BY inside the parentheses after a field list: `RETURNING Account(Id, Name ORDER BY Name)`.

---

## Gotcha 2: More Objects Means Fewer Results per Object

**What happens:** Widening a search to more objects returns fewer rows for each of them.

**When it occurs:** Each object returns up to min(2,000/n, 250). The reference's examples: 2 objects → 250 each; 10 objects → 200 each. Past eight objects every addition lowers every object's cap (16 objects → 125). The 2,000 statement total includes results from child objects.

**How to avoid:** Keep the RETURNING list as short as the requirement allows. To protect one object's results, search it alone.

---

## Gotcha 3: Admins and Standard Users See Different Result Sets

**What happens:** The admin investigating a "missing record" report finds the record; the reporting user still cannot.

**When it occurs:** "Admins (users with the View All Data permission) see the full set of results returned. For all other users, SOSL applies user permission filters." The LDV guide describes the same order: the index is searched first, then results are narrowed by access permissions, search limits, and other filters, and once the result set reaches a predetermined size the remaining records are discarded.

**How to avoid:** Reproduce as the affected user. If the record vanishes only for non-admins, fix sharing or field access; do not grant View All Data to make search work.

---

## Gotcha 4: The FIND Term Length Changes Results With No Error

**What happens:** A dynamically built search sometimes returns nothing, or an AND search returns far too much.

**When it occurs:** The text inside `FIND {…}` crosses a threshold. Over 4,000 characters, logical operators are removed and "the AND operator in a statement with a SearchQuery that's 4,001 characters defaults to the OR operator." Over 10,000 characters, no rows are returned. These thresholds apply to the search term; the whole SOSL statement has a separate default limit of 100,000 characters tied to the org's SOQL statement limit. Measuring `String.length()` of the entire statement mixes the two up.

**How to avoid:** Validate the term (the bound value or the text between the braces) before the search runs, and reject anything over 4,000 characters.

---

## Gotcha 5: Custom Objects Can Be Unsearchable by Default, or After 120 Idle Days

**What happens:** Records of a custom object never appear in SOSL or global search, however the query is written.

**When it occurs:** The CustomObject `enableSearch` field ("Allow Search" in Setup) is false. The Metadata API guide says search is disabled by default for new custom objects, and that searchability is disabled for custom objects that haven't been searched for more than 120 days.

**How to avoid:** Retrieve the object and check `<enableSearch>true</enableSearch>` before debugging limits. Conversely, the LDV guide advises not indexing custom objects that you don't want searched, because they add to search crowding.

---

## Gotcha 6: New and Changed Data Is Invisible Until the Index Catches Up

**What happens:** Records loaded or edited a few minutes ago do not appear in search results; an hour later they do.

**When it occurs:** Data must be indexed before it can be searched. The LDV guide says that after a searchable record is created or updated "it could take about 15 minutes or more for the updated text to become searchable," and longer after large data volumes are added or changed.

**How to avoid:** Re-test after indexing before changing the query. For integrations that create a record and immediately look it up, query by Id or external ID with SOQL instead of searching.

---

## Gotcha 7: LIMIT Cannot Raise Any Cap

**What happens:** A developer adds `LIMIT 2000` to a statement or object clause expecting more rows, and nothing changes.

**When it occurs:** The LIMIT reference: "The LIMIT clause can't increase the maximum number of records returned." A statement-level LIMIT also distributes results evenly across objects, so `LIMIT 20` over Account and Contact returns 10 of each even when one object had more matches.

**How to avoid:** Use LIMIT only to lower or apportion results; use a per-object LIMIT to stop one object from consuming the statement's budget. To lift a single-object cap, use WHERE or ORDER BY.

---

## Gotcha 8: Unit Tests Cannot Reproduce the Caps

**What happens:** A test asserts that a search returns the expected records and passes, while production still truncates.

**When it occurs:** In a test method, SOSL returns an empty list unless `Test.setFixedSearchResults` defines the record Ids to return; WHERE and LIMIT clauses are then applied to that fixed list. The engine's scan and per-object caps are not exercised.

**How to avoid:** Use fixed results to test the code path, and verify the real caps with the real search as an affected user in a sandbox with production-like data.
