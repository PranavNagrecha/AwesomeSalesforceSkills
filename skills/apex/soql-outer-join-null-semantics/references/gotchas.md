# Gotchas — SOQL Outer-Join & Null Semantics

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `WHERE Parent.Field = null` can't distinguish "no lookup" from "deleted parent"

**What happens:** a filter written to mean "records with no parent" returns more rows than
expected — it also picks up records whose parent record does not exist.

**When it occurs:** you test a traversed parent field for null (`WHERE Contact.LastName = null`)
instead of the foreign-key field. The reference states the record "is returned even if the
parent does not exist," so both empty-lookup rows and unresolvable-parent rows come back.

**How to avoid:** filter the foreign-key Id column on the base object (`WHERE ContactId = null`),
which tests the scalar field directly and means "unset" precisely.

---

## Gotcha 2: A Boolean `= null` filter returns every `false` row, not an empty set

**What happens:** `WHERE Flag__c = null` returns all the records where the checkbox is unchecked,
surprising anyone who expected it to match "no value."

**When it occurs:** any time a Boolean/checkbox field is compared to null. "Boolean fields never
contain null values"; the platform evaluates `= null` as `= false` and `!= null` as `= true`.

**How to avoid:** compare Boolean fields to an explicit `true` / `false`. Never use `= null` as a
proxy for "unset" on a Boolean.

---

## Gotcha 3: Reading a parent field in Apex after a relationship query can throw NPE

**What happens:** a loop over query results throws `System.NullPointerException` on some records
even though the query ran fine.

**When it occurs:** the query is an outer join, so rows with a null foreign key come back with the
parent relationship object set to `null`; dereferencing `rec.Account.Name` on those rows throws.

**How to avoid:** null-guard the relationship object (`rec.Account != null`) before reading any
parent field, or filter the foreign key so parent-less rows are excluded from the query.

---

## Gotcha 4: OR and ORDER BY on a related field silently keep null-FK rows

**What happens:** a query with an `OR` branch on a relationship field, or an `ORDER BY` on a
parent field, returns records whose foreign key is null even though the relationship condition
looks like it should exclude them.

**When it occurs:** the reference says records "are returned even if the foreign key value in a
record is null" both in an `OR` clause and in an `ORDER BY`. The relationship term does not act
as an implicit "parent exists" filter.

**How to avoid:** if parent-less rows must be excluded, add an explicit `ForeignKeyId != null`
condition (`AND`-ed at the right precedence) rather than assuming the join drops them.

---

## Gotcha 5: `!= null` means different things on scalar vs Boolean fields

**What happens:** the same operator behaves differently depending on field type — `ActivityDate
!= null` returns rows that have a date, but `Flag__c != null` returns rows where the Boolean is
`true`, not "rows that have a value."

**When it occurs:** any query that reuses a `!= null` idiom across field types, or generated code
that treats every field as nullable in the same way.

**How to avoid:** reserve `= null` / `!= null` for genuinely nullable scalar fields; for Booleans,
always write `= true` / `= false` so the type-specific coercion never surprises a reader.
