# Salesforce MCP Server Setup — Work Template

Use this template when working on tasks in this area. Fill in each section before starting implementation.

## Scope

**Skill:** `salesforce-mcp-server-setup`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Answer the Before Starting questions from SKILL.md before proceeding:

- **Org API version:** (confirm `sf org display` shows API 65.0+ / Spring '25+)
- **Node.js version:** (confirm `node --version` shows >= 20)
- **Connected App status:** (new or existing? Client Credentials Flow enabled?)
- **Endpoint URL path:** (the `urlMapping` value in the Apex @RestResource class, e.g. `/mcp/v1`)
- **Package ID to install:** `04tdL000000So9xQAC` (verify against GitHub release page before production install)
- **MCP client:** (Claude Desktop, Cursor, ChatGPT, other)
- **Known constraints:** (sandbox only, PII concerns, shared org, etc.)

## Approach

Which pattern from SKILL.md applies?

- [ ] **Full Stack Setup** — Installing package + Apex endpoint + npm proxy + Claude Desktop config from scratch
- [ ] **Environment Variable Configuration** — Secrets via env vars for CI/CD-friendly or team-shared setup
- [ ] **Other:** (describe)

**Rationale:** (why this pattern over the alternatives)

## Implementation Checklist

Copy from SKILL.md review checklist:

- [ ] Apex package `04tdL000000So9xQAC` installed and confirmed via `sf package installed list`
- [ ] Apex REST endpoint deployed with `@RestResource` and `McpServer.handleRequest()` call
- [ ] Connected App has OAuth 2.0 Client Credentials Flow enabled and run-as user assigned
- [ ] npm proxy environment variables set (no hardcoded secrets in config files for production)
- [ ] MCP client (Claude Desktop / Cursor) shows registered tools in the tools panel
- [ ] `--log-level debug` tested and no authentication errors visible
- [ ] Run-as profile reviewed for minimum necessary object/field permissions

## Apex Endpoint Skeleton

```apex
@RestResource(urlMapping='/mcp/v1')
global class MyOrgMcpEndpoint {
    @HttpPost
    global static void handlePost() {
        McpServer server = new McpServer();
        // Register tools here:
        server.registerTool(new MyFirstTool());
        // Register resources or prompts if needed:
        // server.registerResource(new MyResource());
        server.handleRequest(RestContext.request, RestContext.response);
    }
}
```

## npm Proxy Config (Claude Desktop — macOS)

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "npx",
      "args": [
        "-y",
        "salesforce-mcp-lib",
        "--instance-url", "https://YOUR_ORG.my.salesforce.com",
        "--client-id", "YOUR_CONNECTED_APP_CLIENT_ID",
        "--client-secret", "YOUR_CONNECTED_APP_CLIENT_SECRET",
        "--endpoint", "/services/apexrest/mcp/v1"
      ]
    }
  }
}
```

**Config file location (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`

## Environment Variable Alternative

```bash
# ~/.salesforce-mcp.env  (add to .gitignore)
SF_INSTANCE_URL=https://YOUR_ORG.my.salesforce.com
SF_CLIENT_ID=YOUR_CONNECTED_APP_CLIENT_ID
SF_CLIENT_SECRET=YOUR_CONNECTED_APP_CLIENT_SECRET
SF_ENDPOINT=/services/apexrest/mcp/v1
SF_LOG_LEVEL=info
```

## Debugging Notes

- Use `--log-level debug` to see each JSON-RPC exchange in stderr
- 401 errors immediately after Connected App setup = propagation delay (wait up to 10 min)
- 404 errors = `--endpoint` path does not match `urlMapping` in the Apex class
- Tools not appearing in MCP client = check `handlePost()` has all `registerTool()` calls before `handleRequest()`

## Deviations from Standard Pattern

(Record any deviations from the standard pattern and the reason for each deviation)
