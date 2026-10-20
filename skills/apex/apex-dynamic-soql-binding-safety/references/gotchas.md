# Gotchas — Apex Dynamic SOQL Binding Safety

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `Database.query` bind variables must be in lexical scope at the call site

**What happens:** Bind variables in a `Database.query` string "must be within the scope of the database operation" (apex dev guide 264 L11623-11624), and a bind on a field (`:myVariable.field1__c`) "results in a Variable does not exist error" (L11629-11633). UNVERIFIED (2026-10-20): that a class field named `term` does not always work, that a variable in the caller never works, and the exact text `System.QueryException: Variable does not exist: term`.

**When it occurs:** Most often after a refactor that splits a query into a helper method (UNVERIFIED (2026-10-20): that the helper does not see the caller's locals). The guide's documented trigger is a bind on an object field.

**How to avoid:** Use `Database.queryWithBinds(query, Map<String, Object> binds, AccessLevel level)` (API 57.0 and later) whenever the query is not built and executed in the same method body: it "removes the need for the variables to be in scope when the query is executed" (L11647-11649).

---

## Gotcha 2: `Database.queryWithBinds` requires `Map<String, Object>`, not `Map<String, String>`

**What happens:** UNVERIFIED (2026-10-20): that a `Map<String, String>` compiles through Apex covariance and fails at run time when a bind needs an `Integer`, `Date`, `Id` or `List<Id>`, and the `System.TypeException` / `QueryException` outcome. The documented signature takes `Map<String, Object>` (apexref 262 L209135). The documented failure is a duplicate key ignoring case, which throws `System.QueryException: The bindMap consists of duplicate case-insensitive keys` (apex dev guide 264 L11659-11662).

**When it occurs:** When developers reach for `Map<String, String>` as the "obvious" filter map (since values often arrive as strings from the UI), then later add an `IN :ids` clause or a numeric LIMIT.

**How to avoid:** Always declare the bind map as `Map<String, Object>`. Convert UI strings to their real types (`Integer.valueOf`, `Date.valueOf`, `Id.valueOf` or just `Id`) before putting them in the map.

---

## Gotcha 3: `IN :collection` requires a `List` or `Set`, not a comma-separated `String`

**What happens:** Developers sometimes try to bind a single `String` like `'001xx,002yy,003zz'` to an `IN` clause, expecting the platform to split it. UNVERIFIED (2026-10-20): the outcome (empty result vs the `Invalid bind expression type … for column of type Id` error) The guide's own `IN` binds are collections — an Id list, a list of sObjects, a String list (apex dev guide 264 L10075-10084) — and never a delimited String.

**When it occurs:** When IDs arrive from a multi-select UI as a comma-separated string and the developer skips the parsing step.

**How to avoid:** Parse the input into `List<Id>` or `Set<Id>` before binding. The bind value for `IN :ids` must be the collection itself, not a serialized form.

---

## Gotcha 4: `AccessLevel.SYSTEM_MODE` silently bypasses FLS and CRUD

**What happens:** `Database.queryWithBinds(soql, binds, AccessLevel.SYSTEM_MODE)` ignores the running user's object and field-level permissions, and sharing follows the class keyword (apex dev guide 264 L11610-11612). UNVERIFIED (2026-10-20): "no warning, no log entry".

**When it occurs:** When a developer copy-pastes a working background-job example (which legitimately uses SYSTEM_MODE) into a user-facing controller, or when a `with sharing` class is mistakenly assumed to also enforce FLS: before API 67.0 system mode is the default and the sharing keyword governs only record-level access (L12138-12140); at API 67.0 and later Apex runs in user context by default (L11928-11929).

**How to avoid:** Default every `queryWithBinds` call to `AccessLevel.USER_MODE`. If `SYSTEM_MODE` is needed (system-context jobs, integrations, internal aggregations), require a code comment block explaining why. Code review should reject undocumented SYSTEM_MODE.

---

## Gotcha 5: `WITH USER_MODE` inside the dynamic query string does NOT replace allowlisting

**What happens:** Developers see `WITH USER_MODE` in a dynamic query and assume it makes the whole query safe. It enforces the running user's permissions, including on the WHERE clause (apex dev guide 264 L12154-12157), but it does NOT prevent injection into the WHERE clause, ORDER BY, or LIMIT.

**When it occurs:** When `WITH USER_MODE` (or the older `WITH SECURITY_ENFORCED`, which you can't use at API 67.0 and later, apex dev guide 264 L11926-11927) is added as a "security checkbox" without the rest of the bind/allowlist discipline.

**How to avoid:** Treat `WITH USER_MODE` / `AccessLevel.USER_MODE` as one layer (FLS enforcement). Treat binding and allowlisting as a separate, mandatory layer (parser-injection prevention). You need both.
