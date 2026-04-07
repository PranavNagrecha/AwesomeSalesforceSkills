# Well-Architected Notes — Salesforce MCP Server Setup

## Relevant Pillars

- **Security** — The four-layer security model (OAuth scopes, Profile, Permission Sets, Sharing Rules) is the primary architectural concern. The service account run-as user must be provisioned with least-privilege access. Client credentials must never be embedded in committed source files.
- **Reliability** — The npm proxy is a single point of failure between the MCP client and the org. The Apex handler chain is stateless, which ensures reliability at the Salesforce layer, but the proxy process must be monitored by the MCP client host.
- **Operational Excellence** — Debug logging (`--log-level debug`) provides the primary observability mechanism during setup. Production deployments should use structured log aggregation from the proxy's stdout and Apex debug logs from the org.

## Architectural Tradeoffs

**Self-hosted vs. Salesforce Hosted MCP Servers:** salesforce-mcp-lib is developer-operated. You control the endpoint, the tools, and the credentials. Salesforce Hosted MCP Servers (available for specific Salesforce products in beta as of Spring '25) are managed by Salesforce and require less setup but offer less customization. Use salesforce-mcp-lib when you need custom Apex tool logic; use Hosted MCP when the pre-built Salesforce tools cover your use case.

**Client Credentials vs. User Context:** The Client Credentials OAuth flow authenticates as a service account, not as the end user of the MCP client. This simplifies setup (no browser redirect) but means all tool invocations run with the same permissions. If per-user authorization is required, a different OAuth flow or a custom token-forwarding mechanism is needed — salesforce-mcp-lib does not support per-user authorization natively.

**Single endpoint vs. multiple endpoints:** Registering all tools in one Apex endpoint class is simpler to operate (one Connected App, one proxy instance). Splitting tools across endpoints increases surface area and operational complexity with no benefit for most use cases.

## Anti-Patterns

1. **Secrets in committed config files** — Embedding `--client-id` and `--client-secret` directly in `claude_desktop_config.json` and committing that file to version control. Client secrets for Connected Apps are equivalent to API keys — they grant full access to the run-as user's permissions. Use environment variables or a secrets manager and add config files with secrets to `.gitignore`.

2. **Overprivileged run-as user** — Assigning a System Administrator profile to the Connected App's run-as user for convenience. If the MCP proxy is compromised, the attacker has full org access. The run-as user should have a custom profile limited to the specific objects and fields the registered tools need.

3. **Using `with sharing` carelessly on tool classes** — Assuming `with sharing` makes the tool "safer" without understanding that it enforces the run-as user's sharing access (which may be broader than expected for a system user). Explicitly document the sharing decision and test with a restricted user account.

## Official Sources Used

- salesforce-mcp-lib GitHub (MIT) — https://github.com/Damecek/salesforce-mcp-lib
- Salesforce Connected Apps OAuth 2.0 Client Credentials Flow — https://help.salesforce.com/s/articleView?id=sf.connected_app_client_credentials_setup.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
