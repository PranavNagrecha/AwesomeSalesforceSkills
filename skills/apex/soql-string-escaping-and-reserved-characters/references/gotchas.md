# Gotchas — SOQL String Escaping and Reserved Characters

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Doubling the quote (SQL habit) is invalid in SOQL

**What happens:** the query throws a parse error even though the same escaping works in Oracle,
SQL Server, or Postgres.

**When it occurs:** a developer escapes an apostrophe SQL-style by doubling it — `'O''Brien'` —
instead of using SOQL's backslash escape.

**How to avoid:** SOQL's escape character is the backslash. Write `'O\'Brien'`. There is no
double-quote-the-quote escaping in SOQL.

---

## Gotcha 2: A lone backslash is a hard error, not a literal backslash

**What happens:** the whole query is rejected — not silently kept — the moment a backslash is
followed by a character that isn't a defined escape sequence.

**When it occurs:** Windows paths (`'C:\Users'`), regex fragments (`'\d+'`, `'\w'`), or any text
where someone assumed an unknown escape falls through to a literal backslash. The SOQL Reference
says: "If you use a backslash character in any other context, an error occurs." — UNVERIFIED
(2026-10-20): that guide is not in the corpus.

**How to avoid:** double every literal backslash to `\\`, and only ever emit backslash sequences
that appear in the escape table (`\n \r \t \b \f \s \" \' \\ \uXXXX`, plus LIKE-only `\_ \%`); the Apex guide lists `\s` among the sequences shared with SOQL (apexdev 264 L1280-1282).

---

## Gotcha 3: `String.escapeSingleQuotes` does not neutralize LIKE wildcards

**What happens:** after "escaping" user input, a `LIKE` search still returns too many rows, or a
user can broaden a search by typing `%`.

**When it occurs:** the value is passed through `String.escapeSingleQuotes` (which escapes only
`'` and `\` — apexref 262 L235380) and dropped into a `LIKE` pattern; the user's `%`/`_` are still active wildcards.

**How to avoid:** escape LIKE wildcards separately (`%` → `\%`, `_` → `\_`) before assembling the
pattern. Treat quote-escaping and wildcard-escaping as two independent steps.

---

## Gotcha 4: LIKE-only escapes (`\_`, `\%`) are errors outside a LIKE expression

**What happens:** a query with `\%` or `\_` in an equality or non-LIKE context fails to parse.

**When it occurs:** copy-pasting a LIKE pattern into a `=` filter, or reflexively escaping a `%`
in a value that isn't part of a `LIKE`. `\_` and `\%` are valid *only* inside a LIKE expression;
everywhere else they fall under the "any other context → error" rule.

**How to avoid:** use `\_` / `\%` only inside `LIKE`. In an equality filter, `%` and `_` are
ordinary characters and need no escaping.

---

## Gotcha 5: Letter escapes are case-insensitive — don't over-think the casing

**What happens:** a developer worries `\N` versus `\n` behaves differently, or a code reviewer
flags `\T` as a typo.

**When it occurs:** reading queries where escapes appear uppercase (`\N`, `\R`, `\T`).

**How to avoid:** the alphabetic escape sequences are case-insensitive — `\n` and `\N` both mean
newline, `\t` and `\T` both mean tab. Only `\uXXXX` requires its lowercase `u`, with four hex
digits following. UNVERIFIED (2026-10-20): case-insensitivity is a SOQL Reference statement, not in the corpus.

---

## Gotcha 6: `_` in `LIKE` Is a Single-Character Wildcard — `LIKE '%__c'` Matches Almost Everything

**What happens:** A field-debt query `WHERE DeveloperName LIKE '%__c'` is meant to find custom fields. In SOQL `LIKE`, `_` matches **any single character**. The pattern matches `Account`, `Contact`, and every standard object whose API name is at least two characters plus anything. Counts explode; custom-field inventories are garbage.

**When it occurs:** Tooling/EntityDefinition scans, report-type field lists, "find all custom fields" Apex.

**How to avoid:** Escape the underscore: inline SOQL `LIKE '%\_\_c'`; inside an Apex string passed to `Database.query`, `'%\\_\\_c'` (the Apex layer turns `\\` into one `\`). Corrected 2026-10-20: the old text gave only `'%\\_\\_c'`, which inline is an escaped backslash followed by a live `_` wildcard. Prefer `DurableId` / `QualifiedApiName` ending-in checks in Apex after an unfiltered describe, not LIKE on `__c`.
