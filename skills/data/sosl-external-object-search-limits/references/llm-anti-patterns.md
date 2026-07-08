# LLM Anti-Patterns — SOSL External Object Search Results Limits

Common mistakes AI coding assistants make when generating or advising on SOSL against Salesforce Connect
external objects. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `LIKE` for a "starts with" search on an external object

**What the LLM generates:** a SOSL (or SOSL-shaped) statement with a `LIKE` operator, e.g.
`FIND ... RETURNING Order__x WHERE Name__c LIKE 'Acme%'`.

**Why it happens:** SQL/SOQL training data overwhelmingly uses `LIKE` for prefix matching, and the model
carries it into SOSL. External objects reject the `LIKE` operator outright.

**Correct pattern:**

```apex
// Wildcards live inside the FIND term, not in a LIKE operator
List<List<SObject>> hits = [FIND 'Acme*' RETURNING Order__x(Name__c, Description__c)];
```

**Detection hint:** any `LIKE` token in a statement whose `RETURNING` names a `__x` object.

---

## Anti-Pattern 2: Reaching for `INCLUDES` / `EXCLUDES` on an external object

**What the LLM generates:** multi-select-style filtering with `INCLUDES('a;b')` or `EXCLUDES(...)`
against an external object.

**Why it happens:** the model pattern-matches multi-select picklist semantics from standard-object SOQL,
unaware that external objects don't support these operators.

**Correct pattern:** external objects support neither `INCLUDES` nor `EXCLUDES`. Search on a text field
with wildcards and post-filter the returned rows in Apex, or filter at the source system.

**Detection hint:** `INCLUDES(` or `EXCLUDES(` anywhere in a statement returning a `__x` object.

---

## Anti-Pattern 3: Relying on `IN ALL FIELDS` and omitting the external object from RETURNING

**What the LLM generates:** `FIND {term} IN ALL FIELDS` with a `RETURNING` clause that lists only standard
objects (or no `RETURNING` at all), assuming the external object is included implicitly.

**Why it happens:** for standard objects `IN ALL FIELDS` feels comprehensive, so the model assumes it also
sweeps in external objects.

**Correct pattern:**

```apex
// External objects are opt-in: name them explicitly in RETURNING
List<List<SObject>> hits = [FIND 'Acme' IN ALL FIELDS RETURNING Order__x(Name__c, Description__c)];
```

**Detection hint:** a `__x` object expected in results but absent from every `RETURNING FieldSpec`.

---

## Anti-Pattern 4: Emitting `toLabel()`, `convertCurrency()`, or `WITH DATA CATEGORY` on an external object

**What the LLM generates:** translation via `toLabel(field)`, currency conversion via `convertCurrency()`,
or Knowledge-style category filtering via `WITH DATA CATEGORY` in an external-object search.

**Why it happens:** these are common, valid tools on standard-object SOQL/SOSL; the model doesn't surface
the external-object exclusions. (`WITH DATA CATEGORY` and `toLabel()` are unsupported on all external
objects; `convertCurrency()` and generic `WITH` are unsupported on custom-adapter external objects.)

**Correct pattern:** return raw fields and do translation/conversion/categorization in the client or source
system; drop `WITH DATA CATEGORY` entirely.

**Detection hint:** `toLabel(`, `convertCurrency(`, or `WITH DATA CATEGORY` in a `__x` statement.

---

## Anti-Pattern 5: Assuming any field type is searchable

**What the LLM generates:** a `RETURNING Object__x(Amount__c, CreatedDate)` that searches on numeric/date
fields, or advice that "the search covers all fields."

**Why it happens:** standard-object search indexes many field types, so the model generalizes. On external
objects only `Text`, `Text Area`, and `Long Text Area` fields are searchable, and an object with no text
field returns zero records with no error.

**Correct pattern:** restrict searched/returned fields to text types and confirm at least one exists;
explain that an empty result may mean "no searchable field," not "no data."

**Detection hint:** a `__x` search that expects hits from non-text fields, or a "returns nothing" claim
with no check of searchable-field presence.

---

## Anti-Pattern 6: Mis-scoping adapter rules or asserting a maturity level

**What the LLM generates:** "logical operators in FIND are always fine," "`convertCurrency()` never works on
external objects," or "this GA feature since Spring 'NN…" — applying an adapter-scoped rule universally, or
inventing a GA/Beta status.

**Why it happens:** the model flattens the OData-only and custom-adapter-only qualifications into blanket
rules and pattern-fills maturity labels.

**Correct pattern:** scope precisely — **OData 2.0/4.0** adapters reject logical operators in FIND;
**custom** adapters reject `convertCurrency()` and generic `WITH`; everything else applies to all external
objects. State no GA/Beta/Pilot status — the reference page gives none.

**Detection hint:** a universal claim about logical operators or `convertCurrency()` without naming the
adapter, or any "Generally Available"/"Beta" wording not backed by a release-notes citation.
