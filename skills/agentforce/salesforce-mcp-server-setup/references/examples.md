# Examples — Salesforce MCP Server Setup

## Example 1: Install Apex Package and Verify

**Context:** Developer has a scratch org or sandbox and wants to install the salesforce-mcp-lib Apex package for the first time.

**Problem:** The package must be installed before any Apex endpoint class can reference McpServer or McpToolDefinition.

**Solution:**

```bash
# Install the 2GP unlocked package
sf package install \
  --package 04tdL000000So9xQAC \
  --target-org my-sandbox \
  --wait 10

# Confirm installation
sf package installed list --target-org my-sandbox
```

**Why it works:** The `--wait 10` flag blocks until installation completes (up to 10 minutes). Without it, the command exits immediately and you may attempt to deploy the endpoint class before Apex compilation finishes.

---

## Example 2: Minimal Apex REST Endpoint

**Context:** The Apex package is installed. You need an entry-point class for the npm proxy to POST to.

**Problem:** Without an Apex REST endpoint that calls `McpServer.handleRequest()`, all JSON-RPC requests return 404.

**Solution:**

```apex
@RestResource(urlMapping='/mcp/v1')
global class MyOrgMcpEndpoint {
    @HttpPost
    global static void handlePost() {
        McpServer server = new McpServer();
        server.registerTool(new MyRecordLookupTool());
        server.handleRequest(RestContext.request, RestContext.response);
    }
}
```

**Why it works:** `McpServer` (from the installed package) parses the incoming JSON-RPC 2.0 payload, dispatches to the registered tool whose name matches the `method` field, and writes the JSON-RPC response back to `RestContext.response`.

---

## Example 3: Claude Desktop Configuration (macOS)

**Context:** Connected App credentials are in hand. Wire Claude Desktop to call the Salesforce MCP server.

**Problem:** The `claude_desktop_config.json` must use the exact flag names the npm proxy expects. A single typo silently prevents tools from loading.

**Solution:** Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "npx",
      "args": [
        "-y",
        "salesforce-mcp-lib",
        "--instance-url", "https://your-org.my.salesforce.com",
        "--client-id", "YOUR_CONNECTED_APP_CLIENT_ID",
        "--client-secret", "YOUR_CONNECTED_APP_CLIENT_SECRET",
        "--endpoint", "/services/apexrest/mcp/v1"
      ]
    }
  }
}
```

**Why it works:** `npx -y salesforce-mcp-lib` downloads and runs the latest npm proxy package. The four flags map directly to the OAuth and HTTPS parameters the proxy needs; no additional config file is required.

---

## Example 4: Environment Variable Configuration

**Context:** You want to keep secrets out of the config file and share configuration across team members.

**Problem:** Embedding client secrets in `claude_desktop_config.json` risks accidental git exposure and makes secret rotation difficult.

**Solution:**

```bash
# .env file (gitignored)
SF_INSTANCE_URL=https://your-org.my.salesforce.com
SF_CLIENT_ID=3MVG9...
SF_CLIENT_SECRET=ABC123...
SF_ENDPOINT=/services/apexrest/mcp/v1
SF_LOG_LEVEL=info
```

Then in the config file, use a shell wrapper that loads the env file before executing:

```json
{
  "mcpServers": {
    "salesforce": {
      "command": "bash",
      "args": ["-c", "source ~/.salesforce-mcp.env && npx salesforce-mcp-lib"]
    }
  }
}
```

**Why it works:** The proxy reads all its parameters from environment variables when CLI flags are absent, allowing secret injection at shell startup without exposing values in the config file.

---

## Anti-Pattern: Hardcoding the Package Version in the Endpoint Class Name

**What practitioners do:** Name their endpoint class `McpEndpointV1` and add a `@RestResource(urlMapping='/mcp/v1')` annotation, then expect to update this class when the package upgrades.

**What goes wrong:** The McpServer dispatch logic lives entirely in the installed package's Apex classes, not in the endpoint class. The endpoint class is a thin wrapper. When the package upgrades, no changes to the endpoint class are typically required.

**Correct approach:** Keep the endpoint class minimal — instantiate `McpServer`, register tools, call `handleRequest`. All routing logic is inside the package and updates automatically when you reinstall a newer package version.
