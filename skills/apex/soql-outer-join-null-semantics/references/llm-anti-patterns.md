# LLM Anti-Patterns — SOQL Outer-Join & Null Semantics

Common mistakes AI coding assistants make when generating or advising on SOQL relationship
queries and null handling. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating a relationship query as an inner join

**What the LLM generates:** guidance (or downstream code) that assumes `SELECT ..., Account.Name
FROM Case` returns only Cases that have an Account, and therefore skips a null check or an
explicit foreign-key filter.

**Why it happens:** in SQL that most training data is drawn from, `JOIN` defaults to an inner
join, so the model imports that mental model into SOQL, where relationship traversal is an outer
join.

**Correct pattern:**

```sql
-- Returns ALL Cases; parent columns are null where AccountId is null.
-- To exclude parent-less rows, filter the foreign key explicitly:
SELECT Id, Account.Name FROM Case WHERE AccountId != null
```

**Detection hint:** a claim that a relationship query "only returns records with a parent," or
generated code that reads a parent field without either a null guard or a foreign-key filter.

---

## Anti-Pattern 2: Using `WHERE Parent.Field = null` to mean "no parent"

**What the LLM generates:** `SELECT Id FROM Case WHERE Contact.LastName = null` (or similar)
presented as the way to find records with no related parent.

**Why it happens:** the model reasons that "the parent's field is null, therefore there is no
parent," missing the documented rule that the row is returned even when the parent doesn't
exist.

**Correct pattern:**

```sql
-- Records whose lookup is empty — filter the foreign-key Id, not the parent field:
SELECT Id FROM Case WHERE ContactId = null
```

**Detection hint:** a `= null` (or `!= null`) comparison whose left operand contains a dot
(relationship traversal), used to express presence/absence of a parent.

---

## Anti-Pattern 3: Comparing a Boolean field to null

**What the LLM generates:** `WHERE Active__c = null` to find "records with no value," or Apex
that treats a Boolean sObject field as if it can be `null`.

**Why it happens:** in most languages a boolean-typed variable can be null/None, so the model
assumes the same for a SOQL Boolean field.

**Correct pattern:**

```sql
-- Booleans are never null; compare to an explicit literal:
SELECT Id FROM Account WHERE Active__c = false   -- (WHERE Active__c = null is equivalent)
```

**Detection hint:** a `= null` / `!= null` comparison against a field that is a checkbox/Boolean
(often named `Is*`, `Has*`, `*Active*`, `*Enabled*`).

---

## Anti-Pattern 4: Dereferencing a parent relationship in Apex without a null guard

**What the LLM generates:** a loop like `for (Case c : [...]) { use(c.Account.Name); }` with no
`c.Account != null` check.

**Why it happens:** the model assumes that if `Account.Name` was in the SELECT list, the parent
object is always populated — ignoring that the outer join returns null-FK rows with a null parent
object.

**Correct pattern:**

```apex
for (Case c : [SELECT Id, Account.Name FROM Case]) {
    if (c.Account != null) {
        // safe to read c.Account.Name
    }
}
```

**Detection hint:** chained parent access (`x.Parent.Field`) on query results without a preceding
null check and without a foreign-key filter excluding null-FK rows.

---

## Anti-Pattern 5: Assuming OR / ORDER BY on a related field filters out null-FK rows

**What the LLM generates:** a query such as `WHERE LastName = 'Young' OR Account.Name = 'Quarry'`
described as returning only Contacts that have an Account, or an `ORDER BY Account.Name` described
as dropping Contacts with no Account.

**Why it happens:** the model treats the relationship term as an implicit "parent exists"
predicate.

**Correct pattern:** state that both `OR` and `ORDER BY` keep null-foreign-key rows, and add an
explicit `AccountId != null` term when parent-less rows must be excluded.

**Detection hint:** any explanation that an `OR`/`ORDER BY` involving a relationship field
excludes records whose foreign key is null.

---

## Anti-Pattern 6: Stamping a GA/Beta maturity or citing the wrong reference

**What the LLM generates:** "this outer-join behavior is a GA feature introduced in <release>," or
sourcing the claim from a blog instead of the SOQL and SOSL Reference.

**Why it happens:** models pattern-fill maturity labels and reach for popular secondary sources.

**Correct pattern:** describe it as standard, documented query-language behavior in the SOQL and
SOSL Reference and do not assert a GA/Beta/Pilot status the reference does not state.

**Detection hint:** a "Generally Available"/"Beta"/"since <release>" claim about relationship
null semantics, or a non-`developer.salesforce.com` citation for the behavior.

---

## Anti-Pattern 7: Generating SQL-style `IS NULL` / `IS NOT NULL`

**What the LLM generates:** `WHERE ActivityDate IS NOT NULL` or `WHERE AccountId IS NULL`, ported
straight from SQL into a SOQL string.

**Why it happens:** `IS NULL` / `IS NOT NULL` is the null idiom in nearly every SQL dialect the
model trained on, so it emits the same syntax for SOQL, which has no such operator.

**Correct pattern:**

```sql
-- SOQL compares to the null keyword directly; there is no IS NULL operator:
SELECT Id FROM Event WHERE ActivityDate != null
SELECT Id FROM Case  WHERE AccountId = null
```

**Detection hint:** the tokens `IS NULL` or `IS NOT NULL` anywhere in a generated SOQL string.
