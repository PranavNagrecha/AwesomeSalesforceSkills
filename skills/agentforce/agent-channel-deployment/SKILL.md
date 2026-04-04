---
name: agent-channel-deployment
description: "Use when deploying an Agentforce agent to a channel surface: Embedded Service web chat, Slack, Experience Cloud, Agent REST API, or Salesforce Mobile. Triggers: 'deploy agent to website', 'add Agentforce to Slack', 'enable agent for mobile app', 'configure embedded service for agent', 'agent API for custom integration', 'multi-channel agent deployment'. NOT for agent logic design — use agentforce/agent-topic-design or agentforce/agent-actions for topics, instructions, and action contracts."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
triggers:
  - "how to deploy my Agentforce agent to the website so customers can chat with it"
  - "add Agentforce agent to Slack channel for internal support team"
  - "enable agent for mobile app using the Agent REST API"
  - "configure embedded service deployment to surface my Agentforce agent on Experience Cloud"
  - "how do I set up multi-channel deployment so the same agent works on web and Slack"
  - "CORS error when deploying Agentforce Embedded Service to my external site"
tags:
  - agentforce
  - agent-channels
  - embedded-service
  - slack-deployment
  - agent-api
  - experience-cloud
  - multi-channel
  - channel-deployment
inputs:
  - "Active Agentforce agent (agent must not be in Draft or Inactive state)"
  - "target channel type: Embedded Service, Slack, Experience Cloud, Agent API, or Mobile"
  - "target domain URLs for Embedded Service (required for CORS and CSP Trusted Sites)"
  - "Slack workspace details and OAuth app configuration (for Slack channel)"
  - "Named Credential or OAuth configuration for Agent API channel (for API/mobile)"
outputs:
  - "channel deployment configuration steps and checklist per channel type"
  - "Embedded Service snippet code for web/Experience Cloud embedding"
  - "CORS and CSP Trusted Sites configuration guidance"
  - "Slack app OAuth scope list and Slack channel association guidance"
  - "Agent API authentication and request/response usage guidance"
  - "multi-channel testing and validation checklist"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Agent Channel Deployment

Use this skill when an Agentforce agent has been created and activated and now needs to be surfaced on a channel so that end users can interact with it. This skill covers all supported Agentforce channel surfaces — Embedded Service (web chat), Slack, Experience Cloud, the Agent REST API for programmatic integrations, and Salesforce Mobile — including configuration, CORS/CSP requirements, OAuth setup, and multi-channel coordination. It does NOT cover agent logic design: topics, instructions, action contracts, or reasoning engine configuration are handled by `agentforce/agent-topic-design` and `agentforce/agent-actions`.

Channel deployment is a distinct lifecycle stage that comes after agent creation and activation. A successfully activated agent in Agentforce Builder is not yet accessible to users. Each channel requires its own separate configuration and publishing step.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the agent in Active state? Navigate to Setup > Agentforce Agents and confirm the status is Active, not Draft or Inactive. A non-Active agent cannot be associated with any channel deployment.
- Which channel type or types are required? Each channel (Embedded Service, Slack, Agent API) has independent prerequisites and configuration steps.
- For Embedded Service: what is the domain (origin URL) where the chat widget will be embedded? This is required for CORS Allowed Origins and CSP Trusted Sites configuration.
- For Slack: does the Salesforce org have the Salesforce Slack app installed with admin consent? Slack channel deployment requires org-level OAuth token exchange, not per-user configuration.
- For Agent API: what authentication method will the calling application use? Session ID (for Salesforce-authenticated clients) vs. OAuth 2.0 Connected App (for external apps) have different setup paths.
- Has the Einstein Trust Layer been reviewed? Data sent through channels passes through the Trust Layer. Confirm ZDR and masking policies before opening a channel to external users.

---

## Core Concepts

### Channel Surfaces Are Independent Of Agent Definition

An Agentforce agent definition (the Bot + BotVersion + GenAiPlannerBundle metadata bundle) exists independently of any channel. The same agent can be associated with multiple channel surfaces simultaneously. Each channel surface is a separate Salesforce metadata component or platform configuration record that points to the agent. Changing the agent definition (adding topics, updating instructions) requires republishing each dependent channel deployment for the changes to reach users — the channels do not auto-refresh.

### Embedded Service Deployment Is The Primary Web Channel

Embedded Service Deployment (ESD) is the standard mechanism for surfacing an Agentforce agent in a web chat widget. The ESD produces a JavaScript snippet that is added to an Experience Cloud site or any external web page. The snippet loads the Salesforce Messaging for In-App and Web runtime and connects to the agent. For external pages (not hosted on Salesforce), CORS Allowed Origins must include every domain origin where the snippet runs, and CSP Trusted Sites must whitelist the Salesforce domain serving the widget assets. Omitting either setting causes the widget to silently fail to load.

### Slack Deployment Uses A Salesforce-Managed Slack App

Agentforce deploys to Slack via a Salesforce-managed Slack application — not a custom Slack app created by the admin. The admin installs this managed Slack app into the Slack workspace through the Salesforce Setup flow (Setup > Agentforce > Slack Deployment). The OAuth flow during installation grants the necessary scopes: `chat:write`, `channels:read`, `app_mentions:read`, and `im:read` at minimum. After installation, the agent can be configured to respond in specific Slack channels or via direct messages. DM mode and channel-mention mode have different user experience implications and are configured separately.

### Agent REST API Enables Programmatic And Custom-Surface Integrations

The Agentforce Agent API is a REST endpoint (`/services/data/vXX.0/einstein/ai-agent/agents/{agentId}/sessions`) that allows any external application to open a session with an Agentforce agent, send messages, and receive responses. This is the correct channel for mobile apps, custom web surfaces, IVR integrations, or third-party tools that cannot use Embedded Service. Authentication uses either a Salesforce Session ID (for internal Salesforce clients) or a Connected App OAuth 2.0 flow (for external clients). The Agent API is not the same as a custom Apex REST endpoint — it is a Salesforce platform endpoint managed by the Einstein Platform Services runtime.

### Multi-Channel Coordination Requires Per-Channel Testing

A single agent deployed across multiple channels will behave identically in terms of reasoning, but the conversational experience differs: Embedded Service has a visual chat widget with rich formatting support, Slack follows Slack's message formatting conventions, and Agent API responses are JSON-structured for the calling app to render. Each channel should be tested independently in sandbox before production promotion. Channel-specific issues (CORS failures on web, OAuth scope errors on Slack, JSON malformation on API) do not surface in Agentforce Builder's Conversation Preview — they only appear when testing the actual channel surface.

---

## Common Patterns

### Pattern 1: Deploy Agent To Embedded Service (Web Chat)

**When to use:** The agent needs to be accessible as a chat widget on an Experience Cloud portal or an external website.

**How it works:**

1. Navigate to Setup > Embedded Service Deployments > **New**.
2. Select **Messaging for In-App and Web** as the channel type.
3. On the Basic Setup tab: enter a deployment name and API name. Select the target Experience Cloud site (or "None" for external sites).
4. On the **Messaging** tab: select the Agentforce agent from the agent selector. The agent must be in Active state for it to appear in the dropdown.
5. Configure the **Chat Settings**: set the pre-chat fields (if any), offline behavior, and branding colors.
6. On the **Security** tab: add each domain origin (e.g., `https://www.mycompany.com`) to **CORS Allowed Origins**. Also add the same domain to Setup > CSP Trusted Sites if the page includes `frame-src` or `connect-src` restrictions.
7. Click **Publish**. Salesforce generates the embedding snippet.
8. Copy the two-part snippet (the `<script>` bootstrap tag and the `<div>` launch button placeholder) into the `<head>` and `<body>` of the target page, or add the Embedded Messaging component in Experience Builder and republish the Experience Cloud site.
9. Allow up to 10 minutes for CDN propagation before testing on the live domain.

**Why not the alternative:** Attempting to embed a Messaging for In-App and Web widget without configuring CORS and CSP first causes the widget to silently fail. The browser blocks the cross-origin request with no visible error in Salesforce Setup.

### Pattern 2: Connect Agent To Slack

**When to use:** Internal teams need to interact with the Agentforce agent directly within Slack workspaces.

**How it works:**

1. Navigate to Setup > **Agentforce** > **Slack Deployment** (or via the Agentforce Setup Hub).
2. Click **Connect to Slack**. This initiates the Salesforce-managed OAuth flow to install the Salesforce Slack app into the target workspace. A Slack workspace admin must approve the installation.
3. After installation, select the Agentforce agent to associate with this Slack deployment.
4. Configure the channel association: choose one or more Slack channels where the agent is available. In DM mode, users can message the app directly. In channel-mention mode, users `@mention` the app in a channel.
5. Save and publish the Slack deployment.
6. Test by messaging the Slack app from a Slack account. The agent must be Active and the Slack workspace admin must have approved all required OAuth scopes.

**Why not the alternative:** Creating a custom Slack app independently and attempting to connect it to Agentforce is not supported. Agentforce requires its own managed Slack application for authentication and session management. Using a custom app bypasses the Einstein Trust Layer and breaks the session model.

### Pattern 3: Expose Agent Via Agent REST API

**When to use:** A mobile app, custom web surface, IVR, or third-party system needs to interact with the agent programmatically.

**How it works:**

1. Create a Connected App (Setup > App Manager > New Connected App) with OAuth 2.0 enabled. Enable `api` and `chatbot_api` OAuth scopes. This is required for external clients; internal Salesforce clients can use Session ID instead.
2. Record the Connected App's Consumer Key and Consumer Secret. Use the OAuth 2.0 JWT Bearer Flow or Username-Password Flow to obtain an access token.
3. Retrieve the agent ID from Setup > Agentforce Agents > select the agent > note the URL or use the Tooling API: `SELECT Id FROM BotDefinition WHERE DeveloperName = 'MyAgent'`.
4. Start a session: `POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions` with the body `{"externalSessionKey": "<unique-session-id>", "instanceConfig": {"endpoint": "<myOrgInstanceUrl>"}}`. The response returns a `sessionId`.
5. Send a message: `POST /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}/messages` with body `{"message": {"text": "user input here", "sequenceId": 1, "type": "StaticContent"}}`.
6. Parse the response `messages` array for the agent's reply. The `type` field on each response message indicates whether it is text, a choice prompt, or a handoff signal.
7. Close the session when the conversation ends: `DELETE /services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}`.

**Why not the alternative:** Do not create an Apex REST endpoint (`@RestResource`) as a proxy to the agent — this bypasses Einstein Trust Layer enforcement and does not have access to the agent session model. The Agent API is the correct, supported integration surface.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Customer-facing web chat on Experience Cloud | Embedded Service Deployment with Messaging for In-App and Web | Native widget, pre-built UI, full Trust Layer coverage |
| Customer-facing web chat on an external (non-Salesforce) site | Embedded Service Deployment with CORS + CSP Trusted Sites configured | Same widget, but CORS/CSP must be configured for the external domain |
| Internal team support via Slack | Slack Deployment using Salesforce-managed Slack app | Requires Slack workspace admin consent; DM or channel-mention modes available |
| Custom mobile app or third-party surface | Agent REST API with Connected App OAuth 2.0 | Decouples rendering from Salesforce; caller controls the UI |
| Same agent on multiple surfaces simultaneously | Deploy to each channel separately; test each independently | Channels are independent; agent changes must be republished to each |
| Testing before production | Use Conversation Preview in Agentforce Builder, then test each channel in sandbox | Preview tests agent reasoning only; channel-specific failures only appear on the actual surface |

---

## Recommended Workflow

Step-by-step instructions for deploying an Agentforce agent to one or more channels:

1. **Confirm agent readiness** — verify the agent is in Active state in Setup > Agentforce Agents. Confirm topics, actions, and instructions are finalized. Confirm the Einstein Trust Layer has been reviewed for the channel's audience (internal vs. external users).
2. **Identify target channels** — determine which channel surfaces are required (Embedded Service, Slack, Agent API, or a combination). For each channel, collect the prerequisites: domain origins for web, Slack workspace admin contact for Slack, Connected App credentials for API.
3. **Configure the channel** — follow the channel-specific pattern from the Common Patterns section. For Embedded Service: create the deployment, associate the agent, configure CORS/CSP, publish, and embed the snippet. For Slack: run the OAuth install flow, associate the agent, configure channel or DM mode, publish. For Agent API: create the Connected App, retrieve the agent ID, test the session and message endpoints.
4. **Test on the actual channel surface in sandbox** — do not rely solely on Conversation Preview. Test each channel independently. Verify the widget loads (web), the Slack app responds (Slack), and the API returns valid JSON (Agent API). Check browser console for CORS errors (web), OAuth errors (Slack), and HTTP 4xx responses (API).
5. **Promote to production** — deploy channel metadata alongside agent metadata. After deployment, the agent arrives in Inactive state; activate it in production before enabling the channel. Republish each Embedded Service deployment after activation. Re-run channel-specific tests in production.
6. **Monitor and validate** — review Enhanced Event Logs for conversation traces. Confirm each channel surface is routing to the correct agent. Set up monitoring for session failure rates and unhandled topic rates across channels.

---

## Review Checklist

Run through these before marking channel deployment work complete:

- [ ] Agent is in Active state (not Draft or Inactive) before configuring any channel.
- [ ] For Embedded Service: CORS Allowed Origins includes every domain where the widget will run.
- [ ] For Embedded Service: CSP Trusted Sites are configured for Salesforce widget asset domains.
- [ ] For Embedded Service: the snippet has been added to the page or Embedded Messaging component added in Experience Builder, and the site has been republished.
- [ ] For Slack: Slack workspace admin has approved the Salesforce-managed Slack app installation.
- [ ] For Slack: required OAuth scopes (`chat:write`, `channels:read`, `app_mentions:read`, `im:read`) are granted.
- [ ] For Agent API: Connected App is configured with `api` and `chatbot_api` OAuth scopes.
- [ ] For Agent API: session creation and message endpoint have been tested and return valid responses.
- [ ] Each channel has been tested independently in sandbox before production promotion.
- [ ] After production metadata deployment, the agent has been manually activated in production.
- [ ] Each Embedded Service deployment has been republished after production activation.
- [ ] Enhanced Event Logs are enabled and conversation records are visible for each channel.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Agent must be Active before channel deployment can be published** — the agent selector in Embedded Service Deployment and Slack Deployment Setup only shows agents in Active state. If the agent is in Draft or Inactive, it will not appear in the dropdown and the deployment cannot be associated.
2. **Embedded Service deployment must be republished after every agent change** — modifying agent instructions, topics, or actions does not update active channel deployments. Each Embedded Service deployment caches the agent configuration at publish time. Changes only reach users after the deployment is explicitly republished.
3. **CORS and CSP must cover every domain origin where the widget runs** — a missing CORS entry for even a single domain causes the Embedded Service widget to silently fail on that domain. There is no Salesforce-side error log for CORS failures; the error appears only in the browser developer console as a blocked cross-origin request.
4. **Slack deployment requires the Salesforce-managed Slack app, not a custom app** — creating a custom Slack app and attempting to wire it to Agentforce is unsupported and will not work. The managed app handles session lifecycle and Trust Layer enforcement. The Slack workspace admin must approve the managed app installation; this cannot be pre-approved by the Salesforce admin alone.
5. **Agent API authentication uses `chatbot_api` OAuth scope, not standard `api` scope alone** — Connected Apps configured with only the `api` scope cannot open Agent API sessions. The `chatbot_api` scope must be explicitly added. This is a common omission that produces HTTP 403 responses when trying to create a session.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Channel deployment checklist | Per-channel step-by-step checklist for Embedded Service, Slack, and Agent API configuration |
| CORS and CSP configuration list | Exact domain origins and CSP trusted site entries required for the target web deployment |
| Embedded Service snippet | The JavaScript snippet and Embedded Messaging component configuration for the target page |
| Agent API usage guide | Endpoint URLs, request body schemas, and authentication flow for Agent REST API integration |
| Multi-channel test plan | Test scenarios and validation steps for each channel surface in sandbox and production |

---

## Related Skills

- `agentforce/agentforce-agent-creation` — use when the agent itself has not yet been created or activated; channel deployment is a post-creation step.
- `agentforce/agent-topic-design` — use when the problem is topic boundary design or classification logic, not channel surface configuration.
- `agentforce/agent-actions` — use when the problem is action contract quality or action availability within topics.
- `agentforce/einstein-trust-layer` — use alongside this skill to review ZDR, data masking, and grounding policies before opening a channel to external users.
- `security/csp-trusted-sites` — use for detailed CSP Trusted Sites configuration if the Embedded Service deployment is on an external site with a strict Content Security Policy.
