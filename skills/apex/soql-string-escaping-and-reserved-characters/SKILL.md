---
name: soql-string-escaping-and-reserved-characters
description: "Use when a SOQL single-quoted string literal contains a character that must be escaped: an apostrophe in a name (O'Brien, Bob's BBQ), a backslash, a tab/newline/other control character, a Unicode character via \\uXXXX, or a literal LIKE wildcard (\\_ or \\%). Covers the backslash escape character, the full quoted-string escape-sequence table, the two reserved characters (single quote and backslash) that must always be escaped, the LIKE-only \\_ / \\% wildcard escapes, the hard-error rule for any other backslash use, and String.escapeSingleQuotes on the Apex side. NOT for choosing bind variables vs concatenation or SOQL-injection defense-in-depth (see apex/apex-dynamic-soql-binding-safety and apex/soql-security), NOT for general SELECT/WHERE/ORDER BY syntax (see apex/soql-fundamentals), NOT for Apex String/regex methods (see apex/apex-string-and-regex)."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "escape a single quote in a SOQL literal for a name like O'Brien or Bob's BBQ"
  - "match a literal percent sign or underscore wildcard in a SOQL LIKE clause"
  - "fix a SOQL query error caused by a backslash in a string literal or file path"
  - "include a newline, tab, or Unicode character inside a SOQL string literal"
  - "escape reserved characters when building a dynamic SOQL string in Apex"
tags:
  - soql
  - string-escaping
  - reserved-characters
  - like-wildcards
  - escape-sequences
inputs:
  - "A SOQL query (inline [SELECT ...] or a dynamic query string) containing a single-quoted string literal"
  - "The literal value being embedded — a name with an apostrophe, a path with a backslash, a LIKE pattern, or text with control/Unicode characters"
  - "Whether the value originates from user input (then binding and injection defense also apply)"
outputs:
  - "A correctly escaped SOQL string literal that parses without a query error"
  - "The right escape sequence for each special character (\\', \\\\, \\n, \\uXXXX, and the LIKE-only \\_ / \\%)"
  - "Apex-side guidance: when String.escapeSingleQuotes covers the reserved characters and when to bind instead"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# SOQL String Escaping and Reserved Characters

This skill activates when a SOQL single-quoted string literal contains a character the parser treats specially — an apostrophe, a backslash, a control character, a Unicode code point, or a LIKE wildcard you want to match literally. It documents the fixed SOQL escape rule set so the query parses correctly instead of throwing a hard error or matching the wrong records.

---

## Before Starting

Gather this context before working on anything in this domain:

- **The escape character in SOQL is the backslash (`\`)** — not doubling the quote (`''`), which is the SQL-92 / Oracle convention. This is the single most common wrong assumption: a person who knows SQL will write `'Bob''s BBQ'`, which is invalid SOQL. The correct form is `'Bob\'s BBQ'`.
- **A backslash used outside a defined escape sequence is a *hard query error*, not a literal backslash.** The docs state: "If you use a backslash character in any other context, an error occurs." So a Windows path like `'C:\Users'` or a regex-style `'\d+'` inside a SOQL literal fails to parse — it does not silently keep the backslash.
- **Two characters are formally *reserved*: the single quote (`'`) and the backslash (`\`).** Inside a single-quoted literal both must be preceded by a backslash to be interpreted correctly, or an error occurs.
- **Maturity is unstated.** These are baseline SOQL language rules documented in the SOQL and SOSL Reference; the official docs do not stamp them with a GA/Beta/Pilot label, and they are unchanged in substance across recent API versions. Do not assert a maturity level the docs don't state.

---

## Core Concepts

### The escape character and the escape-sequence table

The escape character for SOQL string literals is the backslash. Only the sequences in the table below are valid; the letter sequences are **case-insensitive** (`\n` and `\N` are equivalent):

| Sequence | Meaning |
|---|---|
| `\n` or `\N` | New line |
| `\r` or `\R` | Carriage return |
| `\t` or `\T` | Tab |
| `\b` or `\B` | Bell |
| `\f` or `\F` | Form feed |
| `\"` | One double-quote character |
| `\'` | One single-quote character |
| `\\` | Backslash |
| `\_` | Matches a single underscore character — **LIKE expression only** |
| `\%` | Matches a single percent sign character — **LIKE expression only** |
| `\uXXXX` | Unicode character, where `XXXX` is the hex code (e.g. `é` is `é`) |

Any backslash followed by anything else is an error. There is no "unknown escape falls back to literal" behavior — the parser rejects the whole query.

### Reserved characters: single quote and backslash

The single quote (`'`) and the backslash (`\`) are reserved in SOQL. Any reserved character that appears as a literal inside a single-quoted string must be escaped with a preceding backslash, or the query errors. This is why:

- An apostrophe in data (`O'Brien`, `Bob's BBQ`) must be written `O\'Brien`, `Bob\'s BBQ`.
- A literal backslash must be written `\\`.

The reserved-character rule and the escape-sequence table are two views of the same mechanism: `\'` and `\\` appear in both.

### LIKE-only wildcard escapes

In a `LIKE` expression, `%` matches any sequence of characters and `_` matches any single character. To match a **literal** `%` or `_`, escape it: `\%` and `\_`. These two sequences are valid *only* inside a `LIKE` expression — using them anywhere else is one of the "any other context" errors. The escape changes match semantics, not just parsing:

- `LIKE 'Ter%'` → names that **begin with** `Ter`.
- `LIKE 'Ter\%'` → the name **exactly equal to** `Ter%`.
- `LIKE 'Ter\%%'` → names that **begin with** `Ter%` (escaped `%` is literal, trailing `%` is the wildcard).

### Two escaping layers when the query lives in Apex

For **inline** SOQL (`[SELECT ... WHERE Name = 'Bob\'s BBQ']`), the bracketed text *is* SOQL, so you write SOQL escapes directly. For **dynamic** SOQL, the query is an Apex `String` first, so Apex string-literal escaping applies to your source, and the *runtime* string is what the SOQL parser sees. `String.escapeSingleQuotes(stringToEscape)` adds the escape character (`\`) before any single quote (`'`) or backslash (`\`) in a value — exactly the two reserved characters — which is why the Apex Reference Guide recommends it "to help prevent SOQL injection." It does not escape `%`/`_`, so it does not neutralize LIKE wildcards.

---

## Common Patterns

### Apostrophe-safe literal (the reserved single quote)

**When to use:** a filter value can contain an apostrophe — person and company names are the usual source (`O'Brien`, `Bob's BBQ`).

**How it works:** in inline SOQL, escape the quote in the literal: `WHERE Name = 'Bob\'s BBQ'`. When the value is an Apex variable going into dynamic SOQL, prefer a bind variable so you never hand-escape; if you must concatenate, run the value through `String.escapeSingleQuotes()` first.

**Why not the alternative:** doubling the quote (`'Bob''s BBQ'`) is SQL, not SOQL, and fails to parse. Leaving the apostrophe raw both errors *and* is the classic SOQL-injection break-out character.

### Literal wildcard in a LIKE search

**When to use:** the search term itself contains `%` or `_` and the user means those characters literally — e.g. searching product names for "50% off" or a code like `A_B`.

**How it works:** escape the wildcard inside the LIKE pattern: `WHERE Name LIKE '%50\% off%'`. The `\%` matches a literal percent; the surrounding bare `%` remain wildcards.

**Why not the alternative:** an unescaped `%`/`_` from user input is treated as a wildcard, silently widening the result set (a correctness and, for user-driven search, a data-exposure problem). `String.escapeSingleQuotes` does **not** fix this — wildcard escaping is separate.

### Control characters and Unicode in a literal

**When to use:** you need a newline, tab, or a specific Unicode character inside a literal (rare in filters, more common when a stored value legitimately contains them).

**How it works:** use the table sequence — `\n`, `\t`, or `\uXXXX` (e.g. `é` for `é`). Never paste a raw backslash-plus-letter that isn't in the table.

---

## Decision Guidance

| Situation | Recommended approach | Reason |
|---|---|---|
| Value with an apostrophe in **dynamic** SOQL from user input | Bind variable (or `queryWithBinds`); `String.escapeSingleQuotes` only if you must concatenate | Binding removes the escaping burden and closes injection; see apex/apex-dynamic-soql-binding-safety |
| Apostrophe in a **static, inline** literal you control | Write `\'` in the query text | Inline SOQL uses SOQL escapes directly; no Apex layer |
| User's LIKE term may contain a literal `%` or `_` | Escape it to `\%` / `\_` in the pattern | Unescaped wildcards widen matches; `escapeSingleQuotes` won't help |
| Literal backslash needed in the value | Write `\\` | A lone `\` outside a valid sequence is a hard error |
| Newline / tab / Unicode inside a literal | Use `\n` / `\t` / `\uXXXX` from the table | These are the only valid representations |
| You came from SQL/Oracle and reflexively doubled the quote | Replace `''` with `\'` | `''` is not a SOQL escape |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Locate every single-quoted literal** in the query (inline `[SELECT ...]` or the dynamic query string) and note which values come from user input.
2. **Escape the reserved characters** in each literal: single quote → `\'`, backslash → `\\`. For user-supplied values in dynamic SOQL, do this by *binding* (preferred) or `String.escapeSingleQuotes()`, not by hand.
3. **Handle LIKE wildcards deliberately** — decide per `%`/`_` whether it is a wildcard or a literal; escape the literals as `\%` / `\_`, and remember `escapeSingleQuotes` does not touch them.
4. **Represent control/Unicode characters** only with valid table sequences (`\n`, `\t`, `\uXXXX`); reject any other backslash use.
5. **Validate** by running the escape checker (`scripts/check_soql_string_escaping_and_reserved_characters.py`) over `.soql` files or with `--query`, and by executing the query in a sandbox / Developer Console Query Editor to confirm it parses and returns the intended rows.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every apostrophe inside a literal is `\'` (never a raw `'` or a doubled `''`)
- [ ] Every literal backslash is `\\`; no lone `\` sits outside a valid escape sequence
- [ ] Each `%` / `_` in a LIKE pattern is intentionally a wildcard, or escaped `\%` / `\_` if meant literally
- [ ] Control/Unicode characters use only `\n`, `\r`, `\t`, `\b`, `\f`, or `\uXXXX`
- [ ] `\_` and `\%` appear only inside LIKE expressions
- [ ] User-supplied values in dynamic SOQL are bound (or escaped with `String.escapeSingleQuotes`), not concatenated raw
- [ ] The query was executed once to confirm it parses and matches the intended records

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Doubling the quote is a SQL habit that fails in SOQL** — `'O''Brien'` parses in Oracle/SQL-92 but errors in SOQL; the correct escape is `'O\'Brien'`.
2. **A stray backslash is a hard error, not a literal** — Windows paths (`'C:\temp'`) and regex fragments (`'\d'`) inside a SOQL literal throw a query error because the backslash isn't part of a defined sequence.
3. **`String.escapeSingleQuotes` does not escape LIKE wildcards** — it handles `'` and `\` only, so a user-supplied `%`/`_` still behaves as a wildcard and can widen the result set even after "escaping."

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Correctly escaped SOQL literal | A single-quoted literal with `\'`, `\\`, `\%`/`\_`, `\uXXXX` applied per the escape table so the query parses |
| `scripts/check_soql_string_escaping_and_reserved_characters.py` | Stdlib checker that flags invalid backslash escapes and LIKE-only escapes used outside LIKE, in `.soql` files or a `--query` string |
| `templates/soql-string-escaping-and-reserved-characters-template.md` | Quick-reference escape table plus an Apex escaping worksheet to fill in per query |

---

## Related Skills

- `apex/apex-dynamic-soql-binding-safety` — how to inject *values* safely with bind variables / `queryWithBinds`; use it for the injection decision, this skill for the character-level escape rules.
- `apex/soql-security` — CRUD/FLS enforcement and SOQL-injection review; escaping is one layer, binding and `WITH USER_MODE` are the others.
- `apex/soql-fundamentals` — general SELECT/WHERE/ORDER BY/LIKE syntax; this skill is the narrow escaping/reserved-character reference within it.
- `apex/apex-string-and-regex` — the Apex `String` class (including `escapeSingleQuotes`) and regex; distinct from SOQL literal escaping, which happens in the query parser.
