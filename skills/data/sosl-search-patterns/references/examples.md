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

## Anti-Pattern: LIKE Everywhere

**What practitioners do:** They write several SOQL queries with `LIKE '%term%'` for every object and call it search.

**What goes wrong:** Performance, maintainability, and user experience all degrade.

**Correct approach:** Use SOSL for true search experiences and SOQL for precise object-specific filtering.
