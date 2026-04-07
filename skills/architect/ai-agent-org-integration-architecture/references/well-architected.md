# Well-Architected Notes — AI Agent to Salesforce Org Integration Architecture

## Relevant Pillars

- **Security** — The most critical pillar for AI-to-org integration. The connected AI agent must be treated as an external integration with the same threat model as any third-party API consumer. Key concerns: OAuth scope minimization, run-as user least privilege, data exposure scope definition, PII field exclusion, SOQL injection defense in Apex tools, audit trail design.
- **Scalability** — Per-org API call limits and Apex governor limits bound what AI agents can do within the Salesforce platform. Architecture must account for peak call volume, concurrent users, and the combination of human + agent API consumption. Stateless Apex design (required by salesforce-mcp-lib) naturally scales horizontally.
- **Reliability** — AI agent integrations introduce an external dependency into Salesforce workflows. When the agent or its proxy is unavailable, what happens? Architecture must define failure modes, timeouts, and fallback behaviors. For event-driven patterns, the 24-hour CDC retention window is a hard reliability constraint.
- **Operational Excellence** — Observability is non-negotiable. Agent API calls must be logged and alertable. Apex deployments for tool changes need the same CI/CD pipeline as production code. The architecture should make it easy to add, remove, or modify tools without disrupting the agent's connection to the org.

## Architectural Tradeoffs

**MCP vs. Direct REST for custom LLM pipelines:** MCP (via salesforce-mcp-lib) provides a structured, schema-validated tool interface that constrains what an AI agent can do and makes the tool's behavior self-documenting to the MCP client. Direct REST API gives the LLM complete freedom to construct arbitrary SOQL queries and REST calls — which is more flexible but more dangerous and harder to audit. For security-sensitive orgs, prefer MCP with narrow tools over direct REST with open SOQL access.

**Client Credentials vs. Web Server OAuth for user attribution:** Client Credentials is simpler (no browser redirect, no user session management) but all actions are attributed to the service account. Web Server (user-delegated) attributes actions to the human user, which is required for regulatory audit in some industries (financial services, healthcare). The architectural cost is session management complexity and the need for each user to authorize the agent once via browser.

**Synchronous (request-response) vs. event-driven for AI enrichment:** Synchronous patterns (user triggers agent → agent calls Salesforce → returns response) are simpler but create latency dependency. Event-driven patterns (Salesforce publishes event → AI pipeline processes asynchronously → updates record) are more resilient to AI latency spikes but require recovery design for event bus outages. Choose based on the latency tolerance of the use case.

## Anti-Patterns

1. **Overprivileged service account with System Administrator profile** — Granting the AI agent's service account a System Administrator profile eliminates the entire data exposure scope boundary. Any LLM hallucination, prompt injection, or misconfigured tool can access or modify any org data. The correct pattern is a custom profile with explicit, documented permission grants aligned to the tool definitions.

2. **No observability design before go-live** — Deploying an AI agent integration without defining how API calls will be logged, how anomalous behavior will be detected, and how to trace a specific agent action back to the Salesforce record it modified. Salesforce Event Monitoring (available in Enterprise/Unlimited with add-on license) logs API calls with user, endpoint, and timestamp. At minimum, document the monitoring approach in the architecture decision record before production deployment.

3. **Polling instead of CDC for event-driven patterns** — Implementing a scheduled job that polls for new or changed records every N minutes instead of using Change Data Capture. Polling consumes API calls unnecessarily, introduces latency proportional to the polling interval, and misses records created between polls if DML volume is high. CDC is purpose-built for this use case and uses the event bus rather than API quota.

## Official Sources Used

- salesforce-mcp-lib GitHub (MIT) — https://github.com/Damecek/salesforce-mcp-lib
- Salesforce Connected Apps OAuth 2.0 Client Credentials Flow — https://help.salesforce.com/s/articleView?id=sf.connected_app_client_credentials_setup.htm
- Salesforce REST API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/
- Salesforce Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/
- Salesforce Change Data Capture Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/
- Salesforce API Limits Cheat Sheet — https://developer.salesforce.com/docs/atlas.en-us.salesforce_app_limits_cheatsheet.meta/salesforce_app_limits_cheatsheet/
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected Security — https://architect.salesforce.com/docs/architect/well-architected/guide/security.html
- Salesforce Well-Architected Scalability — https://architect.salesforce.com/docs/architect/well-architected/guide/scalability.html
