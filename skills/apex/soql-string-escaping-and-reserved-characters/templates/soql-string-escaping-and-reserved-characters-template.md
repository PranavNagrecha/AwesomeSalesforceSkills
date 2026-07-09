# SOQL String Escaping — Quick Reference + Worksheet

Copy this into your working notes when fixing or authoring a SOQL literal. Part A is a
lookup you keep; Part B is a per-query worksheet you fill in.

## Part A — Escape sequence lookup (keep)

The escape character is the backslash (`\`). Letter escapes are case-insensitive.

| You want... | Write... | Notes |
|---|---|---|
| A literal single quote (`'`) | `\'` | Reserved character — always escape inside a literal |
| A literal backslash (`\`) | `\\` | Reserved character — a lone `\` is a hard error |
| A double quote (`"`) | `\"` | |
| New line | `\n` / `\N` | |
| Carriage return | `\r` / `\R` | |
| Tab | `\t` / `\T` | |
| Bell | `\b` / `\B` | |
| Form feed | `\f` / `\F` | |
| A Unicode character | `\uXXXX` | Exactly 4 hex digits (e.g. `é` = é) |
| A **literal** `%` in a LIKE pattern | `\%` | **LIKE only** — error elsewhere |
| A **literal** `_` in a LIKE pattern | `\_` | **LIKE only** — error elsewhere |

Anything else after a backslash → **query error** ("If you use a backslash character in any
other context, an error occurs").

LIKE match semantics:

```sql
Name LIKE 'Ter%'     -- begins with 'Ter'
Name LIKE 'Ter\%'    -- exactly 'Ter%'
Name LIKE 'Ter\%%'   -- begins with 'Ter%'
```

## Part B — Per-query worksheet (fill in)

**Query under review:**

```sql
-- paste the SOQL here
```

- [ ] Every apostrophe inside a literal is `\'` (not raw `'`, not doubled `''`)
- [ ] Every literal backslash is `\\`; no lone `\` outside a valid sequence
- [ ] Each LIKE `%` / `_` is intentionally a wildcard, or escaped `\%` / `\_` if literal
- [ ] No `\_` / `\%` appears outside a LIKE expression
- [ ] Control/Unicode characters use only table sequences (`\n`, `\t`, `\uXXXX`, ...)

**Value source:** ( ) static literal I control  ( ) user / external input

If user input in **dynamic** SOQL, prefer binding over hand-escaping:

```apex
// Preferred — bind the value (no escaping needed, injection-safe)
Database.query('SELECT Id FROM Account WHERE Name = :acctName');

// Only if concatenation is unavoidable — escape the reserved characters first.
// String.escapeSingleQuotes escapes ' and \ ONLY (not % or _).
String safe = String.escapeSingleQuotes(acctName);
Database.query('SELECT Id FROM Account WHERE Name = \'' + safe + '\'');

// If the value feeds a LIKE pattern, also escape the wildcards separately:
String term = String.escapeSingleQuotes(userInput).replace('%', '\\%').replace('_', '\\_');
Database.query('SELECT Id FROM Account WHERE Name LIKE \'%' + term + '%\'');
```

**Validation:**

```bash
# Validate a single query string
python3 scripts/check_soql_string_escaping_and_reserved_characters.py --query "<your SOQL>"

# Or scan .soql files in a directory
python3 scripts/check_soql_string_escaping_and_reserved_characters.py --manifest-dir path/to/soql
```

- [ ] Checker reports no P0/P1 issues
- [ ] Query executed once (sandbox / Developer Console Query Editor) — parses and returns the intended rows
