# Examples — MCP Tool Definition in Apex

## Example 1: Minimal Tool — Record Lookup by ID

**Context:** An AI agent in Claude Desktop needs to retrieve Account details by ID using an MCP tool call.

**Problem:** Without the correct `global` modifiers and a proper `inputSchema()`, the tool either fails to compile or fails to appear in the MCP client's tool list.

**Solution:**

```apex
global class GetAccountTool extends McpToolDefinition {
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
        List<Account> accounts = [SELECT Id, Name, Industry, Phone, BillingCity FROM Account WHERE Id = :accountId LIMIT 1];
        if (accounts.isEmpty()) return new Map<String, Object>{ 'found' => false };
        Account acc = accounts[0];
        return new Map<String, Object>{
            'found' => true,
            'id' => acc.Id,
            'name' => acc.Name,
            'industry' => acc.Industry,
            'phone' => acc.Phone,
            'billingCity' => acc.BillingCity
        };
    }
}
```

**Why it works:** Using a `List<Account>` query and checking `.isEmpty()` avoids the `QueryException` that a direct `[SELECT ... LIMIT 1]` assignment throws when no record matches. Returning a Map gives the MCP client a predictable response structure.

---

## Example 2: Tool with Enum-Constrained Input and DML

**Context:** An AI agent needs to create a Case with a validated priority field.

**Problem:** If the `priority` field accepts free-text, an invalid picklist value causes a DML error at runtime instead of a clean validation message before execution.

**Solution:**

```apex
global class CreateCaseTool extends McpToolDefinition {
    private static final Set<String> VALID_PRIORITIES = new Set<String>{ 'Low', 'Medium', 'High' };

    global override Map<String, Object> inputSchema() {
        return new Map<String, Object>{
            'type' => 'object',
            'properties' => new Map<String, Object>{
                'subject' => new Map<String, Object>{
                    'type' => 'string',
                    'description' => 'Case subject line'
                },
                'priority' => new Map<String, Object>{
                    'type' => 'string',
                    'enum' => new List<Object>{ 'Low', 'Medium', 'High' },
                    'description' => 'Case priority: Low, Medium, or High'
                },
                'description' => new Map<String, Object>{
                    'type' => 'string',
                    'description' => 'Detailed description of the issue'
                }
            },
            'required' => new List<Object>{ 'subject', 'priority' }
        };
    }

    global override String validate(Map<String, Object> params) {
        if (String.isBlank((String) params.get('subject'))) return 'subject cannot be blank';
        String priority = (String) params.get('priority');
        if (!VALID_PRIORITIES.contains(priority)) {
            return 'priority must be one of: Low, Medium, High';
        }
        return null;
    }

    global override Object execute(Map<String, Object> params) {
        Case c = new Case(
            Subject = (String) params.get('subject'),
            Priority = (String) params.get('priority'),
            Description = (String) params.get('description')
        );
        try {
            insert c;
            Case inserted = [SELECT CaseNumber FROM Case WHERE Id = :c.Id LIMIT 1];
            return new Map<String, Object>{ 'success' => true, 'caseId' => c.Id, 'caseNumber' => inserted.CaseNumber };
        } catch (DmlException e) {
            return new Map<String, Object>{ 'success' => false, 'error' => e.getDmlMessage(0) };
        }
    }
}
```

**Why it works:** The `enum` in `inputSchema()` tells the MCP client which values are valid so it can constrain user input. The `validate()` double-check guards against clients that ignore the schema. Catching `DmlException` and returning `success: false` gives the AI client actionable feedback without a raw exception stack trace.

---

## Example 3: Registering Multiple Tools in the Endpoint

**Context:** You have three tool classes and need to wire them all to the same Apex REST endpoint.

**Problem:** Forgetting to call `registerTool()` for a new tool class means it never appears in the MCP client tool list, with no error message.

**Solution:**

```apex
@RestResource(urlMapping='/mcp/v1')
global class MyOrgMcpEndpoint {
    @HttpPost
    global static void handlePost() {
        McpServer server = new McpServer();
        server.registerTool(new GetAccountTool());
        server.registerTool(new CreateCaseTool());
        server.registerTool(new SearchContactsTool());
        server.handleRequest(RestContext.request, RestContext.response);
    }
}
```

**Why it works:** Each `registerTool()` call adds the tool to the server's dispatch table keyed by the tool's name. The McpServer's `initialize` response includes the full list of registered tools, which is what the MCP client displays in the tools panel.

---

## Anti-Pattern: Returning Raw SObject from execute()

**What practitioners do:** `return [SELECT Id, Name FROM Account WHERE Id = :id LIMIT 1];`

**What goes wrong:** Raw SObject serialization includes internal metadata fields, relationship traversal artifacts, and type information that makes the JSON response opaque and inconsistent. The MCP client may receive unexpected fields that confuse the AI's interpretation of the result.

**Correct approach:** Always return a `Map<String, Object>` with explicitly chosen fields:

```apex
Account acc = accounts[0];
return new Map<String, Object>{
    'id' => acc.Id,
    'name' => acc.Name
};
```
