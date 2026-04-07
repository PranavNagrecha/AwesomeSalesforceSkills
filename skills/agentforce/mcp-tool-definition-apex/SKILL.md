---
name: mcp-tool-definition-apex
description: "Use this skill to implement custom Apex MCP tool classes by extending McpToolDefinition from the salesforce-mcp-lib package. Covers inputSchema(), validate(), and execute() override patterns, JSON schema construction, SOQL and DML inside tools, error handling, and tool registration in the Apex REST endpoint. Trigger keywords: McpToolDefinition, extend McpToolDefinition, Apex MCP tool, mcp-tool Apex, JSON-RPC tool, salesforce-mcp-lib tool class. NOT for the initial server installation and proxy setup (see salesforce-mcp-server-setup), NOT for MCP Resources or Prompts, NOT for OmniStudio or Flow-based tool definitions."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "How do I write a custom Apex class that the MCP server can call as a tool?"
  - "I need to implement McpToolDefinition and override execute() with real Salesforce logic"
  - "How do I define the inputSchema for an MCP tool in Apex?"
  - "My MCP tool validate() method needs to check required params before execute() runs"
  - "I want to expose a SOQL query or Apex DML operation as an MCP tool for Claude"
tags:
  - mcp
  - agentforce
  - salesforce-mcp-lib
  - apex
  - json-rpc
  - tool-definition
  - mcptooldefinition
inputs:
  - salesforce-mcp-lib 2GP Apex package installed in the target org
  - Apex REST endpoint class already scaffolded (from salesforce-mcp-server-setup)
  - "Clear definition of what the tool does — its name, required parameters, and return value"
  - Knowledge of which Salesforce objects and fields the tool needs to access
outputs:
  - Apex class extending McpToolDefinition with inputSchema(), validate(), and execute() implemented
  - Tool registered in the Apex REST endpoint via server.registerTool(new MyTool())
  - Apex test class covering validate() branches and execute() happy path
  - Review checklist confirming SOQL injection safety, sharing context, and governor limit awareness
dependencies:
  - salesforce-mcp-server-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# MCP Tool Definition in Apex

This skill activates when a practitioner needs to write Apex code that extends the `McpToolDefinition` abstract class from the salesforce-mcp-lib package to expose custom Salesforce org logic — SOQL queries, DML, callouts, or complex business calculations — as callable tools to an MCP-capable AI client such as Claude Desktop or Cursor.

The salesforce-mcp-lib package defines three overrideable methods that together form a complete tool contract. Getting each of these right is the central challenge this skill addresses.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Package installed**: Confirm `sf package installed list --target-org YOUR_ORG` shows salesforce-mcp-lib. The McpToolDefinition class will not exist without it.
- **Tool contract**: Before writing code, define: (1) the tool name (snake_case, used by the MCP client to invoke the tool), (2) every required and optional parameter with its JSON Schema type, (3) what the tool returns and in what shape.
- **Governor limits**: Each MCP tool invocation is a single Apex transaction. SOQL limits (100 queries per transaction), DML limits (150 statements), CPU time (10s synchronous), and heap size (6MB synchronous) all apply. Tools that need more resources must use asynchronous Apex patterns, but the `execute()` method is synchronous — async results must be polled in a subsequent tool call.
- **Sharing context**: The tool runs as the Connected App's run-as user. Understand whether the tool should use that user's sharing context or bypass it.

---

## Core Concepts

### The Three-Method Contract

Every `McpToolDefinition` subclass must override three methods:

**`inputSchema()`** — Returns a `Map<String, Object>` that is a valid JSON Schema object describing the tool's parameters. The MCP client uses this schema to populate the tool call's arguments and to validate user input before sending. The minimum required structure is `{ 'type' => 'object', 'properties' => { ... }, 'required' => [...] }`.

**`validate(Map<String, Object> params)`** — Called by the McpServer before `execute()`. Return `null` if params are valid. Return a non-null String error message if validation fails — the McpServer will return a JSON-RPC error response to the client without calling `execute()`. This is the correct place for required-field checks, format validation, and SOQL injection defense.

**`execute(Map<String, Object> params)`** — Called only if `validate()` returns `null`. Contains the actual Salesforce logic. Return any serializable Object (Map, List, SObject, String, Integer). The McpServer serializes the return value to JSON and wraps it in the JSON-RPC 2.0 response.

### JSON Schema for inputSchema()

The `inputSchema()` return value must be a valid JSON Schema object. Salesforce Apex does not have a JSON Schema library, so you construct it as nested `Map<String, Object>` and `List<Object>` literals:

```apex
global override Map<String, Object> inputSchema() {
    return new Map<String, Object>{
        'type' => 'object',
        'properties' => new Map<String, Object>{
            'recordId' => new Map<String, Object>{
                'type' => 'string',
                'description' => '18-character Salesforce Account ID'
            },
            'includeContacts' => new Map<String, Object>{
                'type' => 'boolean',
                'description' => 'Whether to include related Contacts in the response'
            }
        },
        'required' => new List<Object>{ 'recordId' }
    };
}
```

Note that `required` is a `List<Object>`, not `List<String>`. JSON serialization requires `Object` to avoid type coercion errors in some Apex JSON serializers.

### The Global Access Modifier Requirement

All overriding methods in a class that extends a global abstract class from a managed package must also use the `global` access modifier. Using `public override` will cause a compile error because the base class methods are `global abstract`.

---

## Common Patterns

### Pattern: Simple Record Lookup Tool

**When to use:** The most common MCP tool pattern — the AI agent provides a record ID and the tool returns structured data about the record.

**How it works:**

```apex
global class AccountDetailTool extends McpToolDefinition {
    global override Map<String, Object> inputSchema() {
        return new Map<String, Object>{
            'type' => 'object',
            'properties' => new Map<String, Object>{
                'accountId' => new Map<String, Object>{
                    'type' => 'string',
                    'description' => '18-character Salesforce Account ID'
                }
            },
            'required' => new List<Object>{ 'accountId' }
        };
    }

    global override String validate(Map<String, Object> params) {
        if (!params.containsKey('accountId')) return 'accountId is required';
        String id = (String) params.get('accountId');
        if (id == null || id.length() < 15) return 'accountId must be a valid Salesforce ID';
        return null;
    }

    global override Object execute(Map<String, Object> params) {
        String accountId = (String) params.get('accountId');
        Account acc = [SELECT Id, Name, Industry, AnnualRevenue, Phone
                       FROM Account WHERE Id = :accountId LIMIT 1];
        return new Map<String, Object>{
            'id' => acc.Id,
            'name' => acc.Name,
            'industry' => acc.Industry,
            'annualRevenue' => acc.AnnualRevenue,
            'phone' => acc.Phone
        };
    }
}
```

**Why not the alternative:** Returning the raw SObject is tempting but fragile — JSON serialization of SObjects includes all queried fields and relationship metadata that confuses the MCP client. Return an explicit Map instead.

### Pattern: DML Write Tool with Explicit Error Handling

**When to use:** The AI agent needs to create or update Salesforce records based on conversation context.

**How it works:**

```apex
global class CreateCaseTool extends McpToolDefinition {
    global override Map<String, Object> inputSchema() {
        return new Map<String, Object>{
            'type' => 'object',
            'properties' => new Map<String, Object>{
                'subject' => new Map<String, Object>{ 'type' => 'string', 'description' => 'Case subject line' },
                'accountId' => new Map<String, Object>{ 'type' => 'string', 'description' => 'Related Account ID' },
                'priority' => new Map<String, Object>{
                    'type' => 'string',
                    'enum' => new List<Object>{ 'Low', 'Medium', 'High' },
                    'description' => 'Case priority'
                }
            },
            'required' => new List<Object>{ 'subject' }
        };
    }

    global override String validate(Map<String, Object> params) {
        if (!params.containsKey('subject') || String.isBlank((String) params.get('subject'))) {
            return 'subject is required and cannot be blank';
        }
        return null;
    }

    global override Object execute(Map<String, Object> params) {
        Case c = new Case();
        c.Subject = (String) params.get('subject');
        if (params.containsKey('accountId')) c.AccountId = (String) params.get('accountId');
        if (params.containsKey('priority')) c.Priority = (String) params.get('priority');
        try {
            insert c;
            return new Map<String, Object>{ 'success' => true, 'caseId' => c.Id, 'caseNumber' => [SELECT CaseNumber FROM Case WHERE Id = :c.Id].CaseNumber };
        } catch (DmlException e) {
            return new Map<String, Object>{ 'success' => false, 'error' => e.getDmlMessage(0) };
        }
    }
}
```

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Tool needs a single required param | Put it in `required` list in inputSchema() and check in validate() | validate() prevents execute() from running with missing params |
| Tool does SOQL with user-supplied input | Bind the variable with `:variable` syntax in SOQL | Prevents SOQL injection; never concatenate user input into SOQL strings |
| Tool needs to return a list of records | Return a `List<Map<String, Object>>` | Cleaner than returning raw SObject lists and avoids serialization surprises |
| Tool execution might hit governor limits | Design tool to be narrow in scope; one tool per operation | Governor limits apply per transaction; splitting logic across multiple tool calls is safer |
| Tool needs enum-constrained input | Add `'enum' => new List<Object>{ ... }` to the property in inputSchema() | MCP client validates against enum before calling; validate() can double-check |
| Tool result includes currency or date fields | Format as String with explicit format | JSON has no Currency or Date types; Apex auto-serializes to ISO 8601 for Dates |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Define the tool contract** — before writing code, write out: the tool name (snake_case string returned by `getName()`), every parameter (name, JSON Schema type, required/optional, description), and the expected return shape (map keys, types).
2. **Implement `inputSchema()`** — construct the JSON Schema Map using `Map<String, Object>` literals. Include a `description` field for every property — MCP clients use this to explain the tool to the AI.
3. **Implement `validate()`** — check all required fields are present and non-null. Check formats (e.g. Salesforce ID length). Check enum values. Return a descriptive error string on failure; return `null` on success.
4. **Implement `execute()`** — write the SOQL/DML/callout logic. Use bind variables for all user input. Wrap DML in try/catch. Return an explicit Map rather than a raw SObject.
5. **Register the tool** — add `server.registerTool(new MyTool())` inside the Apex REST endpoint's `handlePost()` method before calling `handleRequest()`.
6. **Write an Apex test** — test `validate()` with missing params and invalid values. Test `execute()` with a mock record. Confirm at least 75% coverage on the tool class.
7. **Smoke-test via MCP client** — restart Claude Desktop, find the tool in the tools panel, run it with a real record ID, and confirm the response shape is correct.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Class uses `global` access modifier and all overriding methods use `global override`
- [ ] `inputSchema()` returns a valid JSON Schema with `type: object`, `properties`, and `required`
- [ ] `validate()` checks all required params and returns `null` (not empty string) on success
- [ ] `execute()` uses SOQL bind variables for all user-supplied input (no string concatenation)
- [ ] `execute()` returns an explicit Map or List, not a raw SObject
- [ ] Tool registered in the Apex endpoint's `handlePost()` method
- [ ] Apex test class written with at least 75% coverage

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`null` vs empty string in validate()** — The McpServer treats `null` return from `validate()` as success and any non-null String as a validation error. Returning an empty string `''` is treated as an error with an empty message — not as success. Always return `null` explicitly when validation passes.
2. **SOQL query with no results throws exception** — If `execute()` does `[SELECT ... WHERE Id = :id LIMIT 1]` and no record matches, Apex throws `System.QueryException: List has no rows for assignment`. Wrap single-record queries in a `List<SObject>` query and check `.isEmpty()` before accessing `[0]`.
3. **JSON serialization of SObjects** — Returning an `Account` or `Case` sObject directly from `execute()` will serialize correctly in basic cases but will include unexpected fields and relationship metadata if the object has been populated through relationship traversal. Always return an explicit `Map<String, Object>` to control the response shape.
4. **Governor limits per tool call** — Each MCP tool invocation is a single Apex transaction. If the tool does two SOQL queries (one in `validate()` and one in `execute()`), both count against the 100 SOQL query limit. Design validate() to do format checks only; do data lookups in execute().

---

## Output Artifacts

| Artifact | Description |
|---|---|
| McpToolDefinition Apex class | The tool implementation with inputSchema, validate, and execute |
| Updated Apex REST endpoint | The endpoint class with server.registerTool(new MyTool()) added |
| Apex test class | Test coverage for validate() branches and execute() happy path |

---

## Related Skills

- salesforce-mcp-server-setup — prerequisite: install the Apex package and configure the npm proxy before writing tool classes
- agentforce/custom-agent-actions-apex — native Agentforce Agent Actions as an alternative when MCP protocol compatibility is not required

---

## Official Sources Used

- salesforce-mcp-lib GitHub (MIT) — https://github.com/Damecek/salesforce-mcp-lib
- Apex Developer Guide: Apex REST Web Services — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest.htm
- Apex Developer Guide: Governor Execution Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- JSON Schema specification — https://json-schema.org/understanding-json-schema/
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
