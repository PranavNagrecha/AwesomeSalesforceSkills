# LLM Anti-Patterns — SOQL String Escaping and Reserved Characters

Common mistakes AI coding assistants make when generating or advising on SOQL string escaping
and reserved characters. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Doubling the quote instead of backslash-escaping

**What the LLM generates:** SQL-style apostrophe escaping in a SOQL literal.

```sql
SELECT Id FROM Account WHERE Name = 'Bob''s BBQ'
```

**Why it happens:** the vast majority of SQL in training data uses the SQL-92/Oracle convention
of doubling the single quote, so the model reproduces it for SOQL too.

**Correct pattern:**

```sql
SELECT Id FROM Account WHERE Name = 'Bob\'s BBQ'
```

**Detection hint:** a `''` (two adjacent single quotes) inside a SOQL string literal — SOQL uses
the backslash, so `''` is almost always wrong.

---

## Anti-Pattern 2: Assuming an unknown backslash escape is a literal backslash

**What the LLM generates:** a Windows path or regex-like fragment dropped straight into a SOQL
literal, treating `\` as literal (C/Python/JS mental model).

```sql
SELECT Id FROM Doc__c WHERE Path__c = 'C:\temp\report'
```

**Why it happens:** in many languages an undefined escape degrades to a literal character; the
model generalizes that here. In SOQL it is a hard error instead.

**Correct pattern:**

```sql
SELECT Id FROM Doc__c WHERE Path__c = 'C:\\temp\\report'
```

**Detection hint:** a single `\` inside a SOQL literal followed by any character other than
`n N r R t T b B f F " ' \ u` (or LIKE-only `_ %`). Flag it — it will not parse.

---

## Anti-Pattern 3: Claiming `escapeSingleQuotes` makes LIKE input safe

**What the LLM generates:** advice that running a search term through
`String.escapeSingleQuotes` fully sanitizes it for a `LIKE` clause.

```apex
String term = String.escapeSingleQuotes(userInput);
Database.query('SELECT Id FROM Account WHERE Name LIKE \'%' + term + '%\'');
```

**Why it happens:** the model knows `escapeSingleQuotes` is the injection-prevention helper and
overgeneralizes it to "sanitizes everything."

**Correct pattern:** escape LIKE wildcards separately, because `escapeSingleQuotes` escapes only
`'` and `\`:

```apex
String term = String.escapeSingleQuotes(userInput)
                    .replace('%', '\\%')
                    .replace('_', '\\_');
```

**Detection hint:** `escapeSingleQuotes` feeding a `LIKE` pattern with no separate `%`/`_`
handling nearby.

---

## Anti-Pattern 4: Escaping `%` or `_` outside a LIKE expression

**What the LLM generates:** `\%` or `\_` inside an equality filter (or a non-LIKE context),
"just to be safe."

```sql
SELECT Id FROM Account WHERE Name = 'Acme \% Co'
```

**Why it happens:** the model treats `%`/`_` as always-special (they aren't outside LIKE) and
applies the LIKE-only escape everywhere.

**Correct pattern:** in an equality filter, `%` and `_` are ordinary characters — no escape:

```sql
SELECT Id FROM Account WHERE Name = 'Acme % Co'
```

**Detection hint:** `\%` or `\_` on a line whose comparison operator is `=`, `!=`, `IN`, etc.
rather than `LIKE`.

---

## Anti-Pattern 5: Hand-concatenating quotes into dynamic SOQL instead of binding

**What the LLM generates:** manual `\'` + variable + `\'` string-building for a user value,
skipping bind variables entirely.

```apex
Database.query('SELECT Id FROM Contact WHERE LastName = \'' + name + '\'');
```

**Why it happens:** the model reproduces string-concatenation query building common in older
tutorials, without reaching for bind variables.

**Correct pattern:** bind the value — no hand-escaping, and injection-safe:

```apex
Database.query('SELECT Id FROM Contact WHERE LastName = :name');
```

**Detection hint:** `\'` + concatenation into `Database.query(...)` — prefer `:bindVar`. (Deeper
guidance in `apex/apex-dynamic-soql-binding-safety`.)

---

## Anti-Pattern 6: Fabricating a GA/Beta maturity for these rules

**What the LLM generates:** "SOQL escape sequences became Generally Available in <release>..." or
a version stamp the docs don't give.

**Why it happens:** the model pattern-fills a maturity label onto any feature it describes.

**Correct pattern:** state that these are baseline SOQL language rules in the SOQL and SOSL
Reference and that the docs do not assign a GA/Beta/Pilot status; don't invent one.

**Detection hint:** any "Generally Available", "Beta", or "since <release>" claim about SOQL
escape sequences that isn't backed by a release-notes citation.
