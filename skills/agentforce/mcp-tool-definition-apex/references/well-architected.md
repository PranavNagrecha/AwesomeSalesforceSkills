# Well-Architected Notes — MCP Tool Definition in Apex

## Relevant Pillars

- **Security** — Tools expose Salesforce data to AI clients. SOQL injection via user-supplied params is the primary injection risk. Every tool must use SOQL bind variables. The tool's sharing context (run-as user of the Connected App) must be understood and documented. Overly permissive tools can become data exfiltration channels.
- **Reliability** — Tools must handle edge cases gracefully (no matching records, DML errors, governor limit proximity) without throwing unhandled exceptions. The McpServer may not gracefully handle an unhandled Apex exception, resulting in a malformed JSON-RPC response that confuses the MCP client.

## Architectural Tradeoffs

**Narrow vs. broad tools:** A single "search_all_objects" tool that accepts arbitrary SOQL is maximally flexible but creates an uncontrolled data access surface. Prefer narrow, purpose-specific tools (one tool per operation, one tool per object type) that enforce their own scope boundaries through validate() and explicit field lists in SOQL. Narrow tools are easier to test, easier to audit, and less likely to be misused by AI clients.

**validate() data checks vs. execute() error returns:** Checking whether a referenced record exists in validate() costs a SOQL query before execute() even runs. For most tools, it is better to let execute() do the lookup and return `{ success: false, error: 'record not found' }` as a structured response. The MCP client receives actionable feedback either way; the validate()-as-data-check pattern wastes governor limit budget unnecessarily.

**Synchronous vs. asynchronous execution:** MCP tools execute synchronously within the Apex REST request. Long-running operations (batch processing, large data exports, complex calculations) will hit the 10-second CPU time limit or heap limits. The architectural solution is to design long-running tools in two parts: a "start" tool that enqueues an async job and returns a job ID, and a "check" tool that polls the job status. The MCP client orchestrates the polling loop.

## Anti-Patterns

1. **Dynamic SOQL with string concatenation** — Building SOQL strings by concatenating user-supplied params values creates a SOQL injection vulnerability. The tool appears to work correctly in development (where inputs are well-formed) but is exploitable in production. Always use bind variables.

2. **Returning raw SObjects from execute()** — Serializing SObjects directly creates an unpredictable response shape because Apex JSON serialization of SObjects includes relationship traversal data, type metadata, and null fields. The MCP client receives a confusing and inconsistently structured response. Return explicit `Map<String, Object>` instances with controlled field lists.

3. **Placing all business logic in one mega-tool** — A single tool that accepts an `operation` parameter and branches on it in execute() is difficult to test, impossible to document accurately in inputSchema(), and impossible to scope with sharing rules. Separate concerns into individual tool classes.

## Official Sources Used

- salesforce-mcp-lib GitHub (MIT) — https://github.com/Damecek/salesforce-mcp-lib
- Apex Developer Guide: Apex REST Web Services — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest.htm
- Apex Developer Guide: Governor Execution Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Apex Developer Guide: SOQL Injection — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_security_soql_injection.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
