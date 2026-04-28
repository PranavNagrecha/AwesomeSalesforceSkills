# Gotchas — Apex Dynamic SOQL Binding Safety

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `Database.query` bind variables must be in lexical scope at the call site

**What happens:** `Database.query('SELECT Id FROM Account WHERE Name = :term')` resolves `:term` against the local variables visible to the executing method. A class field named `term` does NOT always work; a variable in the caller never works. The error is `System.QueryException: Variable does not exist: term`, raised at runtime, not at compile time.

**When it occurs:** Most often after a refactor that splits a query into a helper method without realising the helper does not see the caller's locals. Also bites when a class field is shadowed or named the same as something the resolver would not pick up.

**How to avoid:** Use `Database.queryWithBinds(query, Map<String, Object> binds, AccessLevel level)` whenever the query is not built and executed in the same method body. The bind map is explicit and travels with the query string across method boundaries.

---

## Gotcha 2: `Database.queryWithBinds` requires `Map<String, Object>`, not `Map<String, String>`

**What happens:** A `Map<String, String>` compiles fine because `queryWithBinds` accepts a `Map<String, Object>` and Apex covariance permits the call. At runtime, when a bind needs an `Integer` (LIMIT), `Date`, `Id`, or `List<Id>` (IN clause), the bind fails — typically as `System.TypeException` or a generic `QueryException` complaining about the type.

**When it occurs:** When developers reach for `Map<String, String>` as the "obvious" filter map (since values often arrive as strings from the UI), then later add an `IN :ids` clause or a numeric LIMIT.

**How to avoid:** Always declare the bind map as `Map<String, Object>`. Convert UI strings to their real types (`Integer.valueOf`, `Date.valueOf`, `Id.valueOf` or just `Id`) before putting them in the map.

---

## Gotcha 3: `IN :collection` requires a `List` or `Set`, not a comma-separated `String`

**What happens:** Developers sometimes try to bind a single `String` like `'001xx,002yy,003zz'` to an `IN` clause, expecting the platform to split it. The query either returns nothing or throws `Invalid bind expression type ... for column of type Id`.

**When it occurs:** When IDs arrive from a multi-select UI as a comma-separated string and the developer skips the parsing step.

**How to avoid:** Parse the input into `List<Id>` or `Set<Id>` before binding. The bind value for `IN :ids` must be the collection itself, not a serialized form.

---

## Gotcha 4: `AccessLevel.SYSTEM_MODE` silently bypasses FLS and CRUD

**What happens:** `Database.queryWithBinds(soql, binds, AccessLevel.SYSTEM_MODE)` returns rows and fields the running user is not entitled to see. There is no warning, no log entry, no telltale exception — just a security regression compared to USER_MODE.

**When it occurs:** When a developer copy-pastes a working background-job example (which legitimately uses SYSTEM_MODE) into a user-facing controller, or when a `with sharing` class is mistakenly assumed to also enforce FLS (it does not — `with sharing` is record visibility only).

**How to avoid:** Default every `queryWithBinds` call to `AccessLevel.USER_MODE`. If `SYSTEM_MODE` is needed (system-context jobs, integrations, internal aggregations), require a code comment block explaining why. Code review should reject undocumented SYSTEM_MODE.

---

## Gotcha 5: `WITH USER_MODE` inside the dynamic query string does NOT replace allowlisting

**What happens:** Developers see `WITH USER_MODE` in a dynamic query and assume it makes the whole query safe. It only restricts the FIELDS the query can return; it does NOT prevent injection into the WHERE clause, ORDER BY, or LIMIT.

**When it occurs:** When `WITH USER_MODE` (or the older `WITH SECURITY_ENFORCED`) is added as a "security checkbox" without the rest of the bind/allowlist discipline.

**How to avoid:** Treat `WITH USER_MODE` / `AccessLevel.USER_MODE` as one layer (FLS enforcement). Treat binding and allowlisting as a separate, mandatory layer (parser-injection prevention). You need both.
