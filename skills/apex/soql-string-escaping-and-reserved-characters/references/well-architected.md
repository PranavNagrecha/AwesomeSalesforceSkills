# Well-Architected Notes — SOQL String Escaping and Reserved Characters

## Relevant Pillars

- **Security** — the single quote is both a reserved character and the primary SOQL-injection
  break-out character. Escaping it (or binding the value) is a correctness *and* a security
  concern: a raw apostrophe from user input both errors the query and opens an injection path.
  Escaping is one layer only — bind variables and `WITH USER_MODE` (see
  `apex/apex-dynamic-soql-binding-safety` and `apex/soql-security`) are the stronger controls.
  Note too that `String.escapeSingleQuotes` does not escape LIKE wildcards, so unescaped `%`/`_`
  can widen a user-facing search beyond its intended scope.
- **Reliability** — an undefined backslash sequence is a *hard query error*, not a silent
  literal. Getting escaping wrong turns a data issue (a name with an apostrophe, a stored path)
  into a runtime failure. Correct escaping keeps queries parsing deterministically across
  releases, since these rules are stable baseline SOQL language behavior.

## Architectural Tradeoffs

- **Bind vs. escape for user values.** Binding (`:var` / `Database.queryWithBinds`) removes the
  escaping burden and is the safest default for injecting values; hand-escaping with
  `String.escapeSingleQuotes` is acceptable only when binding is genuinely not possible, and it
  covers just `'` and `\`. Reserve escaping for cases the bind mechanism can't express.
- **Wildcard flexibility vs. precision in LIKE.** Leaving `%`/`_` active gives flexible search;
  escaping them (`\%`, `\_`) gives exact literal matching. Decide per character — don't blanket
  one policy across a query, and don't assume quote-escaping handled it.

## Anti-Patterns

1. **SQL-style quote doubling** — using `''` to escape an apostrophe. It is valid SQL and invalid
   SOQL; use `\'`. Copy-pasting SQL escaping into SOQL is the most common failure.
2. **Trusting one escape helper for everything** — assuming `String.escapeSingleQuotes` sanitizes
   LIKE input. It escapes only the two reserved characters; wildcards and injection defense in
   depth need their own handling.

## Official Sources Used

- SOQL and SOSL Reference — Quoted String Escape Sequences — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_quotedstringescapes.htm
- SOQL and SOSL Reference — Reserved Characters — https://developer.salesforce.com/docs/atlas.en-us.soql_sosl.meta/soql_sosl/sforce_api_calls_soql_select_reservedcharacters.htm
- Apex Reference Guide — String Class methods (escapeSingleQuotes) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_string.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
