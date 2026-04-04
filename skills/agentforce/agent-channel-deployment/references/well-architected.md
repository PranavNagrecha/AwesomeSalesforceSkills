# Well-Architected Notes — Agent Channel Deployment

## Relevant Pillars

### User Experience

Channel selection and configuration directly determines the quality of the end-user interaction with an Agentforce agent. A correctly activated agent that is surfaced on the wrong channel, or surfaced on the right channel without proper CORS/CSP configuration, delivers a broken experience despite having correct agent logic. Well-Architected User Experience principles require that every channel surface be tested end-to-end in the user's actual environment (external browser for web chat, real Slack workspace for Slack, actual API client for Agent API) — not only in Agentforce Builder's preview panel. Channel-specific rendering, latency, and error-handling behaviors must be validated independently because they are invisible to the builder preview.

Channel design also includes the decision of which surface is most appropriate for the user's context. Forcing customers to a web widget when they primarily operate in Slack, or exposing an internal-support agent on an external Experience Cloud site without access controls, creates UX friction and potential security exposure. The channel deployment configuration is where these decisions are enforced.

### Reliability

Multi-channel Agentforce deployments introduce operational reliability concerns that do not exist for single-channel deployments. Key reliability risks:

- **Stale channel deployments** — agent changes that are not republished to all dependent channel surfaces result in channels serving outdated behavior. This is a silent failure mode: the channel continues to work, but with the wrong agent configuration.
- **CORS/CSP misconfigurations** — even a single missing CORS Allowed Origins entry for a staging or preview domain causes widget failures that are difficult to diagnose and attribute to deployment configuration rather than agent logic.
- **OAuth token expiry for Agent API** — long-running applications using the Agent API must implement token refresh logic. Session tokens tied to Connected App access tokens expire, and applications that do not handle token refresh gracefully will fail mid-conversation.
- **Activation dependency** — every channel is gated on the agent's Active state. Accidental deactivation of the agent (e.g., during an update workflow) immediately disables all associated channel surfaces simultaneously, with no user-facing warning.

Reliability practices for agent channel deployment: maintain an inventory of all channel deployments per agent; include channel republishing in every agent change deployment runbook; test channel surfaces in production after every metadata promotion; and implement dead-man monitoring (e.g., a synthetic session every N minutes) on critical Agent API integrations.

### Security

Channel deployment is a security boundary. Decisions made at the channel level determine which users can access the agent and what data those users can supply to the agent's reasoning engine. Key security considerations:

- Embedded Service deployments on external sites must restrict CORS to known, controlled domains. Overly permissive CORS or failure to configure CORS at all creates a surface where any domain can embed the chat widget.
- Slack deployments route messages through the Einstein Trust Layer, but the Slack workspace must be controlled by the organization. Deploying an internal-support agent to an uncontrolled or externally managed Slack workspace can expose internal data patterns.
- Agent API integrations using Connected Apps must follow least-privilege OAuth scope configuration. The `chatbot_api` scope should be the minimum required scope for Agent API-only integrations; do not bundle Agent API access into Connected Apps that also have broad data access (`ModifyAllData`, `ViewAllData`).
- Named Credentials can be used to manage the Connected App credentials for server-side Agent API calls, keeping secrets out of code.

## Architectural Tradeoffs

**Embedded Service vs. Agent REST API for web surfaces:** Embedded Service provides a fully managed, pre-built chat widget with Salesforce hosting and session management at no additional integration cost. It is the right default for standard web chat scenarios. The Agent REST API is the right choice when the organization needs full control over the chat UI (custom branding beyond widget customization, accessibility requirements, embedding in a native app frame), or when the channel surface is not a browser page. The tradeoff is implementation cost: Agent API requires the calling application to manage session lifecycle, render responses, and handle error states.

**Single-channel vs. multi-channel deployment:** Deploying the same agent to multiple channels is operationally efficient (one agent definition serves all surfaces) but increases change management complexity. Every agent update must be coordinated across all dependent channel deployments. Teams operating multiple channels should treat the agent as a shared service and apply change management discipline: staged rollouts, per-channel smoke tests, and version tracking in the deployment runbook.

## Anti-Patterns

1. **Configuring channels before the agent is Active** — teams sometimes spend significant time troubleshooting why their Embedded Service deployment shows no agent option or why the Slack connection fails, when the root cause is simply that the agent is still in Draft state. The agent must be Active before any channel configuration work can proceed. Treat agent activation as a deployment gate: no channel work begins until activation is confirmed.

2. **Using Platform Events or custom Apex as a proxy layer between the channel and the agent** — adding an Apex trigger, Platform Event subscriber, or custom REST endpoint as a routing intermediary between the channel and the agent reasoning engine bypasses the Einstein Trust Layer, breaks the session model, and introduces latency into a real-time conversational interaction. The channel-native routing mechanisms (Embedded Service deployment agent association, Slack deployment configuration, Agent API session endpoints) are the correct integration surfaces.

3. **Treating channel republishing as optional after agent changes** — teams that update agent logic and verify behavior in Agentforce Builder's Conversation Preview often assume the live channel is updated automatically. It is not. Failing to republish channel deployments after agent changes results in live users interacting with a stale agent configuration while the preview shows correct behavior, leading to false confidence in the release.

## Official Sources Used

- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html — channel deployment configuration, Agent API endpoint reference, session model
- Einstein Platform Services — https://developer.salesforce.com/docs/einstein/genai/guide/overview.html — Trust Layer, session lifecycle, OAuth scope requirements
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — Reliability and User Experience pillar framing
- Embedded Service Deployment Help — https://help.salesforce.com/s/articleView?id=sf.embedded_service_deployment.htm — Embedded Service widget configuration, CORS, CSP Trusted Sites
- Agentforce for Slack Help — https://help.salesforce.com/s/articleView?id=sf.agentforce_slack.htm — Slack deployment OAuth flow, managed app installation, channel configuration
