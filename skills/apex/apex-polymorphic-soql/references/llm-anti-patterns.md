# LLM Anti-Patterns — Apex Polymorphic SOQL

Common mistakes AI coding assistants make querying polymorphic fields.

## Anti-Pattern 1: Accessing type-specific field without TYPEOF

**What the LLM generates:**

```
SELECT Id, Subject, What.Industry FROM Task
```

**Why it happens:** Model treats polymorphic lookup as normal.

**Correct pattern:**

```
SELECT Id, Subject,
  TYPEOF What
    WHEN Account THEN Industry
    WHEN Opportunity THEN StageName
  END
FROM Task

Industry only exists on Account; querying it flat fails or returns null.
```

**Detection hint:** SOQL with polymorphic traversal (What., Who., LinkedEntity.) to a field that isn't on the common parent.

---

## Anti-Pattern 2: Filtering by Type without a selective filter

**What the LLM generates:**

```
SELECT Id FROM Task WHERE What.Type = 'Account'
```

**Why it happens:** Model treats Type as an index.

**Correct pattern:**

```
What.Type is a non-selective filter. Pair with a selective filter:
SELECT Id FROM Task
WHERE What.Type = 'Account'
  AND CreatedDate = LAST_N_DAYS:7

Without a selective condition, large orgs hit a non-selective-query
exception.
```

**Detection hint:** SOQL on Task/Event filtering only by `What.Type` or `Who.Type` with no time or Id constraint.

---

## Anti-Pattern 3: TYPEOF inside a subquery

**What the LLM generates:**

```
SELECT Id, (SELECT TYPEOF What WHEN Account THEN Name END FROM Tasks) FROM Opportunity
```

**Why it happens:** Model doesn't know the restriction.

**Correct pattern:**

```
TYPEOF is not supported in inner subqueries. Query the child collection
flat (What.Name at most) and do per-type resolution in Apex. Or query
Tasks as a top-level query in a second call.
```

**Detection hint:** SOQL with nested subquery containing `TYPEOF`.

---

## Anti-Pattern 4: Missing ELSE branch in TYPEOF

**What the LLM generates:**

```
SELECT Id, TYPEOF What WHEN Account THEN Name END FROM Task
```

**Why it happens:** Model writes partial coverage.

**Correct pattern:**

```
Add explicit ELSE to catch types you didn't enumerate:
TYPEOF What
  WHEN Account THEN Name
  WHEN Opportunity THEN Amount
  ELSE Name
END

Unmapped types return null without ELSE; if the field list doesn't
share a base field, the query may error.
```

**Detection hint:** TYPEOF block without ELSE branch.

---

## Anti-Pattern 5: Hardcoding the set of target types

**What the LLM generates:** Apex with `if (obj instanceof Account) ... else if (obj instanceof Opportunity)` and assuming those are the only two.

**Why it happens:** Model derives from the immediate TYPEOF query.

**Correct pattern:**

```
Use Schema introspection to get the dynamic set:
List<SObjectType> targets =
  Task.WhatId.getDescribe().getReferenceTo();

Iterate and dispatch via getSObjectType() on each result record. New
object types become eligible when admins enable Activities on them —
hardcoded handlers miss them silently.
```

**Detection hint:** Apex with `instanceof` dispatch on a polymorphic result enumerating only 2–3 types.
