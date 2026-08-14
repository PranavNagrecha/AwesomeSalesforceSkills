# LLM Anti-Patterns — MCP Tool Definition in Apex

Common mistakes AI coding assistants make when generating or advising on MCP Tool Definition in Apex.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `public` Instead of `global` Access Modifier

**What the LLM generates:** `public class MyTool extends McpToolDefinition` and `public override Object execute(...)`.

**Why it happens:** LLMs default to `public` for Apex classes because it is correct for most org-level code. The `global` requirement for extending managed package abstract classes is a niche Salesforce rule that LLMs underrepresent.

**Correct pattern:**

```apex
global class MyTool extends McpToolDefinition {
    global override Map<String, Object> inputSchema() { ... }
    global override String validate(Map<String, Object> params) { ... }
    global override Object execute(Map<String, Object> params) { ... }
}
```

**Detection hint:** Any `McpToolDefinition` subclass with `public class` or `public override` in the method signatures is incorrect and will fail to compile.

---

## Anti-Pattern 2: Returning Empty String Instead of null from validate()

**What the LLM generates:** `return '';` or `return "";` at the end of a validate() method to indicate success.

**Why it happens:** LLMs trained on general programming patterns associate "no error" with an empty string return. In Java/C#/JavaScript, returning `""` to indicate "no error" is a common pattern.

**Correct pattern:**

```apex
global override String validate(Map<String, Object> params) {
    if (!params.containsKey('accountId')) return 'accountId is required';
    // ...
    return null; // MUST be null for success, not '' or ""
}
```

**Detection hint:** Any `return '';` or `return "";` in a validate() method is wrong. Search for `return ""` and `return ''` in McpToolDefinition subclasses.

---

## Anti-Pattern 3: Direct SObject Assignment from Single-Row SOQL

**What the LLM generates:**
```apex
Account acc = [SELECT Id, Name FROM Account WHERE Id = :id LIMIT 1];
```

**Why it happens:** This is the standard Apex pattern for single-row lookups and works correctly in most contexts. LLMs default to it without considering that the MCP tool receives unvalidated IDs from an AI client and may legitimately receive nonexistent or inaccessible record IDs.

**Correct pattern:**

```apex
List<Account> results = [SELECT Id, Name FROM Account WHERE Id = :id LIMIT 1];
if (results.isEmpty()) {
    return new Map<String, Object>{ 'found' => false, 'error' => 'Account not found' };
}
Account acc = results[0];
```

**Detection hint:** Any `SObject var = [SELECT ... WHERE Id = :param LIMIT 1]` pattern in an execute() method where the ID comes from user params is a QueryException risk.

---

## Anti-Pattern 4: String Concatenation in Dynamic SOQL

**What the LLM generates:**
```apex
String name = (String) params.get('name');
List<Account> results = Database.query('SELECT Id FROM Account WHERE Name = \'' + name + '\'');
```

**Why it happens:** LLMs often generate dynamic SOQL using string concatenation because it is the most direct translation from the conceptual query. The SOQL injection risk is well-documented but LLMs don't always apply it consistently when generating tool code.

**Correct pattern:**

```apex
String name = (String) params.get('name');
List<Account> results = [SELECT Id, Name FROM Account WHERE Name = :name];
// Or for truly dynamic SOQL with a variable field name:
String safeQuery = 'SELECT Id FROM Account WHERE Name = :name';
List<Account> results2 = Database.query(safeQuery); // bind variable :name still works
```

**Detection hint:** Any `'... = \'' + params.get(` or `"..." + userInput` in SOQL strings is a SOQL injection risk.

---

## Anti-Pattern 5: Putting Data Lookups Inside validate()

**What the LLM generates:**
```apex
global override String validate(Map<String, Object> params) {
    String accountId = (String) params.get('accountId');
    // checking if record exists
    Integer count = [SELECT COUNT() FROM Account WHERE Id = :accountId];
    if (count == 0) return 'Account not found';
    return null;
}
```

**Why it happens:** LLMs interpret "validate the inputs" broadly to include checking that referenced records exist. This is semantically reasonable but wastes SOQL governor limit budget before execute() runs.

**Correct pattern:**

```apex
global override String validate(Map<String, Object> params) {
    // Only syntactic/format checks here — no SOQL
    String accountId = (String) params.get('accountId');
    if (accountId == null || accountId.length() < 15) return 'accountId must be a valid Salesforce ID';
    return null;
}

global override Object execute(Map<String, Object> params) {
    String accountId = (String) params.get('accountId');
    List<Account> results = [SELECT Id, Name FROM Account WHERE Id = :accountId LIMIT 1];
    if (results.isEmpty()) return new Map<String, Object>{ 'found' => false };
    // ...
}
```

**Detection hint:** Any SOQL query inside a `validate()` method should be reviewed and moved to `execute()` unless there is a documented reason for the pre-execution check.

---

## Anti-Pattern 6: Returning Raw SObject from execute()

**What the LLM generates:**
```apex
global override Object execute(Map<String, Object> params) {
    String id = (String) params.get('id');
    return [SELECT Id, Name, Industry FROM Account WHERE Id = :id LIMIT 1];
}
```

**Why it happens:** It is the shortest path to returning record data. LLMs default to it because SObject implements Object and the return type is Object.

**Correct pattern:**

```apex
global override Object execute(Map<String, Object> params) {
    List<Account> results = [SELECT Id, Name, Industry FROM Account WHERE Id = :params.get('id') LIMIT 1];
    if (results.isEmpty()) return new Map<String, Object>{ 'found' => false };
    Account acc = results[0];
    return new Map<String, Object>{
        'id' => acc.Id,
        'name' => acc.Name,
        'industry' => acc.Industry
    };
}
```

**Detection hint:** Any `return [SELECT ...]` that directly returns a SOQL result from execute() is the anti-pattern.

---

## Anti-Pattern 7: Omitting the Access Modifier Entirely on an `abstract` or `override` Method

**What the LLM generates:**
```apex
global abstract class BaseOrgTool extends McpToolDefinition {
    abstract Map<String, Object> buildSchema();   // no modifier
    override Object execute(Map<String, Object> params) { ... }  // no modifier
}
```

**Why it happens:** For a decade Apex accepted a bare `abstract`/`override` method and defaulted it to private, so the pattern is all over the training data. Models also describe the omission as harmless ("defaults to private"), which was true then and is not now.

**Correct pattern:** Winter '26 tightened this. Per the Winter '26 developer release guide, *"In API version 65.0 and later, `abstract` and `override` methods require a `protected`, `public`, or `global` access modifier."* Declare one explicitly — for MCP tool classes that means `global`, since the base methods are `global abstract`:

```apex
global abstract class BaseOrgTool extends McpToolDefinition {
    global abstract Map<String, Object> buildSchema();
    global override Object execute(Map<String, Object> params) { ... }
}
```

**Detection hint:** Grep for a line starting with `abstract ` or `override ` at method position with no preceding `protected`/`public`/`global`. The gate is the `apiVersion` in the class's `.cls-meta.xml`, not the org's release, so the same file compiles at 64.0 and fails at 65.0 — when a user reports a base class that "suddenly stopped compiling," check for an API version bump before hunting for a code change. `scripts/check_mcp_tool_definition_apex.py` flags this as check 2b.
