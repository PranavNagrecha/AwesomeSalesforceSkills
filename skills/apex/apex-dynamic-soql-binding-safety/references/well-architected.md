# Well-Architected Notes — Apex Dynamic SOQL Binding Safety

## Relevant Pillars

- **Security** — primary pillar. Dynamic SOQL is the canonical SOQL-injection surface in Apex. The Well-Architected Trusted pillar requires that user input never participate in query parsing; bind variables and identifier allowlisting are the two controls that satisfy that requirement. `AccessLevel.USER_MODE` extends the safety net to FLS and CRUD enforcement at query time.
- **Reliability** — secondary. A poorly bound dynamic query throws `QueryException` at runtime instead of compile time, so reliability depends on negative tests covering the binding contract (missing bind, wrong-typed bind, IN with non-collection).
- **Operational Excellence** — secondary. Code review and the bundled checker script catch unsafe concatenations early, before they reach production. Treat the checker as a CI gate.

## Architectural Tradeoffs

| Tradeoff | Implication |
|---|---|
| `Database.query` with `:varName` vs `Database.queryWithBinds` | `query` is terser for single-method use; `queryWithBinds` is mandatory across method boundaries because bind variables otherwise go out of scope. Standardize on `queryWithBinds` to eliminate scope-related bugs. |
| `WITH USER_MODE` clause vs `AccessLevel.USER_MODE` argument | Equivalent semantics. The argument keeps security policy out of the parsed string and out of reach of accidental concatenation. Prefer the argument. |
| Allowlist via `Set<String>` vs Schema describe | `Set<String>` is fast and explicit but goes stale when fields are added. Schema describe is dynamic but slower and more code. Combining both (Set for "exposed in UI", describe for "real and accessible") is the most defensible. |
| `AccessLevel.SYSTEM_MODE` for background jobs | Legitimate but high-risk. Document every site, prohibit it in user-facing controllers, audit periodically. |

## Anti-Patterns

1. **`String.escapeSingleQuotes` as the sole defense.** Escaping protects string-literal contexts only. Field names, sObject names, ORDER BY, and LIMIT are unprotected. Treat escaping as defense-in-depth alongside binding, never as the primary control.
2. **Bind map typed `Map<String, String>`.** Compiles via covariance, fails at runtime when a bind needs Integer, Date, Id, or List. Always declare `Map<String, Object>`.
3. **Field-name allowlist that does not normalize case.** `if (allowed.contains(fieldName))` against an allowlist of `'Name'` will reject `'name'` — and worse, will accept `'Name'` while the developer believes the comparison is case-insensitive. Always lowercase both sides, or use `containsIgnoreCase` style helpers consistently.

## Official Sources Used

- Apex Developer Guide — Dynamic SOQL — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dynamic_soql.htm
- Apex Reference Guide — Database Class (`queryWithBinds`) — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_methods_system_database.htm
- Apex Developer Guide — SOQL Injection — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/pages_security_tips_soql.htm
- Salesforce Security Trailhead — SOQL Injection — https://trailhead.salesforce.com/content/learn/modules/secure-secrets-storage/protect-secrets-using-named-credentials (referenced unit on input safety) and the dedicated unit at https://trailhead.salesforce.com/content/learn/modules/improve-developer-experience-with-platform-cache (combined Apex security path)
- Salesforce Well-Architected — Trusted (Security) — https://architect.salesforce.com/well-architected/trusted/secure
