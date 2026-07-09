# Examples - Sosl Search Patterns

## Example 1: Static SOSL With Bind Variable

**Context:** A service must search Accounts and Contacts from a user-entered keyword.

**Problem:** The team wants to build raw search text with concatenation.

**Solution:**

```apex
String searchTerm = 'Acme*';
List<List<SObject>> results = [
    FIND :searchTerm
    IN ALL FIELDS
    RETURNING
        Account(Id, Name LIMIT 5),
        Contact(Id, Name LIMIT 5)
];
```

**Why it works:** The query stays compact, cross-object, and safer than string-built `Search.query` text.

---

## Example 2: Discovery First, SOQL Second

**Context:** Users search broadly, then open a specific object view with more exact filters.

**Problem:** One query surface is trying to do both discovery and structured retrieval.

**Solution:** Use SOSL for the first discovery step, then switch to SOQL once the object and exact filters are known.

**Why it works:** Each query language handles the part of the experience it is best at.

---

## Example 3: Scope A Search To One List View

**Context:** A support console should let agents search only the Accounts inside the curated "MVP Customers" list view, not every Account in the org.

**Problem:** The team is about to re-implement the list view's filter criteria as a SOQL `WHERE` clause, which will drift as admins edit the view.

**Solution:**

```apex
String searchTerm = 'Acme*';
List<List<SObject>> results = [
    FIND :searchTerm
    IN ALL FIELDS
    RETURNING Account(Id, Name USING ListView=MVPCustomers)
];
```

**Why it works:** The search reuses the view definition the org already maintains instead of duplicating its filter, and requires API version 41 or later (SOAP API, REST API, and Apex).

---

## Example 4: Escape Reserved Characters In A SOSL `FIND`

**Context:** A feature searches for a literal term that contains punctuation, such as `{1+1}:2`.

**Problem:** SOSL reads that punctuation as Boolean or proximity operators, so the naive query errors or over-matches — and wrapping the term in double quotes does not exempt it.

**Solution:** precede each of SOSL's reserved characters (`? & | ! { } [ ] ( ) ^ ~ * : \ " ' + -`) with a backslash, even inside double quotes:

```apex
// Search for the literal text {1+1}:2
List<List<SObject>> results = [FIND '\{1\+1\}\:2' IN ALL FIELDS RETURNING Case(Id, Subject)];
```

**Why it works:** Each reserved character is escaped so the search engine treats it as literal text. SOSL's reserved set is larger than SOQL's two characters (`'` and `\`), so escaping logic cannot be shared between the two languages.

---

## Example 5: Combine `FIND` Operators With Explicit Parentheses

**Context:** A search should match Acme accounts that mention either "renewal" or "expansion", but never "churn".

**Problem:** The team writes `FIND 'Acme AND renewal OR expansion AND NOT churn'` assuming left-to-right evaluation, but the ungrouped `OR` binds more loosely than intended, so the result set is wrong.

**Solution:** Group the intent with parentheses so it does not depend on precedence:

```apex
List<List<SObject>> results = [
    FIND 'Acme AND (renewal OR expansion) AND NOT churn'
    IN ALL FIELDS
    RETURNING Account(Id, Name)
];
```

**Why it works:** Parentheses are evaluated first, so the `OR` is confined to the renewal/expansion clause. To search for the literal words `and`, `or`, or `and not` instead of treating them as operators, wrap those words in double quotes.

---

## Example 6: Filter, Sort, And Page One Object's Slice Inside `RETURNING`

**Context:** A cross-object search returns Accounts and Cases, but the Case slice should show only open cases, newest first.

**Problem:** The team plans to fetch everything and filter/sort in Apex, which wastes rows against the 2,000-per-object cap and can't page server-side.

**Solution:** Push each object's `WHERE`, `ORDER BY`, and `LIMIT` into `RETURNING`:

```apex
String searchTerm = 'Acme*';
List<List<SObject>> hits = [
    FIND :searchTerm
    IN ALL FIELDS
    RETURNING
        Account(Id, Name ORDER BY Name LIMIT 10),
        Case(Id, Subject WHERE IsClosed = false ORDER BY CreatedDate DESC LIMIT 10)
];
```

**Why it works:** Per-object `WHERE` filters matched rows by field value (distinct from the `FIND` term), and `ORDER BY`/`LIMIT` shape each slice server-side. To page, add `OFFSET` — but only on a single-object search (`RETURNING Account(Id, Name ORDER BY Name LIMIT 10 OFFSET 10)`), where it must be the last sub-clause in the order `FieldList` → `WHERE` → `USING ListView` → `ORDER BY` → `LIMIT` → `OFFSET`.

---

## Anti-Pattern: LIKE Everywhere

**What practitioners do:** They write several SOQL queries with `LIKE '%term%'` for every object and call it search.

**What goes wrong:** Performance, maintainability, and user experience all degrade.

**Correct approach:** Use SOSL for true search experiences and SOQL for precise object-specific filtering.
