# Gotchas — MCP Tool Definition in Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: validate() Returning Empty String Counts as an Error

**What happens:** If `validate()` returns `''` (empty string) instead of `null`, the McpServer treats it as a validation failure and returns a JSON-RPC error response to the MCP client with an empty error message. The tool's `execute()` method is never called.

**When it occurs:** When a developer writes `return '';` as a "no-op" success return, or when a conditional validation block falls through without an explicit `return null`.

**How to avoid:** Always return `null` (the Apex keyword, not the string `'null'`) for a successful validation. Code review for any `return '';` or `return "";` in validate() methods.

---

## Gotcha 2: QueryException on Single-Row SOQL Assignment

**What happens:** `Account acc = [SELECT Id FROM Account WHERE Id = :id LIMIT 1];` throws `System.QueryException: List has no rows for assignment to SObject` when the query returns zero rows.

**When it occurs:** Any time the provided record ID does not exist in the org, was deleted, or is outside the run-as user's sharing context. This is a runtime exception, not a validation error — so it propagates as an unhandled exception through McpServer and may return a malformed JSON-RPC error response.

**How to avoid:** Always query into a `List<SObject>` and check `.isEmpty()` before accessing the first element:

```apex
List<Account> results = [SELECT Id, Name FROM Account WHERE Id = :id LIMIT 1];
if (results.isEmpty()) return new Map<String, Object>{ 'found' => false };
Account acc = results[0];
```

---

## Gotcha 3: SOQL Injection via String Concatenation in execute()

**What happens:** If user-supplied `params` values are concatenated into a SOQL string (e.g. `'SELECT Id FROM Account WHERE Name = \'' + name + '\''`), a malicious or careless MCP client can inject arbitrary SOQL clauses, potentially exfiltrating data the tool was not designed to expose.

**When it occurs:** Whenever dynamic SOQL is used without bind variables.

**How to avoid:** Always use bind variables for user-supplied values:

```apex
String name = (String) params.get('name');
List<Account> results = [SELECT Id, Name FROM Account WHERE Name = :name];
```

If a dynamic field name (not value) is required, use Schema.SObjectType reflection to validate the field name against the org's schema before constructing the dynamic SOQL string.

---

## Gotcha 4: Governor Limits Accumulate Across validate() and execute()

**What happens:** SOQL queries in `validate()` count against the same per-transaction limit as queries in `execute()`. A tool that does two SOQL queries in `validate()` (e.g. to check if a referenced record exists) and three in `execute()` has already used 5 of the 100 SOQL query limit before any business logic runs. In a worst-case scenario with many tool registrations and a complex tool chain, the limit can be reached unexpectedly.

**When it occurs:** When validate() performs database lookups instead of staying limited to format and null checks.

**How to avoid:** Keep `validate()` focused on syntactic and format validation only (null checks, string length, regex, enum membership). Do all data lookups in `execute()`. If a reference check (does this ID exist?) is truly necessary, do it once in `execute()` and return an error result rather than a validation error.

---

## Gotcha 5: Tool Name Collision Silently Overwrites Earlier Tool

**What happens:** If two `registerTool()` calls register tools with the same name, the second registration silently overwrites the first in the McpServer's dispatch table. The first tool becomes unreachable with no error at registration time.

**When it occurs:** When multiple tool classes return the same value from `getName()` — either by accident (copy-paste) or by design (trying to "override" a tool without removing the old registration).

**How to avoid:** Ensure each `McpToolDefinition` subclass returns a unique name from `getName()`. Use a naming convention like `domain_action_object` (e.g. `crm_create_case`, `crm_get_account`) to reduce collision risk. Grep the codebase for duplicate `getName()` return values before adding a new tool.
