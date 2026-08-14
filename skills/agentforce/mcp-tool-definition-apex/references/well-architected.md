# Well-Architected Notes — MCP Tool Definition in Apex

## Relevant Pillars

- **Security** — Tools expose Salesforce data to AI clients. SOQL injection via user-supplied params is the primary injection risk. Every tool must use SOQL bind variables. The tool's sharing context (run-as user of the Connected App) must be understood and documented. Overly permissive tools can become data exfiltration channels.
- **Reliability** — Tools must handle edge cases gracefully (no matching records, DML errors, governor limit proximity) without throwing unhandled exceptions. The McpServer may not gracefully handle an unhandled Apex exception, resulting in a malformed JSON-RPC response that confuses the MCP client.

## Architectural Tradeoffs

**Narrow vs. broad tools:** A single "search_all_objects" tool that accepts arbitrary SOQL is maximally flexible but creates an uncontrolled data access surface. Prefer narrow, purpose-specific tools (one tool per operation, one tool per object type) that enforce their own scope boundaries through validate() and explicit field lists in SOQL. Narrow tools are easier to test, easier to audit, and less likely to be misused by AI clients.

**validate() data checks vs. execute() error returns:** Checking whether a referenced record exists in validate() costs a SOQL query before execute() even runs. For most tools, it is better to let execute() do the lookup and return `{ success: false, error: 'record not found' }` as a structured response. The MCP client receives actionable feedback either way; the validate()-as-data-check pattern wastes governor limit budget unnecessarily.

**Hand-rolled tool class vs. Salesforce-hosted custom server:** The `salesforce-mcp-lib` route puts the protocol, the endpoint, and the authorization surface in your own Apex — maximum control, and a Connected App run-as user whose sharing context you have to reason about yourself. Salesforce Hosted MCP Servers (GA 29 April 2026) invert that. A custom server declares tools over Flows, Apex Invocable Actions (`@InvocableMethod`), `@AuraEnabled` methods, Apex REST methods (`@RestResource`), or API Catalog APIs, and the platform — not your endpoint code — establishes the caller: the GA announcement states that *"Every MCP transaction runs with the authenticated user's identity, permissions, and accountability,"* and the Flows guide repeats it for the Flow-backed case (execution runs as the authenticated user, not as a system context). That is the stronger Security default. Neither route relaxes governor limits — the Flows guide notes for Flow-backed tools that *"Governor limits apply. Flows invoked via MCP consume Apex and DML limits the same as flows triggered from the UI or Apex,"* and the hand-rolled endpoint is an ordinary synchronous Apex REST transaction with the same per-transaction budget. The cost of the hosted route is control over the wire format, so keep `McpToolDefinition` when you need a custom JSON-RPC error shape, a hand-built `inputSchema()`, or an endpoint that ships inside your own package.

Whichever route the tool takes, the FLS and sharing idiom *inside* the tool body is gated on the `apiVersion` in that class's `.cls-meta.xml`, not on the org's release — a Summer '26 org runs a tool class pinned to 58.0 with the old system-mode defaults. Canonical table: [`agents/_shared/AGENT_CONTRACT.md` → Apex security idiom by API version](../../../../agents/_shared/AGENT_CONTRACT.md#apex-security-idiom-by-api-version). Read it rather than assuming user mode from the org's release.

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
- The Salesforce Developer's Guide to the Winter '26 Release — https://developer.salesforce.com/blogs/2025/09/winter26-developers — confirms that in API version 65.0 and later, `abstract` and `override` methods require a `protected`, `public`, or `global` access modifier, and that omitting one is a compilation error (verified 2026-08-13)
- Hosted MCP Servers: Flows as MCP Tools — https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide/flows.html — confirms that only autolaunched flows can be exposed as MCP tools, that flow execution runs as the authenticated user rather than a system context, and that governor limits apply identically to UI- and Apex-triggered flows (verified 2026-08-13)
- Hosted MCP Servers: Build Custom MCP Servers — https://developer.salesforce.com/docs/platform/hosted-mcp-servers/guide/custom-servers.html — confirms the set of assets a custom MCP tool can be backed by: Flows, Apex Invocable Actions, AuraEnabled Apex methods, Apex REST methods, and APIs from API Catalog. Does NOT state how a tool's parameter schema is derived, and does NOT state an edition or user-context requirement (verified 2026-08-14)
- Salesforce Hosted MCP Servers Are Now Generally Available — https://developer.salesforce.com/blogs/2026/04/salesforce-hosted-mcp-servers-are-now-generally-available — dated 29 April 2026; confirms GA and that "Every MCP transaction runs with the authenticated user's identity, permissions, and accountability" (verified 2026-08-14)
- The Salesforce Developer's Guide to the Summer '26 Release — https://developer.salesforce.com/blogs/2026/06/the-salesforce-developers-guide-to-the-summer-26-release — confirms the Summer '26 attribution for the Flow-backed form: "Lightning Flows: Expose autolaunched flows as MCP tools" (verified 2026-08-14)
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
