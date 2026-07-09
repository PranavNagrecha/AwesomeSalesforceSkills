# LLM Anti-Patterns — SOQL FOR VIEW and FOR REFERENCE

Common mistakes AI coding assistants make when generating or advising on `FOR VIEW` /
`FOR REFERENCE`. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing FOR VIEW with FOR UPDATE

**What the LLM generates:** `SELECT ... FOR UPDATE` when the user asked to mark a record as
recently viewed, or claims `FOR VIEW` locks rows.

**Why it happens:** `FOR UPDATE` (row locking) is far more common in training data, and the two
clauses share the `FOR` keyword and sit adjacent in the grammar, so the model conflates them.

**Correct pattern:**

```sql
-- Marks the record viewed (writes LastViewedDate). Does NOT lock.
SELECT Id, Name FROM Account WHERE Id = :id LIMIT 1 FOR VIEW
```

**Detection hint:** the request mentions Recent Items / recently viewed but the output contains
`FOR UPDATE`, or the answer says `FOR VIEW` acquires a lock.

---

## Anti-Pattern 2: Manually updating LastViewedDate / inserting RecentlyViewed

**What the LLM generates:** an `Account a = ...; a.LastViewedDate = System.now(); update a;` or a
`new RecentlyViewed(...)` insert to fake "recently viewed."

**Why it happens:** the model reaches for the general "set a field and DML it" pattern instead of
the purpose-built SOQL clause it has seen rarely.

**Correct pattern:** `LastViewedDate` is not directly writable this way and `RecentlyViewed` is
populated by the platform; use the clause:

```sql
SELECT Id FROM Account WHERE Id = :id LIMIT 1 FOR VIEW
```

**Detection hint:** any direct assignment to `LastViewedDate` / `LastReferencedDate`, or a DML
insert/update against `RecentlyViewed`.

---

## Anti-Pattern 3: Adding the clause to bulk, async, or system-context queries

**What the LLM generates:** `FOR VIEW` on a query inside a `Database.Batchable`, `Schedulable`,
`Queueable`, trigger handler, or an unbounded `[SELECT ... FOR VIEW]` used to "warm" records.

**Why it happens:** the model treats the clause as a free enhancement ("make these show as
viewed") without surfacing the documented constraint that a logged-in user must actually be
viewing the records.

**Correct pattern:** omit the clause entirely in non-user-facing code. The docs: use it "only when
you are sure that the retrieved records will definitely be viewed by the logged-in user, else the
clause incorrectly updates the usage information for the records."

**Detection hint:** `FOR VIEW` / `FOR REFERENCE` appearing in a `.trigger`, or in a class
implementing `Database.Batchable` / `Schedulable` / `Queueable`, or on a query with no `WHERE`
and no `LIMIT`.

---

## Anti-Pattern 4: Inventing a combined `FOR VIEW FOR REFERENCE` syntax

**What the LLM generates:** a single query such as `SELECT Id FROM Contact LIMIT 1 FOR VIEW FOR
REFERENCE` (or `FOR VIEW, FOR REFERENCE`) after reading that the two are used "in conjunction."

**Why it happens:** the phrase "use the FOR VIEW clause in conjunction with the FOR REFERENCE
clause" reads like the two compose in one statement, and the model fills in a plausible-looking
combined form.

**Correct pattern:** the reference shows the clauses only individually and the grammar is an
alternation `{FOR VIEW | FOR REFERENCE}`. Choose one clause per query based on the real
interaction; do not ship a combined syntax the docs do not print.

```sql
SELECT Id FROM Contact WHERE Id = :id LIMIT 1 FOR VIEW   -- OR FOR REFERENCE, not both
```

**Detection hint:** both `FOR VIEW` and `FOR REFERENCE` tokens in the same `SELECT` statement.

---

## Anti-Pattern 5: Asserting a GA/Beta status or wrong grammar placement

**What the LLM generates:** "this GA feature, new in <release>…", or places the clause in the
wrong spot, e.g. before `WHERE` or between `SELECT` and `FROM`.

**Why it happens:** models pattern-fill maturity labels, and they under-train on the exact
position of a rarely used trailing clause.

**Correct pattern:** do not state a maturity the docs do not give (the SOQL/SOSL Reference marks
neither clause GA/Beta/deprecated and still documents them at Summer '26 / API 67.0). Place the
clause after `ORDER BY` / `LIMIT` / `OFFSET` and before `UPDATE {TRACKING|VIEWSTAT}` / `FOR
UPDATE`.

**Detection hint:** a "Generally Available"/"Beta" claim without a release-notes citation, or the
clause appearing anywhere other than the tail of the `SELECT` statement.

---

## Anti-Pattern 6: Ignoring the custom-object custom-tab prerequisite

**What the LLM generates:** confidently applies `FOR VIEW` to a custom object (`Widget__c`) and
tells the user it will work, with no mention of the tab requirement.

**Why it happens:** standard objects have `LastViewedDate` / `LastReferencedDate` out of the box,
so the model generalizes that all objects do.

**Correct pattern:** flag that a custom object needs a custom tab (visibility not required) before
the recency fields exist, or the query throws `No such column 'LastViewedDate'`.

**Detection hint:** guidance to use the clause on a `__c` object with no note about creating a
custom tab first.
