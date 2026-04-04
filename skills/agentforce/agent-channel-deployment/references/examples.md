# Examples — Agent Channel Deployment

## Example 1: Deploy Agent To Experience Cloud Help Center (Embedded Service)

**Context:** A Service Cloud team has built and activated an Agentforce Service Agent. They need to surface it as a web chat widget on their Experience Cloud customer portal at `https://help.mycompany.com`. External customers will use the chat widget to get answers without waiting for a human agent.

**Problem:** The team publishes the Embedded Service deployment and adds the snippet to the Experience Cloud page, but the chat widget does not load on the live site. The Agentforce Builder Conversation Preview works fine, leading the team to assume the agent is broken — when the real issue is CORS and CSP configuration.

**Solution:**

Step 1 — In Setup > Embedded Service Deployments, open the published deployment. Navigate to the Security tab.

Step 2 — Add `https://help.mycompany.com` to CORS Allowed Origins. If the portal also runs on a staging domain (`https://staging.help.mycompany.com`), add that origin too. Each origin is a separate entry — wildcards are not permitted for CORS Allowed Origins in Embedded Service.

Step 3 — Navigate to Setup > CSP Trusted Sites. Add entries for:
- The Salesforce org domain serving the Embedded Service assets: `https://<orgid>.lightning.force.com`
- The Salesforce CDN domain: `https://static.lightning.force.com`
Set the directive to `connect-src` and `frame-src` as appropriate for the page's Content Security Policy.

Step 4 — Republish the Embedded Service deployment (click Publish again on the deployment page). Even if you did not change the agent, republishing is required after any security configuration change.

Step 5 — Clear browser cache and reload `https://help.mycompany.com`. The chat widget should now appear. Use the browser developer console Network tab to confirm the Embedded Service bootstrap request returns HTTP 200.

```text
Embedded Service CORS entry format:
  Allowed Origin: https://help.mycompany.com
  (no trailing slash, must match exact protocol and domain)

CSP Trusted Site example entries:
  Name: SalesforceEmbeddedService
  URL: https://<your-org-domain>.my.salesforce.com
  Context: All pages
  Directives: connect-src

  Name: SalesforceCDN
  URL: https://static.lightning.force.com
  Context: All pages
  Directives: connect-src, frame-src
```

**Why it works:** The browser enforces the Same-Origin Policy on cross-origin fetch requests. When the chat widget JavaScript running on `https://help.mycompany.com` tries to connect to the Salesforce Messaging endpoint, the browser first checks whether the Salesforce server's CORS response headers allow `https://help.mycompany.com` as an origin. Without the CORS Allowed Origins entry, Salesforce does not include the `Access-Control-Allow-Origin` header, and the browser blocks the request. The CSP Trusted Sites configuration ensures the page's own Content Security Policy permits outgoing connections to Salesforce domains.

---

## Example 2: Connect Agent To Slack Workspace For Internal Support

**Context:** An IT team has built an internal support Agentforce agent to answer employee questions about HR policies and IT procedures. They want employees to interact with the agent directly from Slack, either by DMing the Slack app or by mentioning it in specific IT support channels.

**Problem:** The Salesforce admin tries to connect Agentforce to Slack using a custom Slack app they created independently, wiring it via the Agentforce API. The connection does not work, and Slack DM responses never arrive because the session lifecycle and Trust Layer routing are not handled correctly outside the managed Slack app.

**Solution:**

Step 1 — Confirm the Agentforce agent is Active in Setup > Agentforce Agents.

Step 2 — In Salesforce Setup, search for **Agentforce Slack Deployment** (or navigate via the Agentforce Setup Hub). Click **Connect to Slack**.

Step 3 — The Setup wizard initiates the OAuth install flow for the Salesforce-managed Slack app. Sign in with a Slack account that has **Workspace Admin** privileges. The Slack permission consent screen will list the required OAuth scopes:
- `chat:write` — allows the app to post messages
- `channels:read` — allows the app to view channel membership
- `app_mentions:read` — allows the app to receive @mentions
- `im:read` — allows the app to receive direct messages

Step 4 — Click **Allow** to complete the OAuth installation. The Salesforce-managed Slack app is now installed in the workspace.

Step 5 — Back in Salesforce Setup, select the internal support agent from the agent dropdown. Configure the deployment mode:
- **DM mode:** employees can open a direct message with the Salesforce app in Slack
- **Channel mode:** add specific Slack channel IDs where the app will respond to @mentions

Step 6 — Click **Publish**. Test by sending a DM to the Salesforce app in Slack (DM mode) or @mentioning the app in a configured channel (channel mode). The agent should respond within a few seconds.

```text
Required Slack OAuth scopes for Agentforce Slack deployment:
  chat:write
  channels:read
  app_mentions:read
  im:read

Installation requirement:
  Must be installed by a Slack Workspace Admin.
  Salesforce admin role alone is not sufficient.
```

**Why it works:** The Salesforce-managed Slack app handles the session lifecycle between Slack and the Agentforce runtime, including message routing through the Einstein Trust Layer. This is not a generic webhook integration — it is a purpose-built application that Salesforce maintains. A custom Slack app does not have access to the internal session management APIs required to route messages through the agent reasoning engine.

---

## Anti-Pattern: Using Platform Events To Route Agent Channels

**What practitioners do:** An architect suggests publishing a Platform Event when a user starts a chat, with a subscriber flow or trigger that routes the message to the Agentforce agent programmatically. They reason this gives more control over routing logic.

**What goes wrong:** Platform Events are asynchronous and add latency to a real-time conversational interaction. More critically, routing through a Platform Event bypasses the channel surface entirely — the agent is not connected to a session, so the response has nowhere to go. The Einstein Trust Layer is not invoked for messages that do not originate from a valid channel session. This approach works for triggering back-end workflows, but it is the wrong pattern for interactive agent conversations.

**Correct approach:** Use the channel's built-in routing mechanism — the Embedded Service deployment's agent association for web chat, the Slack deployment configuration for Slack, or the Agent REST API session model for custom surfaces. Channel routing is declarative configuration in Setup, not code. Reserve Platform Events for post-conversation triggers (e.g., case creation after conversation close), not for in-conversation routing.
