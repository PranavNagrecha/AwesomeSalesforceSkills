# LLM Anti-Patterns — Lookup and Relationship Design

Common mistakes AI coding assistants make when designing object relationships.

## Anti-Pattern 1: Defaulting to Master-Detail "for cascade delete"

**What the LLM generates:** Master-detail recommended whenever deletion cascade is mentioned, without examining sharing implications.

**Why it happens:** Model optimizes for the single mentioned requirement.

**Correct pattern:**

```
Master-detail changes sharing semantics — child inherits from parent.
If children need independent sharing (different owners, separate
visibility), lookup with "Clear field on delete" or restrict-delete
is correct. Cascade is achievable with lookup + Apex trigger when needed.
```

**Detection hint:** Data-model change converting a loosely-related child object from lookup to master-detail with no sharing justification.

---

## Anti-Pattern 2: Adding roll-up summary requirements and forcing MD conversion

**What the LLM generates:** Proposes converting existing lookup to master-detail solely to enable roll-up.

**Why it happens:** Model knows roll-ups require master-detail; misses alternatives.

**Correct pattern:**

```
Declarative Lookup Rollup Summaries (DLRS, an unmanaged package) or a
custom Apex rollup framework enables rollups on lookup relationships
without sacrificing the child's independent sharing. Preserve existing
data model before forcing conversion.
```

**Detection hint:** Change proposals converting lookup → MD with "enable roll-up" as rationale.

---

## Anti-Pattern 3: Using a standard polymorphic lookup on a custom object

**What the LLM generates:** Suggests a polymorphic lookup on a custom object "like Task.WhatId."

**Why it happens:** Model overgeneralizes the polymorphic pattern.

**Correct pattern:**

```
Polymorphic lookups are only supported on specific standard objects
(Task, Event, ContentDocumentLink, FeedItem, etc.). Custom objects
need two lookups + a type-discriminator picklist, or a single lookup
to a super-object that has sub-type records.
```

**Detection hint:** Custom object metadata requesting a relationship to multiple target objects.

---

## Anti-Pattern 4: Ignoring the 40-relationship limit per object

**What the LLM generates:** Adds a 41st lookup field with no acknowledgment.

**Why it happens:** Model focuses on the immediate need and doesn't audit existing fields.

**Correct pattern:**

```
Hard limit: 40 relationship fields per object. Before adding a
lookup, count existing relationships. If near limit, consolidate
via a related junction object or an intermediate record pattern.
Reaching 40 is a design smell — the object is doing too much.
```

**Detection hint:** Object metadata with 35+ lookup fields receiving more.

---

## Anti-Pattern 5: Building five-level SOQL traversal

**What the LLM generates:** `SELECT Parent.Parent.Parent.Parent.Parent.Name FROM Child`.

**Why it happens:** Model treats SOQL like SQL with unlimited joins.

**Correct pattern:**

```
SOQL relationship queries cap at 5 levels of parent relationships and
1 level of child (subquery). Deeper traversal must flatten via formula
fields, denormalization, or multiple queries. Build relationships with
flat access in mind.
```

**Detection hint:** SOQL with 5+ dot-traversals in SELECT or WHERE.
