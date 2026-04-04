# Gotchas — Agent Channel Deployment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Agent Must Be Active Before Channel Deployment Can Be Associated Or Published

**What happens:** An admin navigates to Setup > Embedded Service Deployments (or Slack Deployment) to configure the channel and associate the agent. The agent does not appear in the agent dropdown. Alternatively, a previously working deployment stops working after the agent was deactivated for maintenance.

**When it occurs:** Any time the target agent is in Draft or Inactive state. An agent in Draft state has never been activated. An agent in Inactive state was previously active but was deliberately deactivated. Neither state appears in the channel configuration agent selectors. The Embedded Service deployment UI will show an empty agent selector or will retain the previous agent association but fail to serve sessions if the associated agent becomes Inactive.

**How to avoid:** Always activate the agent first (Setup > Agentforce Agents > Open in Builder > Activate) before configuring or republishing any channel deployment. If deactivating an agent for updates, have a plan to re-activate and republish all dependent channel deployments before the maintenance window ends. Maintain an inventory of which channel deployments are associated with each agent.

---

## Gotcha 2: CORS Must Be Configured For Every Domain Where Embedded Service Is Deployed

**What happens:** The Embedded Service widget works perfectly in the Salesforce Developer sandbox or on the Experience Cloud domain (`.my.site.com`) but silently fails to load on any external domain (`www.company.com`, `support.company.com`). The browser developer console shows a CORS error: "Access to XMLHttpRequest has been blocked by CORS policy." There is no Salesforce-side error log or alert for this failure mode.

**When it occurs:** Any time the Embedded Service snippet is embedded on a page whose origin is not listed in the deployment's CORS Allowed Origins configuration. Salesforce only serves the `Access-Control-Allow-Origin` header for origins explicitly whitelisted. This includes staging environments, preview URLs, and any subdomain that is treated as a distinct origin by the browser (different subdomain = different origin). Wildcard origins (`*`) are not permitted in Embedded Service CORS configuration.

**How to avoid:** Before publishing an Embedded Service deployment, compile a full list of all domain origins where the snippet will run — including staging, QA, and production URLs. Add each origin individually to the CORS Allowed Origins list in the deployment's Security tab. Also add the corresponding CSP Trusted Sites entries to allow outgoing connections from those pages to the Salesforce messaging endpoint. After adding origins, republish the deployment.

---

## Gotcha 3: Slack Deployment Requires The Salesforce-Managed Slack App And Workspace Admin Consent

**What happens:** The Salesforce admin attempts to configure the Slack channel but cannot proceed because the OAuth flow requires a Slack Workspace Admin to approve the app installation. The Salesforce admin may not have Slack admin privileges. Additionally, if the team previously installed a custom Slack app and wired it via API, it does not integrate with the Agentforce session model and messages are never routed to the agent.

**When it occurs:** At the point where the Setup wizard initiates the OAuth install flow for the Salesforce-managed Slack app. The consent screen requires workspace-level Slack permissions that only a Slack Workspace Admin or Org Owner can grant. This is a Slack-side permission requirement, not a Salesforce configuration gap. The step is non-negotiable: the managed app must be installed with admin consent before any agent-to-Slack routing works.

**How to avoid:** Identify the Slack Workspace Admin early in the channel deployment planning process — before any Salesforce configuration work begins. Coordinate the OAuth install flow as a joint step with the Slack admin. Do not attempt to workaround the managed app by creating a custom Slack bot app; the session lifecycle and Trust Layer integration are only available through the Salesforce-managed Slack application.

---

## Gotcha 4: Embedded Service Deployment Must Be Republished After Any Agent Change

**What happens:** A team updates agent instructions or adds a new topic after the Embedded Service deployment is already live. Users continue to see the old behavior. The team verifies in Agentforce Builder's Conversation Preview that the new topic works correctly, but customers on the live site still trigger the old behavior.

**When it occurs:** Whenever any change is made to an agent (instructions, topics, actions, role description) after an Embedded Service deployment has been published. The deployment caches the agent configuration at publish time. Changes to the agent definition are not automatically propagated to live deployments. For Experience Cloud-hosted deployments, republishing the Experience Cloud site alone is not sufficient — the Embedded Service deployment itself must be republished first, then the Experience Cloud site.

**How to avoid:** Include "republish all dependent channel deployments" as a mandatory step in the agent change management process. Maintain a record of which Embedded Service deployments, Slack deployments, and other channel configurations reference each agent. After any agent change reaches production (via metadata deployment or direct configuration), republish each dependent channel deployment and allow up to 10 minutes for CDN propagation before declaring the change live.

---

## Gotcha 5: Agent API Requires The `chatbot_api` OAuth Scope In Addition To `api`

**What happens:** A developer creates a Connected App with the `api` OAuth scope, obtains an access token, and attempts to create an Agent API session via `POST /services/data/vXX.0/einstein/ai-agent/agents/{agentId}/sessions`. The request returns HTTP 403 Forbidden with an error indicating insufficient scope, even though the token is valid for other Salesforce REST API calls.

**When it occurs:** When the Connected App is configured with only the standard `api` scope and the `chatbot_api` scope has not been explicitly added. The Agent API session and message endpoints require the `chatbot_api` scope as a distinct authorization grant. A token issued without this scope is valid for the Salesforce REST API but not for the Agent API endpoints.

**How to avoid:** When creating a Connected App for Agent API integration, explicitly add both the `api` scope and the `chatbot_api` scope to the Connected App's OAuth Scopes list. After updating the Connected App, re-authorize the OAuth flow to obtain a new token that includes the `chatbot_api` scope. Verify the new token's scopes before testing the Agent API endpoints.
