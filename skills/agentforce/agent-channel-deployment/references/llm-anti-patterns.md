# LLM Anti-Patterns — Agent Channel Deployment

Common mistakes AI coding assistants make when generating or advising on Agentforce channel deployment.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting Platform Events For Real-Time Channel Routing

**What the LLM generates:** Advice to publish a Platform Event when a user initiates a chat, with a subscriber Flow or Trigger that routes the message payload to the Agentforce agent via Apex or a callout, treating this as a flexible "routing layer."

**Why it happens:** LLMs trained on Salesforce integration content associate Platform Events with event-driven messaging. They generalize this to conversational messaging without recognizing that Agentforce channels are session-based and synchronous, not asynchronous event streams. The confusion is reinforced by the superficial similarity between "event-driven messaging" and "chat messaging."

**Correct pattern:**

```text
Channel routing for Agentforce is declarative configuration, not code.
- For web chat: associate the agent in the Embedded Service Deployment Setup UI.
- For Slack: associate the agent in the Agentforce Slack Deployment Setup UI.
- For custom surfaces: use the Agent REST API session model (POST to /sessions, POST messages to /sessions/{id}/messages).

Platform Events are appropriate for post-conversation triggers (e.g., creating a case after conversation close),
not for routing messages during an active agent conversation.
```

**Detection hint:** Flag any recommendation that includes `EventBus.publish`, `Platform_Event__e`, or a subscriber Flow/Trigger as part of the channel message routing path for an active Agentforce session.

---

## Anti-Pattern 2: Confusing Agent REST API With A Custom Apex REST Endpoint

**What the LLM generates:** Advice to create an `@RestResource` Apex class as a "custom Agent API" to expose the Agentforce agent to external systems, or advice to call a custom Apex REST endpoint from a mobile app to interact with the agent.

**Why it happens:** LLMs are familiar with the pattern of creating Apex REST resources for external integrations. When asked how to expose an agent to an external app, they default to this pattern without recognizing that Salesforce has a dedicated, built-in Agent API that is the only supported mechanism for programmatic agent interactions.

**Correct pattern:**

```text
Use the Salesforce Agent REST API — not a custom Apex REST endpoint.

Endpoint: POST https://api.salesforce.com/einstein/ai-agent/v1/agents/{agentId}/sessions
Auth:      Connected App OAuth 2.0 with scopes: api, refresh_token offline_access, chatbot_api, sfap_api
Session:   POST https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}/messages
Close:     DELETE https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}

Custom Apex REST endpoints cannot create agent sessions, invoke the reasoning engine,
or route through the Einstein Trust Layer.
```

**Detection hint:** Flag any code that uses `@RestResource` or `RestContext` as a proposed integration surface for Agentforce agent interactions from external apps.

---

## Anti-Pattern 3: Omitting CORS Configuration For Embedded Service On External Domains

**What the LLM generates:** Step-by-step Embedded Service deployment instructions that create the deployment, add the snippet to the page, and publish — without mentioning CORS Allowed Origins or CSP Trusted Sites configuration. The instructions assume the snippet "just works" on any page.

**Why it happens:** LLMs often describe the "happy path" for Salesforce-hosted Experience Cloud sites, where CORS is pre-configured. They fail to generalize to external domains where CORS must be manually configured. The CORS configuration step is buried in the Security tab of the deployment UI and is not prominently featured in basic setup documentation.

**Correct pattern:**

```text
For Embedded Service deployments on external (non-Salesforce) domains:

1. In the deployment's Security tab, add each domain origin to CORS Allowed Origins:
   - Format: https://www.example.com (exact origin, no trailing slash, no wildcards)
   - Add all environments: prod, staging, QA, preview URLs

2. In Setup > CSP Trusted Sites, add entries for:
   - The Salesforce org domain: https://<orgid>.my.salesforce.com
   - The Salesforce CDN: https://static.lightning.force.com
   Directives: connect-src, frame-src

3. Republish the deployment after any security configuration change.
```

**Detection hint:** Flag Embedded Service deployment instructions targeting external domains that do not mention "CORS Allowed Origins" or "CSP Trusted Sites."

---

## Anti-Pattern 4: Advising Users To Create A Custom Slack App Instead Of Using The Salesforce-Managed App

**What the LLM generates:** Instructions to create a new Slack app at api.slack.com, configure a webhook or event subscription, and wire it to Agentforce via an Apex endpoint or outbound message. The LLM treats Agentforce Slack integration like a generic Slack bot integration.

**Why it happens:** LLMs have extensive training data on generic Slack bot development (custom apps, webhooks, Bolt framework). When asked to "connect Salesforce to Slack," they default to custom app patterns without recognizing that Agentforce has a specific, Salesforce-managed Slack app that handles session lifecycle and Trust Layer routing.

**Correct pattern:**

```text
Agentforce deploys to Slack via the Salesforce-managed Slack app — not a custom app.

Steps:
1. Setup > Agentforce > Slack Deployment > Connect to Slack
2. A Slack Workspace Admin must approve the OAuth installation of the Salesforce-managed app.
3. Required OAuth scopes (managed automatically): chat:write, channels:read, app_mentions:read, im:read
4. Associate the Agentforce agent in the Setup wizard after installation.
5. Configure DM mode or channel-mention mode.
6. Publish.

Do NOT create a custom Slack app. Custom apps cannot integrate with the Agentforce session model
or the Einstein Trust Layer.
```

**Detection hint:** Flag any Slack integration instructions that reference `api.slack.com`, Bolt framework, `slack_webhook_url`, or custom Slack app creation in the context of Agentforce channel deployment.

---

## Anti-Pattern 5: Missing The `chatbot_api` OAuth Scope For Agent REST API Connected Apps

**What the LLM generates:** Connected App configuration instructions for Agent API integrations that include only the standard `api` OAuth scope (and possibly `refresh_token`), without the `chatbot_api` scope. The LLM presents these instructions as complete and sufficient for Agent API access.

**Why it happens:** The `chatbot_api` scope is specific to the Agentforce Agent API and is not a standard OAuth scope that LLMs encounter in general Salesforce REST API integration patterns. LLMs default to the most common scope set (`api`, `refresh_token`) without knowing that the Agent API requires an additional scope grant.

**Correct pattern:**

```text
Connected App OAuth Scopes for Agent REST API integration:
  - api         (required — access to Salesforce REST API)
  - chatbot_api (required — "Access chatbot services")
  - sfap_api   (required — "Access the Salesforce API Platform"; most-omitted scope)
  - refresh_token, offline_access (required)
  - refresh_token (recommended — for long-lived integrations)

Without chatbot_api:
  POST https://api.salesforce.com/einstein/ai-agent/v1/agents/{agentId}/sessions
  → HTTP 403 Forbidden (insufficient scope)

Configuration path:
  Setup > App Manager > New Connected App > OAuth Settings
  > Selected OAuth Scopes: Add "Agentforce API (chatbot_api)"
```

**Detection hint:** Flag any Connected App configuration for Agent API that lists OAuth scopes without `chatbot_api` (also labeled "Agentforce API" in the UI).

---

## Anti-Pattern 6: Assuming Channel Deployment Updates Automatically When Agent Changes Are Saved

**What the LLM generates:** Advice that after updating agent instructions, topics, or actions in Agentforce Builder, the changes are immediately live on all deployed channel surfaces. The LLM tells the user to "save the agent and the widget will update automatically."

**Why it happens:** LLMs associate saving configuration changes with immediate platform propagation, which is true for many Salesforce features (e.g., saving a Flow and activating it, or saving a Permission Set). For Agentforce channel deployments, the publish step is a separate, explicit action that is not triggered by saving agent changes.

**Correct pattern:**

```text
After any agent change (instructions, topics, actions):
1. Save and verify the change in Agentforce Builder's Conversation Preview.
2. For each Embedded Service deployment associated with this agent:
   - Setup > Embedded Service Deployments > select deployment > Publish
   - Allow up to 10 minutes for CDN propagation.
3. For Slack deployments: re-save/republish the Slack deployment configuration.
4. Test each channel surface independently to confirm the change is live.

Channel deployments do NOT auto-update when the agent definition changes.
```

**Detection hint:** Flag any instruction that says changes to the agent will "automatically" or "immediately" appear in live channel deployments without an explicit republish step.

---

## Anti-Pattern 6: Serving the Agent API From the Org's `/services/data/vXX.0/` REST Surface

**What the LLM generates:**
```
POST   https://MyDomain.my.salesforce.com/services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions
POST   https://MyDomain.my.salesforce.com/services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}/messages
DELETE https://MyDomain.my.salesforce.com/services/data/v63.0/einstein/ai-agent/agents/{agentId}/sessions/{sessionId}
```
Two independent errors are packed into that block: the wrong host/version prefix, and `agents/{agentId}` retained on the message and delete resources.

**Why it happens:** `/services/data/vXX.0/` is the shape of essentially every Salesforce REST URL in the training corpus — sObjects, Composite, Connect, Tooling, Bulk — so the model applies it as a default frame to any new Salesforce API name it has to render. It then keeps `{agentId}` in the sub-paths because REST convention says a child resource nests under its parent. Agentforce breaks both habits: it is served from a separate platform host, and the session id alone is sufficient to address the conversation once the session exists.

**Correct pattern:**
```
Host: https://api.salesforce.com          (Government Cloud: https://api.gov.salesforce.com)
Version segment: /v1  — NOT the org's /services/data/vXX.0

POST   https://api.salesforce.com/einstein/ai-agent/v1/agents/{agentId}/sessions
POST   https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}/messages
POST   https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}/messages/stream
DELETE https://api.salesforce.com/einstein/ai-agent/v1/sessions/{sessionId}
       header: x-session-end-reason: UserRequest

After session creation the agentId drops out of the path entirely.
```

**Detection hint:** the substring `/services/data/` immediately preceding `/einstein/ai-agent/` is always wrong and always yields 404. Equally mechanical: `/sessions/{sessionId}` appearing after `/agents/{agentId}` in the same path — the two ids never co-occur in a valid Agent API URL. `scripts/check_agent_channels.py` and the sibling skill's `check_agentforce_custom_channel_dev.py` both flag the first form.

---

## Anti-Pattern 7: Listing Only `api` + `chatbot_api` for the Agent API Connected App

**What the LLM generates:** "Create a Connected App with OAuth 2.0 enabled and add the `api` and `chatbot_api` scopes." The answer is *partially* right, which is why it survives review — `chatbot_api` is a genuinely obscure scope, so a reader who has never seen it treats its presence as evidence the author knew the material.

**Why it happens:** `chatbot_api` is the memorable, distinctive-sounding token in the set, so it anchors recall and the rest of the list gets dropped. `sfap_api` is newer, blander, and its consent-screen label ("Access the Salesforce API Platform") reads like boilerplate rather than a requirement.

**Why it matters operationally:** the failure is silent about its cause. A connected app configured with `api` + `chatbot_api` authenticates fine and then fails at the Agent API call with an authorization error that never names `sfap_api`, so the developer debugs the token, the agent id, the host and the payload before suspecting the scope list.

**Correct pattern:**
```
All FOUR scopes on the Connected App / External Client App:
  api                              "Manage user data via APIs"
  refresh_token, offline_access    "Perform requests at any time"
  chatbot_api                      "Access chatbot services"
  sfap_api                         "Access the Salesforce API Platform"
```

**Detection hint:** in prose or a `.connectedApp-meta.xml`, `chatbot_api` present without `sfap_api` alongside it is incomplete for Agent API use. Normalise scope tokens to alphanumerics before comparing (`chatbot_api` / `ChatbotApi` / `Chatbot API` are the same scope) — both skills' checker scripts do this.
