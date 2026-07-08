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

## Anti-Pattern: LIKE Everywhere

**What practitioners do:** They write several SOQL queries with `LIKE '%term%'` for every object and call it search.

**What goes wrong:** Performance, maintainability, and user experience all degrade.

**Correct approach:** Use SOSL for true search experiences and SOQL for precise object-specific filtering.
