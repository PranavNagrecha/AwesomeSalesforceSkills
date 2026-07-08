# LLM Anti-Patterns — SOQL Multi-Select Picklist Queries

Common mistakes AI coding assistants make when generating or advising on SOQL queries against
multi-select picklist fields. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `=` for containment

**What the LLM generates:** `WHERE Interests__c = 'Golf'` to answer "find contacts interested
in Golf."

**Why it happens:** in almost every other language and in single-select picklist filtering,
`field = value` is the natural "has this value" test. The model transfers that habit without
accounting for the semicolon-delimited multi-value storage.

**Correct pattern:**

```sql
WHERE Interests__c INCLUDES ('Golf')
```

**Detection hint:** an `=` or `!=` operator applied to a field known to be multi-select, with a
single-value operand that has no semicolon — almost always should be `INCLUDES` / `EXCLUDES`.

---

## Anti-Pattern 2: `LIKE '%value%'` as a stand-in for INCLUDES

**What the LLM generates:** `WHERE Interests__c LIKE '%Golf%'` for containment, reasoning that
the stored value is a string.

**Why it happens:** substring matching with `LIKE` is a heavily represented pattern in training
data for "does this text contain X," and the model does not model the delimited storage or the
dedicated operator.

**Correct pattern:**

```sql
WHERE Interests__c INCLUDES ('Golf')
```

**Detection hint:** `LIKE '%...%'` on a multi-select picklist field. It risks matching
substrings (`Golfing`) and can't express AND/OR grouping.

---

## Anti-Pattern 3: Inverting semicolon (AND) and comma (OR)

**What the LLM generates:** `INCLUDES ('AAA,BBB')` intending OR, or `INCLUDES ('AAA','BBB')`
intending "both selected."

**Why it happens:** comma-as-OR and comma-as-list are both common elsewhere (IN clauses, CSV),
so the model reaches for a comma without tracking that inside a multi-select operand it is the
semicolon that means AND and the comma *between operands* that means OR.

**Correct pattern:**

```sql
-- AAA AND BBB both selected:
WHERE MSP1__c INCLUDES ('AAA;BBB')
-- AAA OR BBB selected:
WHERE MSP1__c INCLUDES ('AAA','BBB')
```

**Detection hint:** a comma *inside* the single quotes of an operand, or a semicolon *between*
operands — both are grammar inversions.

---

## Anti-Pattern 4: Adding `ORDER BY` on the multi-select field

**What the LLM generates:** `SELECT ... WHERE Interests__c INCLUDES (...) ORDER BY Interests__c`
to produce grouped output.

**Why it happens:** `ORDER BY <the field I just filtered>` is a reflexive completion, and the
model doesn't surface that multi-select picklist is an unsupported sort type.

**Correct pattern:**

```sql
-- Order by a supported field instead:
SELECT Id, Interests__c FROM Contact
WHERE Interests__c INCLUDES ('Golf') ORDER BY Name
```

**Detection hint:** the same multi-select field name appearing after `ORDER BY`. It is a query
error, not a warning.

---

## Anti-Pattern 5: Concatenating values into a dynamic query

**What the LLM generates:** `Database.query('SELECT Id FROM Contact WHERE Interests__c INCLUDES
(\'' + userValue + '\')')`.

**Why it happens:** string-building a query is a common code shape, and the model optimizes for
"make it dynamic" without applying Salesforce's injection-safety guidance.

**Correct pattern:**

```apex
List<String> groups = new List<String>{ 'Golf', 'Tennis;Squash' };
List<Contact> rows = [
    SELECT Id FROM Contact WHERE Interests__c INCLUDES :groups WITH USER_MODE
];
```

**Detection hint:** raw input concatenated into a query string with `INCLUDES`/`EXCLUDES` and no
bind variable or `String.escapeSingleQuotes`.

---

## Anti-Pattern 6: Inventing a GA/Beta status or a version claim

**What the LLM generates:** "multi-select picklist SOQL support has been GA since Spring '16,"
or asserts the four operators are "new in API 39.0."

**Why it happens:** models pattern-fill maturity labels and attach a version number to any
feature. Here the *only* documented version gate is that filtering by a value's **API name**
(vs display label) is available in API version 39.0 and later; the operators themselves carry no
GA/Beta/Pilot label.

**Correct pattern:** describe `=`, `!=`, `INCLUDES`, `EXCLUDES` as standard `WHERE`-clause syntax
with no stated maturity label, and attach the "API version 39.0 and later" gate only to
API-name-based matching.

**Detection hint:** any "Generally Available"/"Beta" claim, or a version number pinned to the
operators rather than to the API-name-matching behavior.
