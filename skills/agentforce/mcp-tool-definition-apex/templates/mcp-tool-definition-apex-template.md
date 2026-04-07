# MCP Tool Definition in Apex — Work Template

Use this template when implementing a new McpToolDefinition subclass. Fill in each section before writing code.

## Scope

**Skill:** `mcp-tool-definition-apex`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before writing code:

- **Package installed:** (confirm `sf package installed list` shows salesforce-mcp-lib)
- **Tool name:** (snake_case identifier the MCP client will use to invoke this tool, e.g. `get_account_detail`)
- **Required parameters:** (name, JSON Schema type, description for each)
- **Optional parameters:** (name, JSON Schema type, description, default for each)
- **Return shape:** (map keys and types the tool returns to the MCP client)
- **Salesforce objects accessed:** (which objects the tool reads/writes)
- **Sharing context decision:** (default sharing / `with sharing` / `without sharing` — and why)
- **Governor limit concerns:** (any risk of hitting SOQL 100 / DML 150 / CPU 10s limits)

## Approach

Which pattern from SKILL.md applies?

- [ ] **Simple Record Lookup Tool** — AI provides an ID, tool returns structured record data
- [ ] **DML Write Tool** — AI provides field values, tool creates/updates records
- [ ] **Search/List Tool** — AI provides search criteria, tool returns list of matching records
- [ ] **Callout Tool** — Tool makes an outbound callout and returns external data
- [ ] **Other:** (describe)

**Rationale:** (why this pattern)

## Implementation Checklist

Copy from SKILL.md review checklist:

- [ ] Class uses `global` access modifier (`global class MyTool extends McpToolDefinition`)
- [ ] All overriding methods use `global override` (not `public override`)
- [ ] `inputSchema()` returns a valid JSON Schema Map with `'type' => 'object'`, `'properties'`, and `'required'`
- [ ] `validate()` checks all required params and returns `null` (not empty string) on success
- [ ] `execute()` uses SOQL bind variables for all user-supplied input (no string concatenation)
- [ ] `execute()` returns an explicit Map or List, not a raw SObject
- [ ] Tool registered in the Apex endpoint's `handlePost()` with `server.registerTool(new MyTool())`
- [ ] Apex test class written with at least 75% coverage

## Tool Skeleton

```apex
global class MyTool extends McpToolDefinition {

    global override Map<String, Object> inputSchema() {
        return new Map<String, Object>{
            'type' => 'object',
            'properties' => new Map<String, Object>{
                'paramOne' => new Map<String, Object>{
                    'type' => 'string',
                    'description' => 'Description of paramOne for the AI client'
                }
                // Add more properties here
            },
            'required' => new List<Object>{ 'paramOne' }
        };
    }

    global override String validate(Map<String, Object> params) {
        // Return null on success; return a non-null String error message on failure
        if (!params.containsKey('paramOne') || params.get('paramOne') == null) {
            return 'paramOne is required';
        }
        // Add additional format checks here
        return null;
    }

    global override Object execute(Map<String, Object> params) {
        String paramOne = (String) params.get('paramOne');

        // Use bind variables for all user input — never concatenate into SOQL
        List<Account> results = [SELECT Id, Name FROM Account WHERE Name = :paramOne LIMIT 10];

        if (results.isEmpty()) {
            return new Map<String, Object>{ 'found' => false, 'records' => new List<Object>() };
        }

        List<Map<String, Object>> records = new List<Map<String, Object>>();
        for (Account a : results) {
            records.add(new Map<String, Object>{ 'id' => a.Id, 'name' => a.Name });
        }
        return new Map<String, Object>{ 'found' => true, 'records' => records };
    }
}
```

## Registration in Apex Endpoint

Add this line inside the `handlePost()` method of the Apex REST endpoint class, before `server.handleRequest(...)`:

```apex
server.registerTool(new MyTool());
```

## Test Class Skeleton

```apex
@IsTest
private class MyToolTest {

    @IsTest
    static void testValidate_missingParam() {
        MyTool tool = new MyTool();
        String result = tool.validate(new Map<String, Object>());
        System.assertNotEquals(null, result, 'validate() should return an error for missing paramOne');
    }

    @IsTest
    static void testValidate_valid() {
        MyTool tool = new MyTool();
        String result = tool.validate(new Map<String, Object>{ 'paramOne' => 'TestValue' });
        System.assertEquals(null, result, 'validate() should return null for valid params');
    }

    @IsTest
    static void testExecute_noResults() {
        MyTool tool = new MyTool();
        Object result = tool.execute(new Map<String, Object>{ 'paramOne' => 'NonExistentValue_XYZ' });
        Map<String, Object> resultMap = (Map<String, Object>) result;
        System.assertEquals(false, resultMap.get('found'));
    }
}
```

## Deviations from Standard Pattern

(Record any deviations from the standard pattern and the reason for each deviation)
