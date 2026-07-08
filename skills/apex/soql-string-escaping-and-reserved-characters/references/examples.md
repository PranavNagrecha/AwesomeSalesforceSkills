# Examples — SOQL String Escaping and Reserved Characters

All queries below follow the SOQL and SOSL Reference. In **inline** SOQL (`[SELECT ...]`) the
bracketed text is SOQL, so you write SOQL escapes directly. In **dynamic** SOQL the query is an
Apex `String` first, so prefer binding for user values; the `String.escapeSingleQuotes` examples
show the escape mechanics when concatenation is unavoidable.

## Example 1: Apostrophe in a name (the reserved single quote)

**Context:** a query filters `Account.Name` for a value that contains an apostrophe, such as
`Bob's BBQ` or `O'Brien`.

**Problem:** a raw apostrophe closes the literal early and the query fails to parse. Developers
coming from SQL/Oracle reflexively double the quote (`'Bob''s BBQ'`), which is also invalid SOQL.

**Solution:**

```apex
// Inline SOQL — escape the single quote with a backslash (SOQL's escape character)
List<Account> accts = [SELECT Id FROM Account WHERE Name = 'Bob\'s BBQ'];
```

**Why it works:** the single quote is a reserved character; preceding it with `\` makes the
parser treat it as a literal quote inside the string rather than the closing delimiter.

---

## Example 2: Literal percent sign in a LIKE search

**Context:** a product-search feature lets users search names, and a user searches for `50% off`.

**Problem:** in a `LIKE` expression `%` is the multi-character wildcard, so an unescaped `%`
matches "any sequence" and silently returns far more rows than intended.

**Solution:**

```apex
// Match names that CONTAIN the literal text "50% off"
List<Product2> hits = [SELECT Id, Name FROM Product2 WHERE Name LIKE '%50\% off%'];
```

The escape only affects the wildcard you escape — compare the reference's worked cases:

```sql
SELECT Id FROM Account WHERE Name LIKE 'Ter%'    -- begins with 'Ter'
SELECT Id FROM Account WHERE Name LIKE 'Ter\%'   -- exactly 'Ter%'
SELECT Id FROM Account WHERE Name LIKE 'Ter\%%'  -- begins with 'Ter%'
```

**Why it works:** `\%` matches a single literal percent sign (valid in LIKE expressions only);
the surrounding bare `%` remain wildcards.

---

## Example 3: Escaping user input in dynamic SOQL (Apex layer)

**Context:** a dynamic query concatenates a user-supplied account name.

**Problem:** the value may contain a single quote or backslash — both reserved — producing a
parse error and a SOQL-injection opening.

**Solution — prefer a bind variable (no hand-escaping):**

```apex
String userName = incoming;                 // may contain ' or \
List<Account> a = Database.query(
    'SELECT Id FROM Account WHERE Name = :userName'
);
```

**If you must concatenate, escape the reserved characters first:**

```apex
// String.escapeSingleQuotes adds '\' before any single quote (') or backslash (\)
String safe = String.escapeSingleQuotes(userName);
List<Account> a = Database.query(
    'SELECT Id FROM Account WHERE Name = \'' + safe + '\''
);
```

**Why it works:** `String.escapeSingleQuotes` escapes exactly the two reserved characters
(`'` and `\`). The Apex Reference Guide recommends it "to help prevent SOQL injection." Binding
is still preferred because it removes the escaping burden entirely — see
`apex/apex-dynamic-soql-binding-safety`.

---

## Example 4: A backslash / Windows path is a hard error, not a literal

**Context:** a query filters a text field that stores a Windows path, `C:\temp\report`.

**Problem:** a lone backslash outside a defined escape sequence is rejected by the parser —
"If you use a backslash character in any other context, an error occurs."

**Solution:**

```apex
// Each literal backslash must be doubled to \\
List<Doc__c> docs = [SELECT Id FROM Doc__c WHERE Path__c = 'C:\\temp\\report'];
```

**Why it works:** `\\` is the defined sequence for a single literal backslash; `\t` on its own
would have meant a tab, and `\r` a carriage return, so the path had to be escaped explicitly.

---

## Example 5: Newline, tab, and Unicode inside a literal

**Context:** a stored value legitimately contains a tab or an accented character (`café`).

**Solution:**

```apex
// \t is a tab; é is the Unicode 'é'
List<Note__c> n = [SELECT Id FROM Note__c WHERE Body__c = 'café'];
// Letter escapes are case-insensitive: \n and \N are equivalent
List<Note__c> m = [SELECT Id FROM Note__c WHERE Body__c = 'line1\nline2'];
```

**Why it works:** `\uXXXX` embeds the character at hex code `XXXX`; `\n`/`\t` are the table
sequences for newline/tab. Only the sequences in the table are valid.

---

## Anti-Pattern: escaping single quotes and assuming LIKE is safe

**What practitioners do:** run a user's search term through `String.escapeSingleQuotes` and drop
it straight into a `LIKE '%' + term + '%'` clause, believing the input is now fully neutralized.

**What goes wrong:** `escapeSingleQuotes` handles `'` and `\` only. A user term containing `%` or
`_` still acts as a wildcard, so `_` matches any single character and `%` matches any sequence —
widening the result set and, for user-facing search, potentially exposing records the search was
meant to narrow.

**Correct approach:** escape LIKE wildcards separately — replace literal `%` with `\%` and `_`
with `\_` in the term before building the pattern — in addition to escaping/binding the quote.
Escaping and wildcard-handling are two different jobs.
