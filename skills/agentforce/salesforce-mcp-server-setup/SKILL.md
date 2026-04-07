---
name: salesforce-mcp-server-setup
description: "Use this skill to install and configure the salesforce-mcp-lib Apex package and npm stdio proxy so that an MCP client (Claude Desktop, Cursor, ChatGPT) can call Salesforce org data and logic via the Model Context Protocol. Trigger keywords: MCP server, salesforce-mcp-lib, Claude Desktop Salesforce, MCP proxy setup, Apex JSON-RPC, MCP Connected App. NOT for Salesforce Hosted MCP Servers (Agentforce-native hosted endpoints), NOT for Flow-based tool definitions, NOT for OmniStudio integrations."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
triggers:
  - "How do I connect Claude Desktop to my Salesforce org using MCP?"
  - "How do I install salesforce-mcp-lib and wire up the npm proxy to my org?"
  - "I want AI agents to call Salesforce Apex logic over the Model Context Protocol"
  - "Setting up a JSON-RPC MCP server inside a Salesforce org with Apex"
  - "Configure Connected App OAuth for salesforce-mcp-lib client credentials flow"
tags:
  - mcp
  - agentforce
  - salesforce-mcp-lib
  - json-rpc
  - apex
  - oauth
  - connected-app
  - claude-desktop
inputs:
  - Target Salesforce org (sandbox or production) with API 65.0+ (Spring '25+)
  - Node.js >= 20 installed on the machine running the npm proxy
  - Connected App Client ID and Client Secret with OAuth 2.0 Client Credentials flow enabled
  - The Apex REST endpoint URL path you intend to expose (e.g. /services/apexrest/mcp/v1)
outputs:
  - Installed salesforce-mcp-lib 2GP Apex package in the target org
  - Working Apex REST endpoint that handles JSON-RPC 2.0 MCP requests
  - Configured npm proxy (salesforce-mcp-lib) with correct environment variables
  - Claude Desktop or Cursor mcp.json / mcp_settings.json wiring
  - Security checklist confirming OAuth scopes, profile permissions, and sharing rules
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-07
---

# Salesforce MCP Server Setup

This skill activates when a practitioner needs to install the salesforce-mcp-lib open-source package (MIT license, https://github.com/Damecek/salesforce-mcp-lib) and configure its two-component architecture — the Apex 2GP unlocked package running inside the org plus the Node.js stdio proxy running on the developer machine — so that an MCP-capable AI client such as Claude Desktop or Cursor can call Salesforce org data and business logic through the standardized Model Context Protocol.

This is not a hosted Salesforce feature. It is a developer-operated, self-hosted bridge.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Org API version**: salesforce-mcp-lib requires API 65.0+ (Spring '25+). Confirm with `sf org display --target-org YOUR_ORG`.
- **Node.js version**: The npm proxy requires Node.js >= 20. Run `node --version` to confirm.
- **Connected App**: You need a Connected App with OAuth 2.0 Client Credentials Flow enabled. The proxy authenticates as a service account — not as a named user — so no user interaction or browser login is involved.
- **Endpoint URL**: You must write one Apex REST class that serves as the MCP entry point. The URL mapping you choose (e.g. `/mcp/v1`) becomes the `--endpoint` flag value.
- **Package ID**: The current installable 2GP Apex package ID is `04tdL000000So9xQAC`. Always verify against the GitHub release page before installing in production.

---

## Core Concepts

### Two-Component Architecture

salesforce-mcp-lib splits into an org-side Apex component and a client-side Node.js component. Neither works without the other.

- **Apex package (org-side)**: A 2GP unlocked package containing 54 Apex classes. It implements a JSON-RPC 2.0 server that runs entirely inside the Salesforce platform as a REST endpoint. It has zero external dependencies and follows the MCP spec version `2025-11-25` with all 11 protocol methods implemented. The Apex handler chain is rebuilt on every request — there is no session state, which eliminates cross-request data leakage by design.
- **npm proxy (client-side)**: A TypeScript/Node.js process with zero npm production dependencies. It speaks stdio to the MCP client (Claude Desktop, Cursor, etc.) and HTTPS to the Salesforce org. It handles the OAuth 2.0 Client Credentials flow on startup and renews tokens automatically.

### MCP Message Flow

```
MCP Client (Claude/Cursor)
  ↓ JSON-RPC 2.0 over stdio
npm proxy (salesforce-mcp-lib)
  ↓ OAuth 2.0 Client Credentials → access token
  ↓ HTTPS POST /services/apexrest/mcp/v1
Apex REST endpoint (your org)
  ↓ McpServer.handleRequest()
  ↓ registered McpToolDefinition / McpResourceDefinition / McpPromptDefinition
  ↑ JSON-RPC response
```

Understanding this flow is essential for debugging: authentication errors come from the proxy layer; logic errors come from the Apex layer.

### Four-Layer Security Model

Security is enforced at four independent layers:

1. **OAuth 2.0 scopes** on the Connected App — restrict which API surfaces the service account can reach.
2. **Profile permissions** — the Connected App's run-as profile controls field and object access.
3. **Permission Sets** — additional fine-grained access layered on top of the profile.
4. **Sharing rules** — Apex running without `without sharing` respects the platform's record visibility rules.

If you omit `without sharing` on your Apex endpoint class, record access is governed by sharing rules for the Connected App user. This is almost always the correct default. Add `with sharing` explicitly if you want to enforce the strictest user-context access rules for the service account.

---

## Common Patterns

### Pattern: Full Stack Setup (Apex Package + npm Proxy + Claude Desktop)

**When to use:** You are setting up salesforce-mcp-lib for the first time in an org and want Claude Desktop to be able to call Salesforce tools.

**How it works:**

1. Install the Apex package: `sf package install --package 04tdL000000So9xQAC --target-org YOUR_ORG --wait 10`
2. Create an Apex REST endpoint class in your org (see templates/).
3. Create a Connected App with OAuth 2.0 Client Credentials Flow enabled. Note the Client ID and Client Secret.
4. Add the Claude Desktop config block to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) with the correct `--instance-url`, `--client-id`, `--client-secret`, and `--endpoint` values.
5. Restart Claude Desktop and verify the MCP tools appear in the Tools panel.

**Why not the alternative:** Using the Salesforce REST API directly from an MCP client requires custom OAuth handling in every client. The npm proxy abstracts that into a one-time configuration step.

### Pattern: Environment Variable Configuration (CI/CD-Friendly)

**When to use:** You want to avoid embedding secrets in the claude_desktop_config.json or share configuration across team members.

**How it works:** The npm proxy reads all flags from environment variables: `SF_INSTANCE_URL`, `SF_CLIENT_ID`, `SF_CLIENT_SECRET`, `SF_ENDPOINT`, and optionally `SF_LOG_LEVEL`. Set these in a `.env` file (gitignored) or in your CI environment, then reference them in the `args` block using your shell's expansion syntax.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| First time setup in a sandbox | Install package, create endpoint, test with `--log-level debug` | Debug logging shows each JSON-RPC exchange so you can confirm the handshake works |
| Production deployment | Use environment variables instead of inline secrets in config files | Secrets in config files risk accidental git exposure |
| Multiple tools from one org | Register all tools in a single Apex endpoint class | One endpoint = one Connected App = one proxy instance; simpler to manage |
| Tool needs record-level access control | Use default sharing (no `without sharing`) on the Apex class | Platform sharing rules control visibility without custom code |
| Need to expose resources (documents, records) | Extend McpResourceDefinition or McpResourceTemplateDefinition | Resources are read-only by MCP spec; use tools for write operations |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Verify prerequisites** — confirm `sf org display` shows API version 65.0+, confirm `node --version` shows >= 20, and confirm you have Salesforce CLI installed.
2. **Install the Apex package** — run `sf package install --package 04tdL000000So9xQAC --target-org YOUR_ORG --wait 10`. Confirm installation with `sf package installed list --target-org YOUR_ORG`.
3. **Create the Apex REST endpoint** — deploy an Apex class with `@RestResource(urlMapping='/mcp/v1')` and a `@HttpPost` method that instantiates `McpServer`, registers tools, and calls `server.handleRequest(RestContext.request, RestContext.response)`.
4. **Create the Connected App** — enable OAuth 2.0 Client Credentials Flow, assign a run-as user (service account profile), and capture the Client ID and Client Secret.
5. **Wire the npm proxy** — add the `mcpServers.salesforce` block to the MCP client's config file with all four required flags (`--instance-url`, `--client-id`, `--client-secret`, `--endpoint`).
6. **Smoke-test the connection** — restart the MCP client, open the tools panel, and confirm the registered tools appear. Use `--log-level debug` to inspect the JSON-RPC handshake if tools do not appear.
7. **Harden for production** — move secrets to environment variables, restrict Connected App scopes to the minimum required, confirm the run-as profile has only the necessary object permissions.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Apex package 04tdL000000So9xQAC installed and confirmed via `sf package installed list`
- [ ] Apex REST endpoint deployed and accessible at the configured URL mapping
- [ ] Connected App has OAuth 2.0 Client Credentials Flow enabled and run-as user assigned
- [ ] npm proxy environment variables set (no hardcoded secrets in config files for production)
- [ ] MCP client (Claude Desktop / Cursor) shows registered tools in the tools panel
- [ ] `--log-level debug` tested and no authentication errors visible
- [ ] Run-as profile reviewed for minimum necessary object/field permissions

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Apex stateless execution** — The McpServer handler chain is rebuilt on every HTTP request. Do not store state in static variables expecting it to persist across MCP calls. Each tool invocation is a fresh Apex transaction.
2. **Connected App propagation delay** — After enabling OAuth 2.0 Client Credentials Flow on a Connected App, Salesforce can take up to 10 minutes to propagate the change to all auth servers. The proxy will return 401 during this window. Wait and retry before debugging further.
3. **API version on the endpoint** — The `@RestResource` URL mapping does not include an API version. The Connected App's OAuth token is issued for the org's default API version. If you need a specific version, include it in your endpoint path explicitly.
4. **Sharing context of the run-as user** — The Client Credentials flow runs as the Connected App's run-as user. SOQL queries inside your Apex tools will be governed by that user's sharing access unless you explicitly use `without sharing`. Unexpected empty result sets are almost always a sharing-context mismatch.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Installed Apex package | salesforce-mcp-lib 2GP classes available for extension in the target org |
| Apex REST endpoint class | The entry point that McpServer.handleRequest() is called from |
| Claude Desktop config block | The mcpServers JSON stanza wiring the proxy to the org |
| Connected App | OAuth 2.0 service account credentials for the proxy |

---

## Related Skills

- mcp-tool-definition-apex — how to implement custom McpToolDefinition classes that extend the server's capabilities with org-specific logic
- agentforce/custom-agent-actions-apex — for native Agentforce Agent Actions as an alternative when you do not need MCP protocol compatibility
- security/connected-app-oauth — deeper Connected App configuration and OAuth scope management

---

## Official Sources Used

- salesforce-mcp-lib GitHub (MIT) — https://github.com/Damecek/salesforce-mcp-lib
- Salesforce Connected Apps OAuth 2.0 Client Credentials Flow — https://help.salesforce.com/s/articleView?id=sf.connected_app_client_credentials_setup.htm
- Salesforce REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
